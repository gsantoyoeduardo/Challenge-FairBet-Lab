"""
Módulo `application.betting` — Casos de uso para la gestión de apuestas.

Función:
- Orquesta la creación de apuestas (simples, combinadas, sistemas), cash-out
    y liquidación de apuestas.
- Realiza validaciones de negocio y coordina movimientos contables via
    `application.wallet.create_double_entry`.

Relaciones:
- Llamado desde `controllers/betting.py` para atender las rutas HTTP.
- Usa `domain.betting` para reglas puras y `infrastructure.*` para modelos.
"""

import logging
from decimal import Decimal
from itertools import combinations

from django.db import transaction
from rest_framework import serializers

from infrastructure.betting import Bet, BetSelection
from infrastructure.events import Selection, Market, Event
from infrastructure.users import UserProfile, IdempotencyKey
from domain.betting import (
    is_valid_transition, is_terminal_status,
    validate_bet_stake, validate_odds, validate_mutual_exclusion,
    validate_event_not_started,
)
from domain.events import calculate_payout, calculate_cashout, CASHOUT_HOUSE_FACTOR
from application.responsible_gaming import validate_user_limits
from application.bonuses import process_rollover_contribution

logger = logging.getLogger(__name__)

SISTEMA_TYPES = {
    'trixie': {'selections': 3, 'combinations': [(2, 3), (3, 1)], 'name': 'Trixie (4 apuestas)'},
    'yankee': {'selections': 4, 'combinations': [(2, 6), (3, 4), (4, 1)], 'name': 'Yankee (11 apuestas)'},
    'patent': {'selections': 3, 'combinations': [(1, 3), (2, 3), (3, 1)], 'name': 'Patent (7 apuestas)'},
    'lucky15': {'selections': 4, 'combinations': [(1, 4), (2, 6), (3, 4), (4, 1)], 'name': 'Lucky 15 (15 apuestas)'},
}


class ApostarSerializer(serializers.Serializer):
    selections = serializers.ListField(min_length=1, child=serializers.DictField())
    stake = serializers.DecimalField(max_digits=18, decimal_places=4)
    expected_odds = serializers.DictField(
        child=serializers.DecimalField(max_digits=18, decimal_places=4),
        required=False,
        help_text='{selection_id: odds_esperada} para re-cotizacion',
    )
    sistema_tipo = serializers.ChoiceField(
        choices=list(SISTEMA_TYPES.keys()), required=False,
        help_text='trixie/yankee/patent/lucky15 para apuesta de sistema',
    )
    idempotency_key = serializers.CharField(max_length=128, required=False, allow_blank=True)


class CashOutSerializer(serializers.Serializer):
    idempotency_key = serializers.CharField(max_length=128, required=False, allow_blank=True)


class BetSelectionNestedSerializer(serializers.Serializer):
    selection_id = serializers.IntegerField()
    selection_name = serializers.CharField(source='selection.name')
    market_type = serializers.CharField(source='selection.market.type')
    market_name = serializers.CharField(source='selection.market.name')
    event = serializers.SerializerMethodField()
    odds_at_time = serializers.DecimalField(max_digits=18, decimal_places=4)

    def get_event(self, obj):
        event = obj.selection.market.event
        return {
            'id': event.id,
            'home': event.team_home,
            'away': event.team_away,
        }


class BetSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    selections = BetSelectionNestedSerializer(many=True, read_only=True)
    cashout_preview = serializers.SerializerMethodField()

    class Meta:
        model = Bet
        fields = ('id', 'username', 'stake', 'total_odds', 'status',
                  'placed_at', 'settled_at', 'payout', 'selections', 'cashout_preview')

    def get_cashout_preview(self, obj):
        if obj.status != 'accepted':
            return None
        try:
            selections = obj.selections.select_related('selection').all()
            current_implied = Decimal('1.0000')
            for bs in selections:
                current_implied *= bs.selection.odds
            cashout_amount = obj.stake * obj.total_odds / current_implied
            cashout_amount = (cashout_amount * CASHOUT_HOUSE_FACTOR).quantize(Decimal('0.0001'))
            return str(cashout_amount)
        except Exception:
            return None


def validar_usuario_apto(user) -> str | None:
    if user.is_staff:
        return None
    try:
        profile = user.profile
    except UserProfile.DoesNotExist:
        return 'Perfil no encontrado'
    if profile.estado_cuenta != 'verificado':
        return f'Cuenta {profile.estado_cuenta}. Solo cuentas verificadas pueden apostar.'
    return None


def realizar_apuesta(user, selections_data: list[dict], stake: Decimal,
                     expected_odds: dict = None) -> Bet:
    error = validar_usuario_apto(user)
    if error:
        raise ValueError(error)

    limit_error = validate_user_limits(user, stake)
    if limit_error:
        raise ValueError(limit_error)

    is_combined = len(selections_data) > 1
    stake_error = validate_bet_stake(stake, is_combined)
    if stake_error:
        raise ValueError(stake_error)

    total_odds = Decimal('1.0000')
    selection_objs = []
    seen_combos = {}  # {(event_id, market_id): selection_name}

    for sel_data in selections_data:
        sel_id = sel_data['selection_id']
        sel = Selection.objects.select_related('market__event').get(id=sel_id)
        selection_objs.append(sel)
        event = sel.market.event
        market = sel.market
        event_error = validate_event_not_started(event.status)
        if event_error:
            raise ValueError(f'{event.team_home} vs {event.team_away}: {event_error}')
        if market.suspended_until and market.suspended_until > timezone_now():
            remaining = (market.suspended_until - timezone_now()).seconds
            raise ValueError(
                f'Mercado "{market.name}" suspendido temporalmente. '
                f'Disponible en {remaining}s'
            )
        odds_error = validate_odds(sel.odds)
        if odds_error:
            raise ValueError(f'{sel.name}: {odds_error}')
        if expected_odds:
            expected = expected_odds.get(str(sel_id))
            if expected and expected != sel.odds:
                raise RecotizacionException(
                    f'Cuota de "{sel.name}" cambio de {expected} a {sel.odds}. Confirma.',
                    selection_id=sel_id, old_odds=expected, new_odds=sel.odds)
        total_odds *= sel.odds

        # Validacion de combinaciones: no repetir mismo mercado del mismo evento
        combo_key = (event.id, market.id)
        if is_combined and combo_key in seen_combos:
            prev_sel = seen_combos[combo_key]
            raise ValueError(
                f'No se puede combinar "{sel.name}" con "{prev_sel}" '
                f'del mismo mercado "{market.name}" en {event.team_home} vs {event.team_away}'
            )
        seen_combos[combo_key] = sel.name

    # Validacion de exclusion mutua en 1X2 del mismo evento
    if is_combined:
        for (ev_id, mkt_id), sel_name in seen_combos.items():
            market = Market.objects.get(id=mkt_id)
            if market.type == '1X2':
                names_in_event = [
                    n for (e, m), n in seen_combos.items()
                    if e == ev_id and m == mkt_id
                ]
                if len(names_in_event) > 1:
                    raise ValueError(
                        f'No se puede combinar selecciones mutuamente excluyentes '
                        f'del mercado 1X2: {", ".join(names_in_event)}'
                    )

    from application.wallet import get_balance as wallet_balance
    from infrastructure.wallet import Account

    with transaction.atomic():
        wallet = Account.objects.select_for_update().get(user=user, type='main')
        apuestas = Account.objects.select_for_update().get(type='apuestas_pendientes')

        balance = wallet_balance(user, 'main')
        if balance < stake:
            raise ValueError(f'Saldo insuficiente. Disponible: {balance} BP')

        bet = Bet.objects.create(user=user, stake=stake, total_odds=total_odds, status='accepted')
        for sel in selection_objs:
            BetSelection.objects.create(bet=bet, selection=sel, odds_at_time=sel.odds)

        from application.wallet import create_double_entry
        create_double_entry(wallet, apuestas, stake, f'Apuesta #{bet.id}')

    process_rollover_contribution(user, stake, min(s.odds_at_time for s in bet.selections.all()))

    return bet


def liquidar_apuesta(bet_id: int, winning_selection_ids: list[int] | None = None):
    with transaction.atomic():
        bet = Bet.objects.select_for_update().get(id=bet_id)
        if is_terminal_status(bet.status):
            raise ValueError(f'Apuesta ya liquidada: {bet.status}')

        from infrastructure.wallet import Account
        from application.wallet import create_double_entry

        apuestas = Account.objects.select_for_update().get(type='apuestas_pendientes')
        wallet = Account.objects.select_for_update().get(user=bet.user, type='main')
        casa = Account.objects.select_for_update().get(type='casa')

        selections = bet.selections.select_related('selection__market__event').all()
        all_won = all(
            bs.selection.is_winner is True or
            (winning_selection_ids and bs.selection_id in winning_selection_ids)
            for bs in selections
        )

        if all_won:
            payout = calculate_payout(bet.stake, bet.total_odds)
            create_double_entry(apuestas, wallet, bet.stake, f'Devolucion stake apuesta #{bet.id}')
            ganancia = payout - bet.stake
            if ganancia > 0:
                create_double_entry(casa, wallet, ganancia, f'Ganancia apuesta #{bet.id}')
            bet.status = 'won'
            bet.payout = payout
        else:
            create_double_entry(apuestas, casa, bet.stake, f'Stake perdido apuesta #{bet.id}')
            bet.status = 'lost'
            bet.payout = Decimal('0.0000')

        bet.settled_at = timezone_now()
        bet.save()
    return bet


def cash_out_apuesta(bet_id: int):
    with transaction.atomic():
        bet = Bet.objects.select_for_update().get(id=bet_id)
        if bet.status != 'accepted':
            raise ValueError(f'Apuesta no elegible para cash-out. Estado: {bet.status}')

        selections = bet.selections.select_related('selection').all()
        current_implied = Decimal('1.0000')
        for bs in selections:
            current_implied *= bs.selection.odds

        cashout_amount = bet.stake * bet.total_odds / current_implied
        cashout_amount = (cashout_amount * CASHOUT_HOUSE_FACTOR).quantize(Decimal('0.0001'))

        from infrastructure.wallet import Account
        from application.wallet import create_double_entry

        apuestas = Account.objects.select_for_update().get(type='apuestas_pendientes')
        wallet = Account.objects.select_for_update().get(user=bet.user, type='main')
        create_double_entry(apuestas, wallet, cashout_amount, f'Cash-out apuesta #{bet.id}')

        bet.status = 'cashed_out'
        bet.payout = cashout_amount
        bet.settled_at = timezone_now()
        bet.save()
    return bet


def realizar_apuesta_sistema(user, selections_data: list[dict], stake_per_line: Decimal,
                              sistema_tipo: str, expected_odds: dict = None) -> list[Bet]:
    if sistema_tipo not in SISTEMA_TYPES:
        raise ValueError(f'Sistema no soportado: {sistema_tipo}')
    config = SISTEMA_TYPES[sistema_tipo]
    if len(selections_data) != config['selections']:
        raise ValueError(f'{config["name"]} requiere exactamente {config["selections"]} selecciones')

    error = validar_usuario_apto(user)
    if error:
        raise ValueError(error)

    selection_objs = []
    event_ids = set()
    for sel_data in selections_data:
        sel = Selection.objects.select_related('market__event').get(id=sel_data['selection_id'])
        selection_objs.append(sel)
        event = sel.market.event
        if evento_error := validate_event_not_started(event.status):
            raise ValueError(f'{event.team_home} vs {event.team_away}: {evento_error}')
        if event.id in event_ids:
            raise ValueError(f'No se puede combinar mismo partido')
        if odds_error := validate_odds(sel.odds):
            raise ValueError(f'{sel.name}: {odds_error}')
        event_ids.add(event.id)

    total_bets = sum(count for _, count in config['combinations'])
    total_stake = stake_per_line * total_bets

    from application.wallet import get_balance as wallet_balance
    balance = wallet_balance(user, 'main')
    if balance < total_stake:
        raise ValueError(f'Saldo insuficiente. Necesitas {total_stake} BP, disponible: {balance} BP')

    bets_created = []
    with transaction.atomic():
        from infrastructure.wallet import Account

        wallet = Account.objects.select_for_update().get(user=user, type='main')
        apuestas = Account.objects.select_for_update().get(type='apuestas_pendientes')
        balance = wallet_balance(user, 'main')
        if balance < total_stake:
            raise ValueError(f'Saldo insuficiente')

        for combo_size, count in config['combinations']:
            for combo in combinations(selection_objs, combo_size):
                total_odds = Decimal('1.0000')
                for sel in combo:
                    total_odds *= sel.odds

                bet = Bet.objects.create(user=user, stake=stake_per_line,
                                         total_odds=total_odds, status='accepted')
                for sel in combo:
                    BetSelection.objects.create(bet=bet, selection=sel, odds_at_time=sel.odds)

                from application.wallet import create_double_entry
                create_double_entry(wallet, apuestas, stake_per_line,
                                    f'Sistema {sistema_tipo} apuesta #{bet.id}')
                bets_created.append(bet)
    return bets_created


def timezone_now():
    from django.utils import timezone
    return timezone.now()


class RecotizacionException(Exception):
    def __init__(self, message, selection_id, old_odds, new_odds):
        self.message = message
        self.selection_id = selection_id
        self.old_odds = old_odds
        self.new_odds = new_odds
        super().__init__(message)
