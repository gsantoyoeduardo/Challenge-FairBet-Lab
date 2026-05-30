"""
Modelos de persistencia para la aplicación `wallet`.

Función:
- Define `Account` y `LedgerEntry` que representan cuentas y asientos
    contables (partida doble). Estos modelos son la fuente de verdad para
    saldos e historiales transaccionales.

Relaciones:
- Consumidos por `application` (casos de uso) y `controllers` (endpoints).
"""

import uuid

from django.db import models, transaction
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal

User = get_user_model()


class Account(models.Model):
    class AccountType(models.TextChoices):
        MAIN = 'main', 'Cuenta Principal'
        BONUS = 'bonus', 'Cuenta Bonos'
        CASA = 'casa', 'Cuenta Casa'
        APUESTAS = 'apuestas_pendientes', 'Apuestas Pendientes'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='accounts', null=True, blank=True)
    type = models.CharField(max_length=30, choices=AccountType.choices, default=AccountType.MAIN)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        app_label = 'wallet'
        unique_together = ('user', 'type')

    def __str__(self):
        username = self.user.username if self.user else 'sistema'
        return f'{username} - {self.type}'


class LedgerEntry(models.Model):
    class Direction(models.TextChoices):
        DEBIT = 'DEBIT', 'Debito'
        CREDIT = 'CREDIT', 'Credito'

    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='entries')
    amount = models.DecimalField(max_digits=18, decimal_places=4)
    direction = models.CharField(max_length=6, choices=Direction.choices, default=Direction.CREDIT)
    transaction_id = models.UUIDField(default=uuid.uuid4, db_index=True)
    description = models.CharField(max_length=255)
    reference = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        app_label = 'wallet'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['transaction_id']),
        ]

    def __str__(self):
        return f'{self.account} - {self.direction} {self.amount} - {self.description}'
