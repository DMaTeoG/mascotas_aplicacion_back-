from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.adoptions.views import AdoptionApplicationViewSet

router = DefaultRouter()
router.register(r'applications', AdoptionApplicationViewSet, basename='adoptionapplication')

urlpatterns = [
    path('', include(router.urls)),
]
