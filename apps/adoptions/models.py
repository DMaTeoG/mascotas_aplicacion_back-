from django.db import models
from django.contrib.auth.models import User
from apps.pets.models import Pet

class ApplicationStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pendiente de Revisión'
    UNDER_REVIEW = 'UNDER_REVIEW', 'En Proceso / Entrevista'
    APPROVED = 'APPROVED', 'Aprobada'
    REJECTED = 'REJECTED', 'Rechazada'

class AdoptionApplication(models.Model):
    applicant_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='adoption_applications',
        verbose_name="Cuenta del Solicitante"
    )
    pet = models.ForeignKey(
        Pet,
        on_delete=models.CASCADE,
        related_name='adoption_applications',
        verbose_name="Mascota Solicitada"
    )
    applicant_name = models.CharField(max_length=150, verbose_name="Nombre Completo del Solicitante")
    applicant_email = models.EmailField(verbose_name="Correo Electrónico")
    applicant_phone = models.CharField(max_length=50, verbose_name="Teléfono / WhatsApp")
    city = models.CharField(max_length=100, default='Bogotá', verbose_name="Ciudad de Residencia")
    
    # Criterios de tenencia responsable
    housing_type = models.CharField(max_length=100, verbose_name="Tipo de Vivienda (Casa/Apto)")
    has_other_pets = models.BooleanField(default=False, verbose_name="¿Tiene otras mascotas actualmente?")
    other_pets_description = models.CharField(max_length=255, blank=True, verbose_name="Detalle de otras mascotas")
    has_children = models.BooleanField(default=False, verbose_name="¿Hay niños en el hogar?")
    time_dedicated = models.CharField(max_length=100, default='Más de 4 horas al día', verbose_name="Tiempo disponible para la mascota")
    experience_description = models.TextField(verbose_name="Experiencia previa y motivación para adoptar")
    agree_to_home_visit = models.BooleanField(default=True, verbose_name="Acepta visita previa domiciliaria o virtual")
    
    # Seguimiento
    status = models.CharField(
        max_length=20,
        choices=ApplicationStatus.choices,
        default=ApplicationStatus.PENDING,
        verbose_name="Estado de Solicitud"
    )
    internal_notes = models.TextField(blank=True, verbose_name="Notas del Refugio / Rescatista")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Envío")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última Actualización")

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Solicitud de Adopción'
        verbose_name_plural = 'Solicitudes de Adopción'

    def __str__(self):
        return f"Solicitud de {self.applicant_name} para {self.pet.title} ({self.get_status_display()})"

# Enums defined
