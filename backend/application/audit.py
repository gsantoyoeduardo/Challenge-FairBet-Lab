"""
Serializers para la auditoría del sistema.

Función:
- Serializar `AuditLog` y `SuspiciousActivity` para exponerlos por la
    API administrativa y para verificar la integridad de la cadena de
    auditoría.

Relaciones:
- Utilizan `infrastructure.audit` como fuente de datos.
"""

from rest_framework import serializers
from infrastructure.audit import AuditLog, SuspiciousActivity


class AuditLogSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True, default='')

    class Meta:
        model = AuditLog
        fields = ('id', 'timestamp', 'username', 'action', 'entity_type',
                  'entity_id', 'data', 'hash_prev', 'hash_current')


class AuditVerifySerializer(serializers.Serializer):
    total = serializers.IntegerField()
    errors = serializers.IntegerField()
    valid = serializers.BooleanField()
    details = serializers.ListField()


class SuspiciousActivitySerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = SuspiciousActivity
        fields = ('id', 'username', 'tipo', 'descripcion', 'severidad',
                  'resuelto', 'created_at')
