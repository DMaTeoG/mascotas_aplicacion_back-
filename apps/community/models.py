from django.db import models
from apps.pets.models import Pet

class Comment(models.Model):
    pet = models.ForeignKey(
        Pet,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name="Mascota / Publicación"
    )
    author_name = models.CharField(max_length=100, default='Vecino Solidario', verbose_name="Nombre del Autor")
    content = models.TextField(verbose_name="Comentario o Pista")
    is_sighting = models.BooleanField(default=False, verbose_name="¿Es una pista de avistamiento?")
    sighting_location = models.CharField(max_length=200, blank=True, verbose_name="Lugar del avistamiento")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha")

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Comentario / Pista'
        verbose_name_plural = 'Comentarios y Pistas'

    def __str__(self):
        return f"Comentario de {self.author_name} en {self.pet.title}"

class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('MATCH', 'Posible Coincidencia IA'),
        ('ADOPTION', 'Solicitud de Adopción'),
        ('COMMENT', 'Nueva Pista / Comentario'),
        ('SYSTEM', 'Mensaje del Sistema')
    )

    title = models.CharField(max_length=150, verbose_name="Título")
    message = models.TextField(verbose_name="Mensaje de Alerta")
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='MATCH')
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    is_read = models.BooleanField(default=False, verbose_name="Leída")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha")

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Notificación'
        verbose_name_plural = 'Notificaciones'

    def __str__(self):
        return f"[{self.get_notification_type_display()}] {self.title}"
