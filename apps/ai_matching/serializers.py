from rest_framework import serializers
from apps.ai_matching.models import MatchResult
from apps.pets.serializers import PetSerializer

class MatchResultSerializer(serializers.ModelSerializer):
    lost_pet_detail = PetSerializer(source='lost_pet', read_only=True)
    found_pet_detail = PetSerializer(source='found_pet', read_only=True)

    class Meta:
        model = MatchResult
        fields = '__all__'
