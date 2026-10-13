from django.contrib import admin
from apps.adoptions.models import AdoptionApplication

@admin.register(AdoptionApplication)
class AdoptionApplicationAdmin(admin.ModelAdmin):
    list_display = ('applicant_name', 'pet', 'applicant_phone', 'city', 'housing_type', 'status', 'created_at')
    list_filter = ('status', 'housing_type', 'has_other_pets', 'created_at')
    search_fields = ('applicant_name', 'applicant_email', 'applicant_phone', 'pet__title')
