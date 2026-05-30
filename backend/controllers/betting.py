"""
Controladores HTTP para la API de `betting`.

Función:
- Manejan endpoints para apostar, cash-out, listar apuestas y
    liquidar — validan requests y llaman a `application.betting`.

Relaciones:
- Delegan la lógica de negocio a `application.betting` y persisten mediante
    `infrastructure` cuando corresponda.
"""

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiTypes

from application.betting import (
    ApostarSerializer, CashOutSerializer, BetSerializer,
    realizar_apuesta, realizar_apuesta_sistema, liquidar_apuesta, cash_out_apuesta,
    RecotizacionException,
)
from infrastructure.betting import Bet
from infrastructure.users import IdempotencyKey
from decimal import Decimal
from domain.events import CASHOUT_HOUSE_FACTOR

APOSTAR_EXAMPLE = OpenApiExample(
    'Apuesta simple 1X2',
    value={
        'selections': [{'selection_id': 1}],
        'stake': '100.0000',
        'expected_odds': {'1': '2.5000'},
        'idempotency_key': 'abc-123',
    },
    request_only=True,
)

CASHOUT_EXAMPLE = OpenApiExample(
    'Cash-out anticipado',
    value={'idempotency_key': 'abc-456'},
    request_only=True,
)


class ApostarView(generics.GenericAPIView):
    serializer_class = ApostarSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'apuesta'

    @extend_schema(
        summary='Realizar apuesta',
        description='Crea apuesta simple o combinada. Bloquea fondos via partida doble. '
                    'Si expected_odds difiere de odds actual, retorna 409 para re-cotizacion.',
        request=ApostarSerializer,
        responses={
            201: BetSerializer,
            400: OpenApiTypes.OBJECT,
            409: OpenApiTypes.OBJECT,
        },
        examples=[APOSTAR_EXAMPLE],
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
                return Response(cached.response_data, status=status.HTTP_201_CREATED)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            sistema_tipo = serializer.validated_data.get('sistema_tipo')
            if sistema_tipo:
                bets = realizar_apuesta_sistema(
                    request.user,
                    serializer.validated_data['selections'],
                    serializer.validated_data['stake'],
                    sistema_tipo,
                    serializer.validated_data.get('expected_odds'),
                )
                response_data = {'bets': BetSerializer(bets, many=True).data, 'total_bets': len(bets)}
            else:
                bet = realizar_apuesta(
                    request.user,
                    serializer.validated_data['selections'],
                    serializer.validated_data['stake'],
                    serializer.validated_data.get('expected_odds'),
                )
                response_data = BetSerializer(bet).data
            if key:
                IdempotencyKey.objects.get_or_create(
                    key=key, user=request.user,
                    defaults={'response_data': response_data},
                )
            return Response(response_data, status=status.HTTP_201_CREATED)

        except RecotizacionException as e:
            return Response({
                'error': e.message,
                'selection_id': e.selection_id,
                'old_odds': str(e.old_odds),
                'new_odds': str(e.new_odds),
            }, status=status.HTTP_409_CONFLICT)

        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CashOutView(generics.GenericAPIView):
    serializer_class = CashOutSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='Cash-out anticipado',
        description='Cierra apuesta accepted antes del resultado final. '
                    'cashout = stake * odds_original / odds_actual * factor_casa',
        request=CashOutSerializer,
        responses={
            200: BetSerializer,
            400: OpenApiTypes.OBJECT,
        },
        examples=[CASHOUT_EXAMPLE],
    )
    def post(self, request, bet_id):
        key = request.headers.get('X-Idempotency-Key') or request.data.get('idempotency_key')
        if key:
            cached = IdempotencyKey.objects.filter(key=key, user=request.user).first()
            if cached and cached.response_data:
                return Response(cached.response_data)

        try:
            bet = cash_out_apuesta(bet_id)
            response_data = BetSerializer(bet).data
            if key:
                IdempotencyKey.objects.get_or_create(
                    key=key, user=request.user,
                    defaults={'response_data': response_data},
                )
            return Response(response_data, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CashOutPreviewView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='Preview de cash-out',
        description='Calcula el monto de cash-out sin ejecutar la operacion.',
        responses={
            200: OpenApiTypes.OBJECT,
            400: OpenApiTypes.OBJECT,
        },
    )
    def get(self, request, bet_id):
        try:
            bet = Bet.objects.select_related('user').prefetch_related(
                'selections__selection'
            ).get(id=bet_id, user=request.user)
            if bet.status != 'accepted':
                return Response(
                    {'error': f'Apuesta no elegible. Estado: {bet.status}'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            selections = bet.selections.select_related('selection').all()
            current_implied = Decimal('1.0000')
            for bs in selections:
                current_implied *= bs.selection.odds
            cashout_amount = bet.stake * bet.total_odds / current_implied
            cashout_amount = (cashout_amount * CASHOUT_HOUSE_FACTOR).quantize(Decimal('0.0001'))
            return Response({
                'bet_id': bet_id,
                'stake': str(bet.stake),
                'total_odds': str(bet.total_odds),
                'cashout_amount': str(cashout_amount),
            })
        except Bet.DoesNotExist:
            return Response({'error': 'Apuesta no encontrada'}, status=status.HTTP_404_NOT_FOUND)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class MisApuestasView(generics.ListAPIView):
    serializer_class = BetSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination

    def get_queryset(self):
        qs = Bet.objects.filter(user=self.request.user)
        status_param = self.request.query_params.get('status')
        if status_param:
            qs = qs.filter(status=status_param)
        return qs.select_related('user').prefetch_related('selections__selection')

    @extend_schema(
        summary='Mis apuestas',
        description='Historial de apuestas del usuario autenticado. Filtro por status.',
        parameters=[{
            'name': 'status',
            'in_': 'query',
            'schema': {'type': 'string'},
            'description': 'accepted/won/lost/cashed_out/cancelled',
        }],
        responses={200: BetSerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class LiquidarApuestaView(generics.GenericAPIView):
    permission_classes = [IsAdminUser]

    @extend_schema(
        summary='Liquidar apuesta (admin)',
        description='Resuelve el resultado de una apuesta. '
                    'Calcula payout automaticamente y mueve fondos via partida doble. '
                    'Si se envia winning_selection_ids, esos IDs se consideran ganadores.',
        request=OpenApiTypes.OBJECT,
        responses={
            200: BetSerializer,
            400: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                'Liquidar con IDs ganadores',
                value={'winning_selection_ids': [5920, 5922]},
                request_only=True,
            ),
        ],
    )
    def post(self, request, bet_id):
        winning_ids = request.data.get('winning_selection_ids')

        try:
            bet = liquidar_apuesta(bet_id, winning_ids)
            return Response(BetSerializer(bet).data, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
