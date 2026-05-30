"""
Controladores administrativos para la auditoría y alertas de fraude.

Función:
- Exponer logs de auditoría, verificación de integridad y alertas de
    actividad sospechosa para uso del equipo de compliance.

Relaciones:
- Interactúan con `infrastructure.audit` y `application.audit`.
"""

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from infrastructure.audit import AuditLog, SuspiciousActivity
from application.audit import AuditLogSerializer, SuspiciousActivitySerializer


class AuditLogListView(generics.ListAPIView):
    permission_classes = [permissions.IsAdminUser]
    serializer_class = AuditLogSerializer
    queryset = AuditLog.objects.all()

    @extend_schema(
        summary='Listar logs de auditoria (admin)',
        description='Devuelve todos los logs de auditoria con hash encadenado.',
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class AuditVerifyView(generics.GenericAPIView):
    permission_classes = [permissions.IsAdminUser]

    @extend_schema(
        summary='Verificar integridad de la cadena de auditoria',
        description='Recalcula todos los hashes SHA256 y verifica que no haya sido alterada.',
    )
    def get(self, request):
        result = AuditLog.verify_chain()
        status_code = status.HTTP_200_OK if result['valid'] else status.HTTP_409_CONFLICT
        return Response(result, status=status_code)


class FraudAlertsView(generics.ListAPIView):
    permission_classes = [permissions.IsAdminUser]
    serializer_class = SuspiciousActivitySerializer
    queryset = SuspiciousActivity.objects.all()

    @extend_schema(
        summary='Listar alertas de anti-fraude (admin)',
        description='Devuelve todas las alertas de actividad sospechosa.',
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
