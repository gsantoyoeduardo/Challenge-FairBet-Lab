"""
Modelos de dominio persistidos para `betting`.

Función:
- `Bet` y `BetSelection` representan apuestas realizadas por usuarios,
    su estado, cuotas y selecciones asociadas.

Relaciones:
- `application.betting` crea y liquida `Bet` usando estos modelos; las
    selecciones referencian `infrastructure.events.Selection`.
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal

from infrastructure.events import Selection

User = get_user_model()


class Bet(models.Model):
    class Status(models.TextChoices):
        ACCEPTED = 'accepted', 'Aceptada'
        WON = 'won', 'Ganada'
        LOST = 'lost', 'Perdida'
        CASHED_OUT = 'cashed_out', 'Cobrada Anticipadamente'
        CANCELLED = 'cancelled', 'Cancelada'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bets')
    stake = models.DecimalField(max_digits=18, decimal_places=4)
    total_odds = models.DecimalField(max_digits=18, decimal_places=4)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACCEPTED)
    placed_at = models.DateTimeField(default=timezone.now)
    settled_at = models.DateTimeField(null=True, blank=True)
    payout = models.DecimalField(max_digits=18, decimal_places=4, null=True, blank=True)

    class Meta:
        app_label = 'betting'
        ordering = ['-placed_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f'Bet #{self.id} - {self.user.username} - {self.status}'


class BetSelection(models.Model):
    bet = models.ForeignKey(Bet, on_delete=models.CASCADE, related_name='selections')
    selection = models.ForeignKey(Selection, on_delete=models.CASCADE, related_name='bet_selections')
    odds_at_time = models.DecimalField(max_digits=18, decimal_places=4)

    class Meta:
        app_label = 'betting'
        unique_together = ('bet', 'selection')

    def __str__(self):
        return f'{self.selection.name} @ {self.odds_at_time}'
