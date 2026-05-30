from django.urls import path
from controllers.operator import MetricsView, ExposureView, ReporteView, BetListView

urlpatterns = [
    path('metrics/', MetricsView.as_view(), name='operator-metrics'),
    path('exposure/<int:event_id>/', ExposureView.as_view(), name='operator-exposure'),
    path('reporte/', ReporteView.as_view(), name='operator-reporte'),
    path('bets/', BetListView.as_view(), name='operator-bets'),
]
