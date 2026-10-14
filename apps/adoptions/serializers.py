from rest_framework import serializers
from apps.adoptions.models import AdoptionApplication
from apps.pets.serializers import PetSerializer

class AdoptionApplicationSerializer(serializers.ModelSerializer):
    pet_detail = PetSerializer(source='pet', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = AdoptionApplication
        fields = '__all__'

    def validate_pet(self, value):
        from apps.pets.models import ReportType, Status
        if value.report_type != ReportType.ADOPTION:
            raise serializers.ValidationError(
                f"No se pueden radicar solicitudes de adopción para mascotas en estado '{value.get_report_type_display()}'. Solo aplica a mascotas 'En Adopción'."
            )
        if value.status != Status.ACTIVE:
            raise serializers.ValidationError(
                "La mascota seleccionada ya no se encuentra disponible para adopción activa."
            )
        return value

