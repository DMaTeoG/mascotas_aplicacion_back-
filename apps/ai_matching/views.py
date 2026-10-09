from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.ai_matching.models import MatchResult
from apps.ai_matching.serializers import MatchResultSerializer
from apps.ai_matching.engine import run_global_matching

class MatchResultViewSet(viewsets.ModelViewSet):
    queryset = MatchResult.objects.filter(is_dismissed=False)
    serializer_class = MatchResultSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        pet_id = self.request.query_params.get('pet_id')
        min_score = self.request.query_params.get('min_score')
        confidence = self.request.query_params.get('confidence')

        if pet_id:
            qs = qs.filter(lost_pet_id=pet_id) | qs.filter(found_pet_id=pet_id)
        if min_score:
            try:
                qs = qs.filter(score_percent__gte=float(min_score))
            except ValueError:
                pass
        if confidence:
            qs = qs.filter(confidence_level=confidence.upper())

        return qs

    @action(detail=False, methods=['post'])
    def recalculate(self, request):
        """Ejecuta el recálculo masivo de coincidencias en segundo plano."""
        count = run_global_matching(min_threshold=50.0)
        return Response({
            'message': f'Motor de IA ejecutado exitosamente. Se evaluaron y generaron {count} coincidencias.',
            'matches_count': count
        })

    @action(detail=False, methods=['post'], url_path='visual-search')
    def visual_search(self, request):
        """Busca en el repositorio de perdidos analizando la coincidencia de imagen de un reporte encontrado."""
        found_pet_id = request.data.get('found_pet_id')
        if not found_pet_id:
            return Response({'error': 'El campo found_pet_id es requerido'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            from apps.pets.models import Pet, ReportType
            from apps.pets.serializers import PetSerializer
            found_pet = Pet.objects.get(id=found_pet_id)
            if found_pet.report_type != ReportType.FOUND:
                return Response({'error': 'La mascota debe ser de tipo FOUND (Encontrada)'}, status=status.HTTP_400_BAD_REQUEST)

            from apps.ai_matching.vision_engine import search_lost_by_found_image
            results = search_lost_by_found_image(found_pet)

            serialized_results = []
            for r in results:
                serialized_results.append({
                    'lost_pet': PetSerializer(r['lost_pet']).data,
                    'visual_score': r['visual_score']
                })

            return Response({
                'found_pet_id': found_pet.id,
                'found_pet_title': found_pet.title,
                'found_pet_image_url': found_pet.image_url,
                'matches_count': len(serialized_results),
                'results': serialized_results
            })
        except Pet.DoesNotExist:
            return Response({'error': 'Mascota encontrada no existe'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'])
    def dismiss(self, request, pk=None):
        """Descarta una coincidencia para que no vuelva a alertar al usuario."""
        match_obj = self.get_object()
        match_obj.is_dismissed = True
        match_obj.save()
        return Response({'message': 'Coincidencia descartada exitosamente'})


# Visual search endpoint registered
