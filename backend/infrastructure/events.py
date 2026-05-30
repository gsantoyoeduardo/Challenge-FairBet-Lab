"""
Modelos de persistencia para la aplicación `events`.

Función:
- Define `Sport`, `Event`, `Market` y `Selection` que modelan el dominio
    de eventos deportivos y mercados de apuestas.

Relaciones:
- Consumidos por `application.betting` y `betting.consumers` para mostrar
    cuotas, validar apuestas y generar actualizaciones en tiempo real.
"""

from django.db import models
from django.utils import timezone
from decimal import Decimal


class Sport(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)

    class Meta:
        app_label = 'events'

    def __str__(self):
        return self.name


class Event(models.Model):
    class Status(models.TextChoices):
        PROGRAMADO = 'programado', 'Programado'
        EN_VIVO = 'en_vivo', 'En Vivo'
        FINALIZADO = 'finalizado', 'Finalizado'
        SUSPENDIDO = 'suspendido', 'Suspendido'
        ANULADO = 'anulado', 'Anulado'

    sport = models.ForeignKey(Sport, on_delete=models.CASCADE, related_name='events')
    team_home = models.CharField(max_length=200)
    team_away = models.CharField(max_length=200)
    start_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PROGRAMADO)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        app_label = 'events'
        ordering = ['start_time']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['sport', 'status']),
        ]

    def __str__(self):
        return f'{self.team_home} vs {self.team_away} ({self.status})'


class Market(models.Model):
    class MarketType(models.TextChoices):
        WIN_DRAW_WIN = '1X2', 'Ganador de Partido'
        DOUBLE_CHANCE = 'DOUBLE_CHANCE', 'Doble Oportunidad'
        DRAW_NO_BET = 'DRAW_NO_BET', 'Draw No Bet'
        OVER_UNDER_05 = 'OU_05', 'Over/Under 0.5 Goles'
        OVER_UNDER_15 = 'OU_15', 'Over/Under 1.5 Goles'
        OVER_UNDER_25 = 'OU_25', 'Over/Under 2.5 Goles'
        OVER_UNDER_35 = 'OU_35', 'Over/Under 3.5 Goles'
        OVER_UNDER_45 = 'OU_45', 'Over/Under 4.5 Goles'
        BTTS = 'BTTS', 'Ambos Equipos Anotan'
        BTTS_OU25 = 'BTTS_OU25', 'BTTS + Over/Under 2.5'
        HOME_OU_15 = 'HOME_OU_15', 'Total Goles Local O/U 1.5'
        AWAY_OU_05 = 'AWAY_OU_05', 'Total Goles Visitante O/U 0.5'
        HT_FT = 'HT_FT', 'Resultado Descanso/Final'
        HT_1X2 = 'HT_1X2', 'Primer Tiempo 1X2'
        HT_OU_15 = 'HT_OU_15', 'Primer Tiempo O/U 1.5'
        HANDICAP_0 = 'HC_0', 'Handicap Asiatico 0'
        HANDICAP_M05 = 'HC_M05', 'Handicap Asiatico -0.5'
        HANDICAP_M1 = 'HC_M1', 'Handicap Asiatico -1'
        HANDICAP_M15 = 'HC_M15', 'Handicap Asiatico -1.5'
        HANDICAP_M2 = 'HC_M2', 'Handicap Asiatico -2'
        HANDICAP_EURO = 'HC_EURO', 'Handicap Europeo -1'
        CORRECT_SCORE = 'CORRECT_SCORE', 'Marcador Exacto'
        ODD_EVEN = 'ODD_EVEN', 'Par/Impar Goles'
        BTTS_1H = 'BTTS_1H', 'Ambos Marcan 1er Tiempo'
        CLEAN_SHEET_HOME = 'CLEAN_HOME', 'Clean Sheet Local'
        CLEAN_SHEET_AWAY = 'CLEAN_AWAY', 'Clean Sheet Visitante'
        FIRST_TO_SCORE = 'FIRST_SCORE', 'Primer Equipo en Anotar'
        MULTI_GOALS_HOME = 'MULTI_HOME', 'Multi-Goles Local'
        MULTI_GOALS_AWAY = 'MULTI_AWAY', 'Multi-Goles Visitante'
        CORNERS_OU = 'CORNERS_OU', 'Córneres O/U 9.5'
        TENNIS_WINNER = 'TENNIS_WINNER', 'Ganador del Partido'
        TENNIS_HANDICAP = 'TENNIS_HC', 'Hándicap Juegos'
        TENNIS_TOTAL = 'TENNIS_TOTAL', 'Total Juegos O/U'
        TENNIS_SET_BET = 'TENNIS_SET', 'Set Betting'
        TENNIS_SET1 = 'TENNIS_SET1', 'Primer Set Ganador'
        TENNIS_SET1_TOTAL = 'TENNIS_SET1_TOT', 'Total Juegos Set 1 O/U'
        TENNIS_BOTH_SETS = 'TENNIS_BOTH', 'Ambos Ganaran un Set'
        BASKET_MONEYLINE = 'BASKET_ML', 'Moneyline'
        BASKET_SPREAD = 'BASKET_SPREAD', 'Spread'
        BASKET_TOTAL = 'BASKET_TOTAL', 'Total Puntos O/U'
        BASKET_HT_SPREAD = 'BASKET_HT_SPR', 'Handicap Mitad'
        BASKET_HT_ML = 'BASKET_HT_ML', 'Mitad 1X2'
        BASKET_HOME_TOTAL = 'BASKET_HOME_TOT', 'Total Puntos Local O/U'

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='markets')
    type = models.CharField(max_length=30, choices=MarketType.choices)
    name = models.CharField(max_length=200)
    is_live = models.BooleanField(default=False)
    suspended_until = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = 'events'
        unique_together = ('event', 'type')

    def __str__(self):
        return f'{self.event} - {self.name}'


class Selection(models.Model):
    market = models.ForeignKey(Market, on_delete=models.CASCADE, related_name='selections')
    name = models.CharField(max_length=200)
    odds = models.DecimalField(max_digits=18, decimal_places=4)
    is_winner = models.BooleanField(null=True, blank=True, default=None)

    class Meta:
        app_label = 'events'

    def __str__(self):
        return f'{self.name} @ {self.odds}'
