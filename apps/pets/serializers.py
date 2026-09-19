from rest_framework import serializers
from apps.pets.models import Pet, PetClaim
from apps.accounts.serializers import UserSerializer

class PetSerializer(serializers.ModelSerializer):
    display_image = serializers.ReadOnlyField()
    report_type_display = serializers.CharField(source='get_report_type_display', read_only=True)
    species_display = serializers.CharField(source='get_species_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    author_detail = UserSerializer(source='author', read_only=True)

    class Meta:
        model = Pet
        fields = '__all__'

class PetClaimSerializer(serializers.ModelSerializer):
    claimant_detail = UserSerializer(source='claimant', read_only=True)
    pet_detail = PetSerializer(source='pet', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = PetClaim
        fields = '__all__'
        read_only_fields = ['id', 'claimant', 'status', 'created_at', 'updated_at']


