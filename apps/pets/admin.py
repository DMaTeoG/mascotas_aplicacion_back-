from django.contrib import admin
from apps.pets.models import Pet

@admin.register(Pet)
class PetAdmin(admin.ModelAdmin):
    list_display = ('title', 'report_type', 'species', 'breed', 'zone_name', 'status', 'created_at')
    list_filter = ('report_type', 'species', 'status', 'size')
    search_fields = ('title', 'breed', 'zone_name', 'description')
