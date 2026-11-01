from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.community.models import Comment, Notification
from apps.community.serializers import CommentSerializer, NotificationSerializer

class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        pet_id = self.request.query_params.get('pet_id')
        if pet_id:
            qs = qs.filter(pet_id=pet_id)
        return qs

class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        unread_only = self.request.query_params.get('unread')
        if unread_only and unread_only.lower() == 'true':
            qs = qs.filter(is_read=False)
        return qs

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        Notification.objects.filter(is_read=False).update(is_read=True)
        return Response({'message': 'Todas las notificaciones marcadas como leídas'})

    @action(detail=True, methods=['post'], url_path='mark_read')
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({'status': 'marked as read', 'id': notification.id})


# Notifications endpoint
# Sanitization safeguard
