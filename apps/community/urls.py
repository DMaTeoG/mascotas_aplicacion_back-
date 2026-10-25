from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.community.views import CommentViewSet, NotificationViewSet

router = DefaultRouter()
router.register(r'comments', CommentViewSet, basename='comment')
router.register(r'notifications', NotificationViewSet, basename='notification')

urlpatterns = [
    path('', include(router.urls)),
]
