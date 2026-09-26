from django.db import models
from apps.pets.models import Pet

class MatchResult(models.Model):
    lost_pet = models.ForeignKey(
        Pet,
        on_delete=models.CASCADE,
        related_name='lost_matches',
        verbose_name="Mascota Perdida"
    )
    found_pet = models.ForeignKey(
        Pet,
        on_delete=models.CASCADE,
        related_name='found_matches',
        verbose_name="Mascota Encontrada"
    )
    score_percent = models.FloatField(verbose_name="Porcentaje de Coincidencia (0-100)")
    confidence_level = models.CharField(max_length=20, default='MEDIA', verbose_name="Nivel de Confianza")
    explanation = models.TextField(verbose_name="Explicación en Lenguaje Natural")
    factors_breakdown = models.JSONField(default=dict, verbose_name="Desglose de Factores")
    is_dismissed = models.BooleanField(default=False, verbose_name="Descartada por Usuario")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Evaluación")

    class Meta:
        ordering = ['-score_percent', '-created_at']
        verbose_name = 'Resultado de Coincidencia'
        verbose_name_plural = 'Resultados de Coincidencias'
        unique_together = ('lost_pet', 'found_pet')

    def __str__(self):
        return f"{self.score_percent:.1f}% Match: Perdido #{self.lost_pet_id} vs Encontrado #{self.found_pet_id}"
