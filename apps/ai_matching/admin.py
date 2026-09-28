from django.contrib import admin
from apps.ai_matching.models import MatchResult

@admin.register(MatchResult)
class MatchResultAdmin(admin.ModelAdmin):
    list_display = ('lost_pet', 'found_pet', 'score_percent', 'confidence_level', 'is_dismissed', 'created_at')
    list_filter = ('confidence_level', 'is_dismissed', 'created_at')
    search_fields = ('explanation', 'lost_pet__title', 'found_pet__title')
