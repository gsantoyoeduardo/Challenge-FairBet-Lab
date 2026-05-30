"""
Modelos de persistencia para la auditoría del sistema (`audit`).

Función:
- `AuditLog` implementa auditoría inmutable mediante encadenamiento de
    hashes SHA-256 (hash chaining). `SuspiciousActivity` almacena alertas de
    comportamiento sospechoso detectado por tareas de auditoría.

Relaciones:
- `audit.tasks` crea entradas en `AuditLog` y `SuspiciousActivity`.
- Otros módulos crean logs al ejecutar operaciones sensibles.
"""

import hashlib
import json
from django.conf import settings
from django.db import models
from django.utils import timezone


class AuditLog(models.Model):
    timestamp = models.DateTimeField(default=timezone.now)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    action = models.CharField(max_length=100)
    entity_type = models.CharField(max_length=50)
    entity_id = models.PositiveIntegerField(null=True, blank=True)
    data = models.JSONField(default=dict)
    hash_prev = models.CharField(max_length=64, default='')
    hash_current = models.CharField(max_length=64, default='', db_index=True)

    class Meta:
        app_label = 'audit'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['entity_type', 'entity_id']),
            models.Index(fields=['action']),
        ]

    def __str__(self):
        return f'[{self.timestamp}] {self.action} {self.entity_type}#{self.entity_id}'

    @classmethod
    def compute_hash(cls, data: dict, hash_prev: str, timestamp_str: str) -> str:
        payload = json.dumps(data, sort_keys=True, default=str)
        raw = f'{payload}|{hash_prev}|{timestamp_str}'
        return hashlib.sha256(raw.encode()).hexdigest()

    @classmethod
    def verify_chain(cls) -> dict:
        logs = cls.objects.order_by('timestamp', 'id')
        errors = []
        prev_hash = ''
        for log in logs:
            expected = cls.compute_hash(log.data, prev_hash, log.timestamp.isoformat())
            if log.hash_current != expected:
                errors.append({
                    'id': log.id,
                    'expected': expected,
                    'stored': log.hash_current,
                })
            prev_hash = log.hash_current
        return {
            'total': logs.count(),
            'errors': len(errors),
            'valid': len(errors) == 0,
            'details': errors[:10],
        }


class SuspiciousActivity(models.Model):
    class Severity(models.TextChoices):
        LOW = 'low', 'Baja'
        MEDIUM = 'medium', 'Media'
        HIGH = 'high', 'Alta'

    class ActivityType(models.TextChoices):
        SAME_IP = 'misma_ip', 'Misma IP'
        PATTERN_IDENTICAL = 'patron_identico', 'Patron Identico'
        DEPOSIT_CASHOUT = 'deposito_cashout', 'Deposito + Cash-out'
        MULTIPLE_ACCOUNTS = 'multiple_accounts', 'Multiples Cuentas'
        STAKE_ANOMALY = 'stake_anomaly', 'Stake Anomalo'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='suspicious_activities',
    )
    tipo = models.CharField(max_length=30, choices=ActivityType.choices)
    descripcion = models.TextField()
    severidad = models.CharField(max_length=10, choices=Severity.choices, default=Severity.LOW)
    resuelto = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        app_label = 'audit'
        ordering = ['-created_at']

    def __str__(self):
        return f'[{self.severidad}] {self.tipo} - {self.user.username}'
