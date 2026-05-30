"""
Modelos de `responsible_gaming`.

Función:
- Almacenan límites de depósito, solicitudes de cambio de límite y
    autoexclusiones del usuario para cumplir requisitos de juego responsable.

Relaciones:
- Utilizados por `application.responsible_gaming` para validar y procesar
    cambios y bloqueos de usuario.
"""

from django.conf import settings
from django.db import models
from django.utils import timezone


class DepositLimits(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='deposit_limits',
    )
    limite_diario = models.DecimalField(max_digits=18, decimal_places=4, default=0)
    limite_semanal = models.DecimalField(max_digits=18, decimal_places=4, default=0)
    limite_mensual = models.DecimalField(max_digits=18, decimal_places=4, default=0)
    limite_apuesta_max = models.DecimalField(max_digits=18, decimal_places=4, default=0)
    limite_perdida_diaria = models.DecimalField(max_digits=18, decimal_places=4, default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'responsible_gaming'

    def __str__(self):
        return f'Limits for {self.user.username}'


class LimitChangeRequest(models.Model):
    class ChangeStatus(models.TextChoices):
        PENDING = 'pending', 'Pendiente'
        APPROVED = 'approved', 'Aprobado'
        REJECTED = 'rejected', 'Rechazado'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='limit_changes',
    )
    tipo_limite = models.CharField(max_length=30)
    valor_anterior = models.DecimalField(max_digits=18, decimal_places=4)
    valor_solicitado = models.DecimalField(max_digits=18, decimal_places=4)
    estado = models.CharField(max_length=20, choices=ChangeStatus.choices, default=ChangeStatus.PENDING)
    created_at = models.DateTimeField(default=timezone.now)
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = 'responsible_gaming'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username} - {self.tipo_limite}: {self.valor_anterior} -> {self.valor_solicitado}'


class AutoExclusion(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='auto_exclusion',
    )
    fecha_inicio = models.DateTimeField(default=timezone.now)
    fecha_fin = models.DateTimeField(null=True, blank=True)
    motivo = models.TextField(blank=True, default='')
    activa = models.BooleanField(default=True)

    class Meta:
        app_label = 'responsible_gaming'

    def __str__(self):
        return f'Autoexclusion {self.user.username}: {self.fecha_inicio} -> {self.fecha_fin}'
