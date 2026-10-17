import logging
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.adoptions.models import AdoptionApplication, ApplicationStatus
from apps.adoptions.serializers import AdoptionApplicationSerializer
from apps.pets.models import Status

logger = logging.getLogger(__name__)

class AdoptionApplicationViewSet(viewsets.ModelViewSet):
    queryset = AdoptionApplication.objects.select_related('pet', 'applicant_user', 'pet__author').all()
    serializer_class = AdoptionApplicationSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        pet_id = self.request.query_params.get('pet_id')
        status_param = self.request.query_params.get('status')
        email = self.request.query_params.get('email')
        user_id = self.request.query_params.get('applicant_user_id')
        owner_id = self.request.query_params.get('owner_id')

        if pet_id:
            qs = qs.filter(pet_id=pet_id)
        if status_param:
            qs = qs.filter(status=status_param)
        if email:
            qs = qs.filter(applicant_email__iexact=email)
        if user_id:
            qs = qs.filter(applicant_user_id=user_id)
        if owner_id:
            qs = qs.filter(pet__author_id=owner_id)

        return qs

    def perform_create(self, serializer):
        if self.request.user and self.request.user.is_authenticated:
            app = serializer.save(applicant_user=self.request.user)
        else:
            app = serializer.save()
        logger.info(
            f"[Adoptions] Solicitud #{app.id} radicada para mascota '{app.pet.title}' (ID {app.pet.id}) por {app.applicant_name}"
        )

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        app = self.get_object()
        new_status = request.data.get('status')
        notes = request.data.get('notes', '')

        # Validar permisos: solo el dueño de la publicación o un staff puede actualizar el estado
        if request.user.is_authenticated and app.pet.author and app.pet.author != request.user and not request.user.is_staff:
            return Response(
                {'error': 'Solo quien dio en adopción a la mascota puede decidir sobre las solicitudes.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if new_status in ApplicationStatus.values:
            app.status = new_status
            if notes:
                app.internal_notes = notes
            app.save()

            # Si la adopción es aprobada, marcar a la mascota como ADOPTED
            if new_status == ApplicationStatus.APPROVED:
                app.pet.status = Status.ADOPTED
                app.pet.save()
                logger.info(
                    f"[Adoptions] ¡Solicitud #{app.id} APROBADA! Mascota #{app.pet.id} ('{app.pet.title}') actualizada a estado ADOPTED."
                )
            elif new_status == ApplicationStatus.REJECTED:
                logger.info(
                    f"[Adoptions] Solicitud #{app.id} RECHAZADA para mascota #{app.pet.id}. Motivo/Notas: {notes}"
                )

            return Response({
                'status': app.status,
                'pet_status': app.pet.status,
                'message': 'Estado de solicitud actualizado correctamente'
            })
        return Response({'error': 'Estado no válido'}, status=status.HTTP_400_BAD_REQUEST)

# Status update transitions
