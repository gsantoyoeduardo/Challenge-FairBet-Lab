"""
Controladores administrativos para métricas y reportes del operador.

Función:
- Exponer métricas (GGR, exposición) y generación de reportes CSV para
    uso interno del operador.

Relaciones:
- Consume funciones en `domain.operator` y `application.operator`.
"""

from django.http import HttpResponse
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from drf_spectacular.utils import extend_schema, OpenApiParameter

from domain.operator import calcular_ggr, calcular_exposure, generar_reporte_csv
from application.operator import MetricsSerializer
from application.betting import BetSerializer
from infrastructure.betting import Bet


class MetricsView(generics.GenericAPIView):
    permission_classes = [permissions.IsAdminUser]
    serializer_class = MetricsSerializer

    @extend_schema(
        summary='Metricas del operador',
        description='GGR, total apostado, total pagado, usuarios activos. '
                    'Filtros opcionales: ?desde=YYYY-MM-DD&hasta=YYYY-MM-DD.',
        parameters=[
            OpenApiParameter(name='desde', type=str, location=OpenApiParameter.QUERY, description='Fecha inicio (YYYY-MM-DD)'),
            OpenApiParameter(name='hasta', type=str, location=OpenApiParameter.QUERY, description='Fecha fin (YYYY-MM-DD)'),
        ],
    )
    def get(self, request):
        from django.utils import timezone
        from datetime import datetime, timedelta
        desde_str = request.GET.get('desde')
        hasta_str = request.GET.get('hasta')
        desde = datetime.strptime(desde_str, '%Y-%m-%d').date() if desde_str else None
        hasta = datetime.strptime(hasta_str, '%Y-%m-%d').date() if hasta_str else None

        metrics = calcular_ggr(desde, hasta)
        from django.db.models import Count

        semana = timezone.now() - timedelta(days=7)
        active_users = Bet.objects.filter(placed_at__gte=semana).values('user').distinct().count()
        active_bets = Bet.objects.filter(status='accepted').count()

        metrics['active_users'] = active_users
        metrics['active_bets'] = active_bets

        return Response(metrics)


class ExposureView(generics.GenericAPIView):
    permission_classes = [permissions.IsAdminUser]

    @extend_schema(
        summary='Exposure por evento',
        description='Cuanto pierde la casa si gana cada seleccion del evento.',
        parameters=[
            OpenApiParameter(name='event_id', type=int, location=OpenApiParameter.PATH),
        ],
    )
    def get(self, request, event_id: int):
        try:
            result = calcular_exposure(event_id)
            return Response(result)
        except Exception as e:
            return Response({'error': str(e)}, status=400)


class ReporteView(generics.GenericAPIView):
    permission_classes = [permissions.IsAdminUser]

    @extend_schema(
        summary='Descargar reporte CSV',
        description='Reporte MINCETUR en formato CSV con filtro por mes y anio.',
        parameters=[
            OpenApiParameter(name='mes', type=int, location=OpenApiParameter.QUERY),
            OpenApiParameter(name='anio', type=int, location=OpenApiParameter.QUERY),
        ],
    )
    def get(self, request):
        from django.utils import timezone
        now = timezone.now()
        mes = int(request.GET.get('mes', now.month))
        anio = int(request.GET.get('anio', now.year))

        try:
            csv_content = generar_reporte_csv(mes, anio)
            response = HttpResponse(csv_content, content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="reporte_{anio}_{mes:02d}.csv"'
            return response
        except Exception as e:
            return Response({'error': str(e)}, status=400)


class BetListView(generics.ListAPIView):
    serializer_class = BetSerializer
    permission_classes = [permissions.IsAdminUser]
    pagination_class = PageNumberPagination

    def get_queryset(self):
        qs = Bet.objects.select_related('user').prefetch_related('selections__selection__market__event')
        status_param = self.request.query_params.get('status')
        if status_param:
            qs = qs.filter(status=status_param)
        return qs.order_by('-placed_at')

    @extend_schema(
        summary='Listar todas las apuestas (admin)',
        description='Lista todas las apuestas del sistema con filtro por status.',
        parameters=[
            OpenApiParameter(name='status', type=str, location=OpenApiParameter.QUERY, description='accepted/won/lost/cashed_out/cancelled'),
        ],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class ExposureSummaryView(generics.GenericAPIView):
    permission_classes = [permissions.IsAdminUser]

    @extend_schema(
        summary='Resumen de exposure por evento',
        description='Lista todos los eventos con apuestas activas y su exposure total.',
    )
    def get(self, request):
        from decimal import Decimal
        from django.db.models import Count, Max, Sum, F
        from infrastructure.events import Event

        events_with_bets = (
            Bet.objects
            .filter(status='accepted')
            .select_related('selections__selection__market__event')
            .prefetch_related('selections__selection__market__event')
            .values(
                'selections__selection__market__event_id',
                'selections__selection__market__event__team_home',
                'selections__selection__market__event__team_away',
                'selections__selection__market__event__sport__name',
                'selections__selection__market__event__start_time',
                'selections__selection__market__event__status',
            )
            .annotate(
                total_bets=Count('id', distinct=True),
                max_payout=Max(F('stake') * F('total_odds')),
            )
            .order_by('-max_payout')
        )

        summary = []
        for item in events_with_bets:
            event_id = item['selections__selection__market__event_id']
            summary.append({
                'event_id': event_id,
                'team_home': item['selections__selection__market__event__team_home'],
                'team_away': item['selections__selection__market__event__team_away'],
                'sport': item['selections__selection__market__event__sport__name'],
                'start_time': item['selections__selection__market__event__start_time'],
                'status': item['selections__selection__market__event__status'],
                'total_bets': item['total_bets'],
                'max_payout': str(item['max_payout']),
            })

        return Response(summary)
