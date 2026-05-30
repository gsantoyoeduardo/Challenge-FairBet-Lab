"""
Controladores HTTP para `responsible_gaming`.

Función:
- Endpoints para consultar y cambiar límites, y para autoexclusión de
    usuarios. Validan peticiones y delegan en `application.responsible_gaming`.

Relaciones:
- Usados por la UI y por los endpoints que necesitan bloquear apuestas
    cuando el usuario está autoexcluido o excede límites.
"""

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiExample

from application.responsible_gaming import (
    DepositLimitsSerializer, AutoExclusionSerializer,
    get_or_create_limits, apply_limit_change, create_autoexclusion,
)
from domain.responsible_gaming import validate_autoexclusion_period


class LimitsView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = DepositLimitsSerializer

    @extend_schema(
        summary='Consultar limites del usuario',
        description='Devuelve los limites configurados: diario, semanal, mensual, apuesta_max, perdida_diaria.',
        responses={200: DepositLimitsSerializer},
    )
    def get(self, request):
        limits = get_or_create_limits(request.user)
        return Response(DepositLimitsSerializer(limits).data)

    @extend_schema(
        summary='Establecer limites de deposito/apuesta',
        description='Bajar limites es inmediato. Subir requiere 24h de cooldown.',
        request=DepositLimitsSerializer,
        responses={200: DepositLimitsSerializer},
        examples=[
            OpenApiExample('Ejemplo', value={
                'limite_diario': '100.0000',
                'limite_semanal': '500.0000',
                'limite_mensual': '2000.0000',
                'limite_apuesta_max': '50.0000',
                'limite_perdida_diaria': '200.0000',
            }),
        ],
    )
    def post(self, request):
        limits = get_or_create_limits(request.user)
        data = request.data
        results = []

        for field in ['limite_diario', 'limite_semanal', 'limite_mensual',
                       'limite_apuesta_max', 'limite_perdida_diaria']:
            if field in data:
                try:
                    result = apply_limit_change(request.user, field, data[field])
                    results.append(result)
                except ValueError as e:
                    return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        limits.refresh_from_db()
        return Response(DepositLimitsSerializer(limits).data)


class AutoExclusionView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = AutoExclusionSerializer

    @extend_schema(
        summary='Autoexcluirse',
        description='El usuario se autoexcluye por un periodo: 7d, 30d, 90d o indefinida. '
                    'Esto bloquea todas las apuestas inmediatamente.',
        request=AutoExclusionSerializer,
        responses={201: None},
        examples=[
            OpenApiExample('30 dias', value={'periodo': '30d', 'motivo': 'Necesito un descanso'}),
        ],
    )
    def post(self, request):
        serializer = AutoExclusionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        periodo = serializer.validated_data['periodo']
        motivo = serializer.validated_data.get('motivo', '')

        err = validate_autoexclusion_period(periodo)
        if err:
            return Response({'error': err}, status=status.HTTP_400_BAD_REQUEST)

        create_autoexclusion(request.user, periodo, motivo)
        return Response({
            'mensaje': f'Autoexclusion aplicada por {periodo}. No podras apostar hasta que termine el periodo.',
        }, status=status.HTTP_201_CREATED)
