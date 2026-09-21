import logging
from rest_framework import viewsets, status, permissions, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from apps.pets.models import Pet, Status, PetClaim, ClaimStatus
from apps.pets.serializers import PetSerializer, PetClaimSerializer
from apps.ai_matching.engine import run_matching_for_pet
from apps.ai_matching.serializers import MatchResultSerializer

logger = logging.getLogger(__name__)

class PetViewSet(viewsets.ModelViewSet):
    queryset = Pet.objects.all()
    serializer_class = PetSerializer

    def get_queryset(self):
        qs = Pet.objects.all()
        report_type = self.request.query_params.get('report_type')
        species = self.request.query_params.get('species')
        size = self.request.query_params.get('size')
        search = self.request.query_params.get('search')
        status_param = self.request.query_params.get('status')
        author_id = self.request.query_params.get('author_id')

        if author_id:
            qs = qs.filter(author_id=author_id)
        if report_type:
            qs = qs.filter(report_type=report_type)
        if species:
            qs = qs.filter(species=species)
        if size:
            qs = qs.filter(size=size)
        if status_param:
            qs = qs.filter(status=status_param)
        else:
            # Por defecto mostrar activos
            qs = qs.filter(status=Status.ACTIVE)

        if search:
            qs = qs.filter(
                Q(title__icontains=search) |
                Q(breed__icontains=search) |
                Q(zone_name__icontains=search) |
                Q(description__icontains=search) |
                Q(primary_color__icontains=search)
            )

        return qs

    def perform_create(self, serializer):
        if self.request.user and self.request.user.is_authenticated:
            pet = serializer.save(author=self.request.user)
        else:
            pet = serializer.save()
        # Disparo automático del motor de IA
        matches = run_matching_for_pet(pet, min_threshold=50.0)
        self._recent_matches = matches
        logger.info(f"[PetViewSet] Mascota #{pet.id} ('{pet.title}') creada con éxito. Matches automáticos: {len(matches)}")

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        if hasattr(self, '_recent_matches') and self._recent_matches:
            match_serializer = MatchResultSerializer(self._recent_matches, many=True)
            response.data['matches_found'] = match_serializer.data
        else:
            response.data['matches_found'] = []
        return response

    @action(detail=True, methods=['post'], url_path='like')
    def like(self, request, pk=None):
        pet = self.get_object()
        pet.likes_count += 1
        pet.save()
        return Response({'likes_count': pet.likes_count, 'message': 'Apoyo registrado'})

    @action(detail=True, methods=['post'], url_path='toggle_like')
    def toggle_like(self, request, pk=None):
        return self.like(request, pk)


class PetClaimViewSet(viewsets.ModelViewSet):
    """
    Controlador para reclamos de propiedad de mascotas encontradas.
    Permite a los usuarios demostrar pertenencia y al rescatista validar y resolver el reporte.
    """
    queryset = PetClaim.objects.all()
    serializer_class = PetClaimSerializer

    def get_permissions(self):
        if self.action in ['create', 'approve', 'reject']:
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def get_queryset(self):
        qs = PetClaim.objects.select_related('pet', 'claimant', 'pet__author').all()
        pet_id = self.request.query_params.get('pet_id')
        claimant_id = self.request.query_params.get('claimant_id')
        author_id = self.request.query_params.get('author_id')
        status_param = self.request.query_params.get('status')

        if pet_id:
            qs = qs.filter(pet_id=pet_id)
        if claimant_id:
            qs = qs.filter(claimant_id=claimant_id)
        if author_id:
            qs = qs.filter(pet__author_id=author_id)
        if status_param:
            qs = qs.filter(status=status_param)
        return qs

    def perform_create(self, serializer):
        pet = serializer.validated_data.get('pet')
        if pet.author and pet.author == self.request.user:
            raise serializers.ValidationError("No puedes presentar un reclamo sobre una mascota que tú mismo publicaste.")
        
        claim = serializer.save(claimant=self.request.user)
        logger.info(
            f"[PetClaim] Reclamo #{claim.id} radicado por '{self.request.user.username}' para mascota #{pet.id} ('{pet.title}')"
        )

    @action(detail=True, methods=['post'], url_path='approve')
    def approve(self, request, pk=None):
        claim = self.get_object()
        pet = claim.pet

        # Solo el rescatista que publicó la mascota o admin puede aprobar el reclamo
        if pet.author and pet.author != request.user and not request.user.is_staff:
            return Response(
                {'error': 'Solo el autor del reporte o un administrador puede validar y aprobar este reclamo.'},
                status=status.HTTP_403_FORBIDDEN
            )

        notes = request.data.get('notes', '')
        claim.status = ClaimStatus.APPROVED
        if notes:
            claim.rescatista_notes = notes
        claim.save()

        # Al confirmar que se encontró/entregó, la mascota pasa a RESOLVED (desaparece del feed activo)
        pet.status = Status.RESOLVED
        pet.save()

        logger.info(
            f"[PetClaim] Reclamo #{claim.id} APROBADO por '{request.user.username}'. Mascota #{pet.id} '{pet.title}' marcada como RESOLVED (Entregada a su dueño)."
        )

        return Response({
            'message': 'Reclamo aprobado exitosamente. La mascota ha sido entregada y el reporte resuelto.',
            'claim_status': claim.status,
            'pet_status': pet.status
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='reject')
    def reject(self, request, pk=None):
        claim = self.get_object()
        pet = claim.pet

        if pet.author and pet.author != request.user and not request.user.is_staff:
            return Response(
                {'error': 'Solo el autor del reporte o un administrador puede rechazar este reclamo.'},
                status=status.HTTP_403_FORBIDDEN
            )

        notes = request.data.get('notes', '')
        claim.status = ClaimStatus.REJECTED
        if notes:
            claim.rescatista_notes = notes
        claim.save()

        logger.info(
            f"[PetClaim] Reclamo #{claim.id} RECHAZADO por '{request.user.username}' para mascota #{pet.id}. Motivo: {notes}"
        )

        return Response({
            'message': 'Reclamo rechazado.',
            'claim_status': claim.status
        }, status=status.HTTP_200_OK)

# Filters applied
