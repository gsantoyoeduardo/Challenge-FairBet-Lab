"""
Modelos de `bonuses`.

Función:
- Definen tipos de bonos, configuración (porcentaje, rollover) y la
    relación `UserBonus` que rastrea saldo y progreso de rollover por
    usuario.

Relaciones:
- Aplicables desde `application.bonuses` para otorgar y liquidar bonos.
"""

from django.conf import settings
from django.db import models
from django.utils import timezone
from decimal import Decimal


class Bonus(models.Model):
    class BonusType(models.TextChoices):
        BIENVENIDA = 'bienvenida', 'Bono de Bienvenida'
        RECARGA = 'recarga', 'Bono de Recarga'

    tipo = models.CharField(max_length=20, choices=BonusType.choices)
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, default='')
    porcentaje = models.DecimalField(max_digits=5, decimal_places=2, default=100)
    monto_max = models.DecimalField(max_digits=18, decimal_places=4, default=100)
    rollover_requerido = models.PositiveIntegerField(default=5)
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'bonuses'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.nombre} ({self.porcentaje}% hasta {self.monto_max} BP)'


class UserBonus(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='user_bonuses',
    )
    bonus = models.ForeignKey(Bonus, on_delete=models.CASCADE)
    saldo_bono = models.DecimalField(max_digits=18, decimal_places=4, default=0)
    rollover_completado = models.DecimalField(max_digits=18, decimal_places=4, default=0)
    fecha_otorgado = models.DateTimeField(default=timezone.now)
    fecha_expiracion = models.DateTimeField(null=True, blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        app_label = 'bonuses'
        ordering = ['-fecha_otorgado']

    @property
    def rollover_restante(self):
        requerido = self.bonus.rollover_requerido * self.saldo_bono
        return max(0, requerido - self.rollover_completado)

    @property
    def rollover_porcentaje(self):
        requerido = self.bonus.rollover_requerido * self.saldo_bono
        if requerido <= 0:
            return 100
        return min(100, int((self.rollover_completado / requerido * Decimal('100')).quantize(Decimal('1'))))

    @property
    def rollover_completo(self):
        return self.rollover_porcentaje >= 100

    def __str__(self):
        return f'{self.user.username} - {self.bonus.nombre}: {self.saldo_bono} BP'
