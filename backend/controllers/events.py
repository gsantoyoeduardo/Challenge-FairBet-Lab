from decimal import Decimal
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiTypes

from infrastructure.events import Event, Market, Sport
from application.events import (
    SportSerializer, EventListSerializer, EventDetailSerializer,
    MarketSerializer,
)


class EventListView(generics.ListAPIView):
    serializer_class = EventListSerializer
    permission_classes = [AllowAny]
    pagination_class = PageNumberPagination

    def get_queryset(self):
        qs = Event.objects.select_related('sport').all()
        sport = self.request.query_params.get('sport')
        status_param = self.request.query_params.get('status')
        if sport:
            qs = qs.filter(sport__slug=sport)
        if status_param:
            qs = qs.filter(status=status_param)
        return qs

    @extend_schema(
        summary='Listar eventos',
        description='Eventos con filtro por deporte y estado',
        parameters=[
            {'name': 'sport', 'in_': 'query', 'schema': {'type': 'string'}, 'description': 'Slug del deporte'},
            {'name': 'status', 'in_': 'query', 'schema': {'type': 'string'}, 'description': 'programado/en_vivo/finalizado'},
        ],
        responses={200: EventListSerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class EventDetailView(generics.RetrieveAPIView):
    serializer_class = EventDetailSerializer
    permission_classes = [AllowAny]
    queryset = Event.objects.select_related('sport').prefetch_related(
        'markets__selections'
    ).all()

    @extend_schema(
        summary='Detalle de evento',
        description='Evento con sus mercados y selecciones (odds)',
        responses={200: EventDetailSerializer},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class LiveEventListView(generics.ListAPIView):
    serializer_class = EventListSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Event.objects.filter(status='en_vivo').select_related('sport')

    @extend_schema(
        summary='Eventos en vivo',
        description='Lista de eventos con estado en_vivo',
        responses={200: EventListSerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class MarketDetailView(generics.RetrieveAPIView):
    serializer_class = MarketSerializer
    permission_classes = [AllowAny]
    queryset = Market.objects.prefetch_related('selections').all()

    @extend_schema(
        summary='Detalle de mercado',
        description='Mercado con sus selecciones y odds',
        responses={200: MarketSerializer},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class SportListView(generics.ListAPIView):
    serializer_class = SportSerializer
    permission_classes = [AllowAny]
    queryset = Sport.objects.all()

    @extend_schema(
        summary='Listar deportes',
        responses={200: SportSerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class ChangeEventStatusView(generics.GenericAPIView):
    permission_classes = [IsAdminUser]

    @extend_schema(
        summary='Cambiar estado de evento (admin)',
        description='Permite al administrador cambiar el estado de un evento: programado, en_vivo, finalizado, suspendido, anulado.',
        request=OpenApiTypes.OBJECT,
        responses={
            200: OpenApiTypes.OBJECT,
            400: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample('Suspender evento', value={'status': 'suspendido'}),
            OpenApiExample('Anular evento', value={'status': 'anulado'}),
        ],
    )
    def post(self, request, event_id):
        try:
            event = Event.objects.select_related('sport').get(id=event_id)
        except Event.DoesNotExist:
            return Response({'error': 'Evento no encontrado'}, status=status.HTTP_404_NOT_FOUND)

        new_status = request.data.get('status')
        valid_statuses = [s[0] for s in Event.Status.choices]
        if new_status not in valid_statuses:
            return Response(
                {'error': f'Estado invalido. Opciones: {valid_statuses}'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        old_status = event.status
        event.status = new_status
        event.save()

        return Response({
            'event_id': event.id,
            'event_name': str(event),
            'old_status': old_status,
            'new_status': event.status,
        })


class SetSelectionWinnerView(generics.GenericAPIView):
    permission_classes = [IsAdminUser]

    @extend_schema(
        summary='Marcar seleccion como ganadora (admin)',
        description='Define si una seleccion es ganadora (is_winner=True/False). '
                    'Usado para liquidar apuestas automaticamente.',
        request=OpenApiTypes.OBJECT,
        responses={
            200: OpenApiTypes.OBJECT,
            400: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample('Marcar ganadora', value={'is_winner': True}),
            OpenApiExample('Marcar perdedora', value={'is_winner': False}),
        ],
    )
    def post(self, request, selection_id):
        from infrastructure.events import Selection
        try:
            sel = Selection.objects.select_related('market__event').get(id=selection_id)
        except Selection.DoesNotExist:
            return Response({'error': 'Seleccion no encontrada'}, status=status.HTTP_404_NOT_FOUND)

        is_winner = request.data.get('is_winner')
        if not isinstance(is_winner, bool):
            return Response(
                {'error': 'El campo is_winner debe ser true o false'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        sel.is_winner = is_winner
        sel.save()

        return Response({
            'selection_id': sel.id,
            'selection_name': sel.name,
            'market': sel.market.name,
            'event': str(sel.market.event),
            'is_winner': sel.is_winner,
        })


class CreateEventView(generics.GenericAPIView):
    permission_classes = [IsAdminUser]

    @extend_schema(
        summary='Crear evento (admin)',
        description='Crea un nuevo evento con mercados y selecciones generados automaticamente.',
        request=OpenApiTypes.OBJECT,
        responses={
            201: OpenApiTypes.OBJECT,
            400: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                'Crear evento futbol',
                value={
                    'sport_slug': 'football',
                    'team_home': 'Alianza Lima',
                    'team_away': 'Universitario',
                    'start_time': '2026-06-01T20:00:00Z',
                    'status': 'programado',
                },
                request_only=True,
            ),
        ],
    )
    def post(self, request):
        from django.utils import timezone
        from datetime import datetime

        sport_slug = request.data.get('sport_slug')
        team_home = request.data.get('team_home')
        team_away = request.data.get('team_away')
        start_time_str = request.data.get('start_time')
        event_status = request.data.get('status', 'programado')

        if not sport_slug or not team_home or not team_away:
            return Response(
                {'error': 'sport_slug, team_home y team_away son requeridos'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            sport = Sport.objects.get(slug=sport_slug)
        except Sport.DoesNotExist:
            return Response(
                {'error': f'Deporte "{sport_slug}" no encontrado'},
                status=status.HTTP_404_NOT_FOUND,
            )

        start_time = timezone.now()
        if start_time_str:
            try:
                start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
            except ValueError:
                return Response(
                    {'error': 'Formato de start_time invalido. Use ISO 8601 (YYYY-MM-DDTHH:MM:SSZ)'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        event = Event.objects.create(
            sport=sport,
            team_home=team_home,
            team_away=team_away,
            start_time=start_time,
            status=event_status,
        )

        from domain.events import (
            generate_1X2, generate_double_chance, generate_draw_no_bet,
            generate_ou_goals, generate_btts, generate_handicap,
            calculate_odds_with_margin,
        )
        from django.conf import settings
        margin = Decimal(settings.EVENTS_MARGIN_FACTOR)

        raw_1X2 = generate_1X2()
        o1, oX, o2 = calculate_odds_with_margin(raw_1X2, margin) if margin > 0 else raw_1X2
        mkt = Market.objects.create(event=event, type='1X2', name='Ganador de Partido')
        mkt.selections.create(name='Local', odds=o1)
        mkt.selections.create(name='Empate', odds=oX)
        mkt.selections.create(name='Visitante', odds=o2)

        dc = generate_double_chance(o1, oX, o2)
        mkt_dc = Market.objects.create(event=event, type='DOUBLE_CHANCE', name='Doble Oportunidad')
        mkt_dc.selections.create(name='1X', odds=dc[0])
        mkt_dc.selections.create(name='12', odds=dc[1])
        mkt_dc.selections.create(name='X2', odds=dc[2])

        ou_ov, ou_un = generate_ou_goals()
        mkt_ou = Market.objects.create(event=event, type='OU_25', name='Over/Under 2.5')
        mkt_ou.selections.create(name='Over', odds=ou_ov)
        mkt_ou.selections.create(name='Under', odds=ou_un)

        btts_si, btts_no = generate_btts()
        mkt_btts = Market.objects.create(event=event, type='BTTS', name='Ambos Equipos Anotan')
        mkt_btts.selections.create(name='Si', odds=btts_si)
        mkt_btts.selections.create(name='No', odds=btts_no)

        return Response({
            'id': event.id,
            'sport': sport.name,
            'team_home': event.team_home,
            'team_away': event.team_away,
            'start_time': event.start_time.isoformat(),
            'status': event.status,
            'markets_created': 4,
        }, status=status.HTTP_201_CREATED)


class SuspendMarketView(generics.GenericAPIView):
    permission_classes = [IsAdminUser]

    @extend_schema(
        summary='Suspender mercado (admin)',
        description='Suspende un mercado temporalmente o permanentemente.',
        request=OpenApiTypes.OBJECT,
        responses={
            200: OpenApiTypes.OBJECT,
            400: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample('Suspender 60 segundos', value={'suspended_until': 60}),
            OpenApiExample('Suspender permanentemente', value={'suspended_until': None}),
        ],
    )
    def post(self, request, market_id):
        from django.utils import timezone
        from datetime import timedelta

        try:
            market = Market.objects.select_related('event').get(id=market_id)
        except Market.DoesNotExist:
            return Response({'error': 'Mercado no encontrado'}, status=status.HTTP_404_NOT_FOUND)

        suspended_until = request.data.get('suspended_until')

        if suspended_until is None:
            market.suspended_until = None
        elif isinstance(suspended_until, (int, float)):
            market.suspended_until = timezone.now() + timedelta(seconds=int(suspended_until))
        else:
            market.suspended_until = None

        market.save()

        return Response({
            'market_id': market.id,
            'market_name': market.name,
            'event': str(market.event),
            'suspended_until': market.suspended_until.isoformat() if market.suspended_until else None,
        })
