"""
URL configuration for core project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/auth/', include('apps.accounts.urls')),
    path('api/v1/pets/', include('apps.pets.urls')),
    path('api/v1/ai/', include('apps.ai_matching.urls')),
    path('api/v1/adoptions/', include('apps.adoptions.urls')),
    path('api/v1/community/', include('apps.community.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
