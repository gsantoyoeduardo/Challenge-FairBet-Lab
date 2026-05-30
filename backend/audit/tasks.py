import logging
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from infrastructure.betting import Bet
from infrastructure.audit import SuspiciousActivity
from application.responsible_gaming import check_and_reactivate_autoexclusion

logger = logging.getLogger(__name__)

@shared_task
def check_fraud_patterns():
    now = timezone.now()
    recent = now - timedelta(hours=1)
    created = 0

    recent_bets = Bet.objects.filter(placed_at__gte=recent).select_related('user')
    bets_by_user: dict = {}
    for bet in recent_bets:
        bets_by_user.setdefault(bet.user_id, []).append(bet)

    for user_id, bets in bets_by_user.items():
        if len(bets) >= 10:
            total_staked = sum((b.stake for b in bets), Decimal('0'))
            if total_staked > Decimal('5000'):
                SuspiciousActivity.objects.get_or_create(
                    user_id=user_id,
                    tipo='stake_anomaly',
                    defaults={
                        'descripcion': f'{len(bets)} apuestas en 1h por {total_staked} BP',
                        'severidad': 'medium',
                    },
                )
                created += 1

    logger.info(f'Fraud check completed. Alerts created: {created}')
    return created


@shared_task
def reactivate_autoexcluded_users():
    count = check_and_reactivate_autoexclusion()
    logger.info(f'Autoexclusion reactivation check. Reactivated: {count}')
    return count


@shared_task
def check_same_ip_multiple_accounts():
    now = timezone.now()
    recent = now - timedelta(hours=24)
    created = 0

    from infrastructure.audit import AuditLog
    from infrastructure.users import UserProfile

    for profile in UserProfile.objects.select_related('user').all():
        user_bets = AuditLog.objects.filter(
            user=profile.user,
            timestamp__gte=recent,
            entity_type='Bet',
        )
        if user_bets.count() < 2:
            continue
        for log in user_bets:
            ip = log.data.get('ip')
            if not ip:
                continue
            other_users = AuditLog.objects.filter(
                timestamp__gte=recent,
                entity_type='Bet',
                data__ip=ip,
            ).exclude(user=profile.user).values_list('user_id', flat=True).distinct()
            if other_users.count() >= 2:
                for uid in other_users:
                    if uid:
                        _, created_flag = SuspiciousActivity.objects.get_or_create(
                            user_id=uid,
                            tipo='misma_ip',
                            defaults={
                                'descripcion': f'IP {ip} usada por multiples cuentas',
                                'severidad': 'high',
                            },
                        )
                        if created_flag:
                            created += 1

    logger.info(f'Same IP check completed. Alerts: {created}')
    return created


@shared_task
def check_deposit_then_cashout():
    from infrastructure.wallet import LedgerEntry
    now = timezone.now()
    recent = now - timedelta(hours=1)
    created = 0

    deposits = LedgerEntry.objects.filter(
        direction='CREDIT',
        account__type='main',
        created_at__gte=recent,
    ).select_related('account__user')

    for entry in deposits:
        if entry.account.user is None:
            continue
        cashed = Bet.objects.filter(
            user=entry.account.user,
            status='cashed_out',
            settled_at__gte=entry.created_at,
            settled_at__lte=entry.created_at + timedelta(minutes=30),
        ).exists()
        if cashed:
            _, created_flag = SuspiciousActivity.objects.get_or_create(
                user=entry.account.user,
                tipo='deposito_cashout',
                defaults={
                    'descripcion': f'Deposito de {entry.amount} BP seguido de cash-out',
                    'severidad': 'medium',
                },
            )
            if created_flag:
                created += 1

    logger.info(f'Deposit-cashout check completed. Alerts: {created}')
    return created


@shared_task
def check_identical_bet_patterns():
    now = timezone.now()
    recent = now - timedelta(minutes=10)
    created = 0

    recent_bets = Bet.objects.filter(
        placed_at__gte=recent
    ).select_related('user').prefetch_related('selections__selection')

    bets_by_pattern: dict = {}
    for bet in recent_bets:
        sel_ids = tuple(sorted(bs.selection_id for bs in bet.selections.all()))
        if not sel_ids:
            continue
        key = (bet.user_id, sel_ids, bet.stake)
        bets_by_pattern.setdefault(key, []).append(bet)

    for (user_id, sel_ids, stake), bets in bets_by_pattern.items():
        if len(bets) >= 3:
            _, created_flag = SuspiciousActivity.objects.get_or_create(
                user_id=user_id,
                tipo='patron_identico',
                defaults={
                    'descripcion': f'{len(bets)} apuestas identicas (stake={stake}) en 10 min',
                    'severidad': 'medium',
                },
            )
            if created_flag:
                created += 1

    logger.info(f'Identical patterns check completed. Alerts: {created}')
    return created


@shared_task
def check_bonus_abuse():
    from infrastructure.bonuses import UserBonus
    from django.db.models import Count
    now = timezone.now()
    recent = now - timedelta(hours=1)
    created = 0

    active_bonus_users = UserBonus.objects.filter(
        activo=True,
        rollover_completado__lt=models.F('bonus__rollover_requerido') * models.F('saldo_bono'),
    ).values_list('user_id', flat=True)

    if not active_bonus_users:
        return 0

    for user_id in active_bonus_users:
        recent_bets = Bet.objects.filter(
            user_id=user_id,
            placed_at__gte=recent,
        ).prefetch_related('selections__selection__market')

        markets_selections: dict = {}
        for bet in recent_bets:
            for bs in bet.selections.all():
                mkt_id = bs.selection.market_id
                markets_selections.setdefault(mkt_id, set()).add(bs.selection_id)

        for mkt_id, sel_ids in markets_selections.items():
            market = Bet.objects.filter(
                user_id=user_id,
                placed_at__gte=recent,
                selections__selection__market_id=mkt_id,
            ).first()
            if not market:
                continue
            mkt = market.selections.first().selection.market
            total_selections = mkt.selections.count()
            if len(sel_ids) == total_selections and total_selections >= 2:
                _, created_flag = SuspiciousActivity.objects.get_or_create(
                    user_id=user_id,
                    tipo='multiple_accounts',
                    defaults={
                        'descripcion': f'Cubrio todos los resultados del mercado "{mkt.name}" ({total_selections} selecciones). Posible abuso de bono.',
                        'severidad': 'high',
                    },
                )
                if created_flag:
                    created += 1

    logger.info(f'Bonus abuse check completed. Alerts: {created}')
    return created
