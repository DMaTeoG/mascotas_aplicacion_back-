from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

class ReportType(models.TextChoices):
    LOST = 'LOST', 'Mascota Perdida'
    FOUND = 'FOUND', 'Mascota Encontrada'
    ADOPTION = 'ADOPTION', 'En Adopción'

class Species(models.TextChoices):
    DOG = 'dog', 'Perro'
    CAT = 'cat', 'Gato'

class Size(models.TextChoices):
    SMALL = 'small', 'Pequeño'
    MEDIUM = 'medium', 'Mediano'
    LARGE = 'large', 'Grande'
    EXTRA_LARGE = 'extra_large', 'Muy Grande'

class Gender(models.TextChoices):
    MALE = 'male', 'Macho'
    FEMALE = 'female', 'Hembra'
    UNKNOWN = 'unknown', 'Desconocido'

class Status(models.TextChoices):
    ACTIVE = 'ACTIVE', 'Activo'
    RESOLVED = 'RESOLVED', 'Resuelto / Encontrado'
    ADOPTED = 'ADOPTED', 'Adoptado'

class Pet(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pets',
        verbose_name="Usuario Publicador"
    )
    title = models.CharField(max_length=200, verbose_name="Título del Reporte")
    report_type = models.CharField(
        max_length=20,
        choices=ReportType.choices,
        default=ReportType.LOST,
        db_index=True,
        verbose_name="Tipo de Publicación"
    )
    species = models.CharField(
        max_length=10,
        choices=Species.choices,
        default=Species.DOG,
        db_index=True,
        verbose_name="Especie"
    )
    breed = models.CharField(max_length=100, default='Mestizo / Criollo', verbose_name="Raza")
    size = models.CharField(
        max_length=20,
        choices=Size.choices,
        default=Size.MEDIUM,
        verbose_name="Tamaño"
    )
    gender = models.CharField(
        max_length=10,
        choices=Gender.choices,
        default=Gender.UNKNOWN,
        verbose_name="Sexo"
    )
    primary_color = models.CharField(max_length=50, verbose_name="Color Principal")
    secondary_color = models.CharField(max_length=50, blank=True, null=True, verbose_name="Color Secundario")
    pattern = models.CharField(max_length=50, default='solido', verbose_name="Patrón de Pelaje")
    distinctive_features = models.TextField(blank=True, verbose_name="Marcas o Rasgos Distintivos")
    
    # Ubicación y Tiempo
    zone_name = models.CharField(max_length=200, verbose_name="Zona o Sector")
    latitude = models.FloatField(blank=True, null=True, verbose_name="Latitud")
    longitude = models.FloatField(blank=True, null=True, verbose_name="Longitud")
    event_date = models.DateTimeField(default=timezone.now, verbose_name="Fecha del Suceso")
    
    # Detalles
    description = models.TextField(verbose_name="Descripción detallada")
    reward = models.CharField(max_length=100, blank=True, verbose_name="Recompensa (opcional)")
    
    # Contacto
    contact_name = models.CharField(max_length=120, default='Comunidad', verbose_name="Nombre de Contacto")
    contact_phone = models.CharField(max_length=50, blank=True, verbose_name="Teléfono")
    contact_email = models.EmailField(blank=True, verbose_name="Correo Electrónico")
    
    # Imagen y Multimedia
    image_url = models.URLField(max_length=1000, blank=True, verbose_name="URL de Imagen Externa")
    image = models.ImageField(upload_to='pets/', blank=True, null=True, verbose_name="Foto Subida")
    
    # Estado e Interacciones Sociales
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True,
        verbose_name="Estado"
    )
    likes_count = models.PositiveIntegerField(default=0, verbose_name="Reacciones / Apoyos")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última Actualización")

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Mascota'
        verbose_name_plural = 'Mascotas'

    def __str__(self):
        return f"[{self.get_report_type_display()}] {self.title} ({self.species})"

    @property
    def display_image(self):
        if self.image:
            return self.image.url
        return self.image_url or '/placeholder-pet.jpg'


class ClaimStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pendiente de Validación'
    APPROVED = 'APPROVED', 'Reclamo Aprobado (Mascota Entregada)'
    REJECTED = 'REJECTED', 'Reclamo Rechazado'

class PetClaim(models.Model):
    """
    Reclamo de propiedad de una mascota encontrada.
    El dueño real debe adjuntar prueba (foto previa o detalles privados que solo él conoce).
    """
    pet = models.ForeignKey(
        Pet,
        on_delete=models.CASCADE,
        related_name='claims',
        verbose_name="Mascota Encontrada"
    )
    claimant = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='pet_claims',
        verbose_name="Usuario Reclamante"
    )
    proof_description = models.TextField(
        verbose_name="Detalles privados o marcas secretas que demuestran pertenencia"
    )
    proof_image_url = models.URLField(
        max_length=1000,
        blank=True,
        verbose_name="URL de foto previa con la mascota"
    )
    proof_image = models.ImageField(
        upload_to='claims/',
        blank=True,
        null=True,
        verbose_name="Foto previa adjunta"
    )
    status = models.CharField(
        max_length=20,
        choices=ClaimStatus.choices,
        default=ClaimStatus.PENDING,
        verbose_name="Estado del Reclamo"
    )
    rescatista_notes = models.TextField(
        blank=True,
        verbose_name="Respuesta o notas del rescatista"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha del Reclamo")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última Actualización")

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Reclamo de Mascota'
        verbose_name_plural = 'Reclamos de Mascotas'

    def __str__(self):
        return f"Reclamo de {self.claimant.username} para '{self.pet.title}' ({self.get_status_display()})"


# Enums validated
# Geo-coordinates supported
