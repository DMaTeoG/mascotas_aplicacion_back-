"""
URL configuration for core project.
"""
from django.contrib import admin
from django.urls import path, re_path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse

def root_health_view(request):
    return JsonResponse({
        'status': 'online',
        'service': 'Huellitas & Rescate Backend API',
        'version': '1.0.0',
        'endpoints': {
            'pets': '/api/v1/pets/',
            'ai_matching': '/api/v1/ai/matches/',
            'visual_search': '/api/v1/ai/matches/visual-search/',
            'adoptions': '/api/v1/adoptions/applications/',
            'notifications': '/api/v1/community/notifications/'
        }
    })

urlpatterns = [
    path('', root_health_view, name='root_health'),
    path('health/', root_health_view, name='health_check'),
    path('admin/', admin.site.urls),
    # Compatible con /api/v1/ y //api/v1/ (doble barra preventiva)
    re_path(r'^(?:/)?api/v1/auth/', include('apps.accounts.urls')),
    re_path(r'^(?:/)?api/v1/pets/', include('apps.pets.urls')),
    re_path(r'^(?:/)?api/v1/ai/', include('apps.ai_matching.urls')),
    re_path(r'^(?:/)?api/v1/adoptions/', include('apps.adoptions.urls')),
    re_path(r'^(?:/)?api/v1/community/', include('apps.community.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
