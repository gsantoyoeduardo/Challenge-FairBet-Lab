"""
Casos de uso y serializadores para métricas del operador.

Función:
- Expone serializers usados por endpoints administrativos para calcular
    métricas (GGR, exposición) y generar reportes CSV.

Relaciones:
- Usa funciones puras en `domain.operator` para los cálculos.
"""

from rest_framework import serializers
from domain.operator import calcular_ggr, calcular_exposure, generar_reporte_csv


class MetricsSerializer(serializers.Serializer):
    total_stakes = serializers.CharField()
    total_payouts = serializers.CharField()
    ggr = serializers.CharField()
    total_bets = serializers.IntegerField()
    active_users = serializers.IntegerField(required=False, default=0)
    active_bets = serializers.IntegerField(required=False, default=0)


class ExposureItemSerializer(serializers.Serializer):
    selection_id = serializers.IntegerField()
    selection_name = serializers.CharField()
    odds = serializers.CharField()
    bets_count = serializers.IntegerField()
    potential_payout = serializers.CharField()
