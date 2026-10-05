from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.ai_matching.views import MatchResultViewSet

router = DefaultRouter()
router.register(r'matches', MatchResultViewSet, basename='matchresult')

urlpatterns = [
    path('', include(router.urls)),
]
