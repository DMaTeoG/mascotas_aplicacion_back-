from django.contrib import admin
from apps.community.models import Comment, Notification

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('author_name', 'pet', 'is_sighting', 'sighting_location', 'created_at')
    list_filter = ('is_sighting', 'created_at')
    search_fields = ('author_name', 'content', 'sighting_location')

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read')
