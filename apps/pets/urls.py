from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.pets.views import PetViewSet, PetClaimViewSet

router = DefaultRouter()
router.register(r'claims', PetClaimViewSet, basename='pet-claim')
router.register(r'', PetViewSet, basename='pet')

urlpatterns = [
    path('', include(router.urls)),
]
