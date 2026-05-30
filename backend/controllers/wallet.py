"""
Controladores HTTP para la API de `wallet`.

Función:
- Exponen endpoints REST (recargar, retirar, consultar saldo) que
    validan la petición y delegan la lógica a `application.wallet`.

Relaciones:
- Usan `application.wallet` para casos de uso y `infrastructure.users`
    para idempotencia.
"""

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiTypes

from application.wallet import (
    RecargarSerializer, RetirarSerializer, TransferirSerializer,
    recargar, retirar, transferir, get_balance,
)
from infrastructure.users import IdempotencyKey

RECARGAR_EXAMPLE = OpenApiExample(
    'Recarga de 100 BP',
    value={'amount': '100.0000', 'reference': 'Pago con tarjeta'},
    request_only=True,
)

RETIRAR_EXAMPLE = OpenApiExample(
    'Retiro de 50 BP',
    value={'amount': '50.0000'},
    request_only=True,
)

SALDO_RESPONSE = OpenApiExample(
    'Saldo actual',
    value={'balance': '1000.0000'},
    response_only=True,
)

TRANSFERIR_EXAMPLE = OpenApiExample(
    'Transferencia de 50 BP',
    value={'to_username': 'demo2', 'amount': '50.0000'},
    request_only=True,
)


class RecargarView(generics.GenericAPIView):
    serializer_class = RecargarSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'wallet'

    @extend_schema(
        summary='Recargar cuenta',
        description='Agrega saldo a la cuenta principal del usuario via partida doble (casa → usuario)',
        request=RecargarSerializer,
        responses={
            200: OpenApiTypes.OBJECT,
            400: OpenApiTypes.OBJECT,
        },
        examples=[RECARGAR_EXAMPLE],
        parameters=[{
            'name': 'X-Idempotency-Key',
            'in_': 'header',
            'schema': {'type': 'string'},
            'description': 'Clave de idempotencia',
        }],
    )
    def post(self, request):
        key = request.headers.get('X-Idempotency-Key') or request.data.get('idempotency_key')
        if key:
            cached = IdempotencyKey.objects.filter(key=key, user=request.user).first()
            if cached and cached.response_data:
                return Response(cached.response_data, status=status.HTTP_200_OK)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            new_balance = recargar(
                request.user,
                serializer.validated_data['amount'],
                reference=serializer.validated_data.get('reference', ''),
            )
            response_data = {'balance': str(new_balance)}
            if key:
                IdempotencyKey.objects.get_or_create(
                    key=key, user=request.user,
                    defaults={'response_data': response_data},
                )
            return Response(response_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class RetirarView(generics.GenericAPIView):
    serializer_class = RetirarSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'wallet'

    @extend_schema(
        summary='Retirar fondos',
        description='Retira saldo de la cuenta principal del usuario via partida doble (usuario → casa)',
        request=RetirarSerializer,
        responses={
            200: OpenApiTypes.OBJECT,
            400: OpenApiTypes.OBJECT,
        },
        examples=[RETIRAR_EXAMPLE],
        parameters=[{
            'name': 'X-Idempotency-Key',
            'in_': 'header',
            'schema': {'type': 'string'},
            'description': 'Clave de idempotencia',
        }],
    )
    def post(self, request):
        key = request.headers.get('X-Idempotency-Key') or request.data.get('idempotency_key')
        if key:
            cached = IdempotencyKey.objects.filter(key=key, user=request.user).first()
            if cached and cached.response_data:
                return Response(cached.response_data, status=status.HTTP_200_OK)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            retirar(
                request.user,
                serializer.validated_data['amount'],
                reference=serializer.validated_data.get('reference', ''),
            )
            response_data = {'balance': str(get_balance(request.user, 'main'))}
            if key:
                IdempotencyKey.objects.get_or_create(
                    key=key, user=request.user,
                    defaults={'response_data': response_data},
                )
            return Response(response_data, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class SaldoView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='Consultar saldo',
        description='Retorna el saldo actual de la cuenta principal calculado como SUM(CREDIT) - SUM(DEBIT). '
                    'Usa ?tipo=bonus para consultar el saldo de bonos.',
        responses={200: OpenApiTypes.OBJECT},
        examples=[SALDO_RESPONSE],
        parameters=[{
            'name': 'tipo',
            'in_': 'query',
            'schema': {'type': 'string', 'enum': ['main', 'bonus'], 'default': 'main'},
            'description': 'Tipo de cuenta: main (principal) o bonus (bonos)',
            'required': False,
        }],
    )
    def get(self, request):
        tipo = request.GET.get('tipo', 'main')
        balance = get_balance(request.user, account_type=tipo)
        return Response({'balance': str(balance)})


class TransferirView(generics.GenericAPIView):
    serializer_class = TransferirSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'wallet'

    @extend_schema(
        summary='Transferir fondos a otro usuario',
        description='Transfiere saldo a otro usuario via partida doble (origen → destino). '
                    'Requiere saldo suficiente en la cuenta principal.',
        request=TransferirSerializer,
        responses={
            200: OpenApiTypes.OBJECT,
            400: OpenApiTypes.OBJECT,
        },
        examples=[TRANSFERIR_EXAMPLE],
        parameters=[{
            'name': 'X-Idempotency-Key',
            'in_': 'header',
            'schema': {'type': 'string'},
            'description': 'Clave de idempotencia',
        }],
    )
    def post(self, request):
        key = request.headers.get('X-Idempotency-Key') or request.data.get('idempotency_key')
        if key:
            cached = IdempotencyKey.objects.filter(key=key, user=request.user).first()
            if cached and cached.response_data:
                return Response(cached.response_data, status=status.HTTP_200_OK)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        from django.contrib.auth import get_user_model
        User = get_user_model()

        try:
            to_user = User.objects.get(username=serializer.validated_data['to_username'])
        except User.DoesNotExist:
            return Response(
                {'error': f'Usuario destino no encontrado: {serializer.validated_data["to_username"]}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            transferir(
                request.user,
                to_user,
                serializer.validated_data['amount'],
            )
            response_data = {'balance': str(get_balance(request.user, 'main'))}
            if key:
                IdempotencyKey.objects.get_or_create(
                    key=key, user=request.user,
                    defaults={'response_data': response_data},
                )
            return Response(response_data, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
