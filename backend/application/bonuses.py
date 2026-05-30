"""
Módulo `application.bonuses` — Casos de uso del sistema de bonos.

Función:
- Gestiona aplicación de bonos, creación de `UserBonus`, expiraciones y la
    lógica de contribución al rollover cuando el usuario apuesta.

Relaciones:
- Invocado desde `application.betting` tras crear apuestas para procesar
    contribuciones al rollover.
- Usa `infrastructure.bonuses` y `infrastructure.wallet` para mover fondos.
"""

from decimal import Decimal
from datetime import timedelta
from django.db import models
from django.utils import timezone
from rest_framework import serializers

from infrastructure.bonuses import Bonus, UserBonus
from infrastructure.wallet import Account
from domain.bonuses import (
    validate_bonus_application, calculate_bonus_amount, validate_rollover_odds,
    BONUS_EXPIRATION_DAYS,
)
from application.wallet import get_balance, create_double_entry


class BonusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bonus
        fields = ('id', 'tipo', 'nombre', 'descripcion', 'porcentaje',
                  'monto_max', 'rollover_requerido', 'activo')


class UserBonusSerializer(serializers.ModelSerializer):
    bonus = BonusSerializer(read_only=True)
    rollover_restante = serializers.DecimalField(max_digits=18, decimal_places=4, read_only=True)
    rollover_porcentaje = serializers.IntegerField(read_only=True)
    rollover_completo = serializers.BooleanField(read_only=True)

    class Meta:
        model = UserBonus
        fields = ('id', 'bonus', 'saldo_bono', 'rollover_completado',
                  'rollover_restante', 'rollover_porcentaje', 'rollover_completo',
                  'fecha_otorgado', 'fecha_expiracion', 'activo')


class ApplyBonusSerializer(serializers.Serializer):
    bonus_id = serializers.IntegerField()
    deposit_amount = serializers.DecimalField(
        max_digits=18, decimal_places=4,
        required=False, default=0,
        help_text='Monto del deposito que activa el bono',
    )


def get_available_bonuses(user):
    return Bonus.objects.filter(activo=True)


def apply_bonus(user, bonus_id: int, deposit_amount: Decimal = Decimal('0')) -> dict:
    bonus = Bonus.objects.get(id=bonus_id, activo=True)

    error = validate_bonus_application(user, bonus)
    if error:
        raise ValueError(error)

    monto_bono = calculate_bonus_amount(deposit_amount, bonus) if deposit_amount > 0 else bonus.monto_max

    bonus_account, _ = Account.objects.get_or_create(
        user=user,
        type=Account.AccountType.BONUS,
        defaults={'type': Account.AccountType.BONUS},
    )

    casa_account = Account.objects.get(type=Account.AccountType.CASA)

    create_double_entry(
        from_account=casa_account,
        to_account=bonus_account,
        amount=monto_bono,
        description=f'Bono {bonus.nombre}',
        reference=f'bonus-{bonus.id}-{user.id}',
    )

    user_bonus = UserBonus.objects.create(
        user=user,
        bonus=bonus,
        saldo_bono=monto_bono,
        fecha_expiracion=timezone.now() + timedelta(days=BONUS_EXPIRATION_DAYS),
    )

    return {
        'user_bonus_id': user_bonus.id,
        'bonus_name': bonus.nombre,
        'monto_bono': str(monto_bono),
        'rollover_requerido': bonus.rollover_requerido,
        'mensaje': f'Bono {bonus.nombre} aplicado: {monto_bono} BP',
    }


def get_user_bonuses(user):
    return UserBonus.objects.filter(user=user).select_related('bonus')


def process_rollover_contribution(user, stake: Decimal, odds: Decimal):
    if not validate_rollover_odds(odds):
        return 0

    active_bonuses = UserBonus.objects.filter(
        user=user,
        activo=True,
        rollover_completado__lt=models.F('bonus__rollover_requerido') * models.F('saldo_bono'),
    ).select_related('bonus')

    total_contributed = Decimal('0')
    for ub in active_bonuses:
        requerido = ub.bonus.rollover_requerido * ub.saldo_bono
        restante = requerido - ub.rollover_completado
        if restante <= 0:
            continue
        contribucion = min(stake, restante)
        ub.rollover_completado += contribucion
        ub.save(update_fields=['rollover_completado'])
        total_contributed += contribucion

        if ub.rollover_completado >= requerido:
            bonus_account = Account.objects.get(user=user, type=Account.AccountType.BONUS)
            main_account = Account.objects.get(user=user, type=Account.AccountType.MAIN)
            create_double_entry(
                from_account=bonus_account,
                to_account=main_account,
                amount=ub.saldo_bono,
                description=f'Rollover completado: {ub.bonus.nombre}',
                reference=f'rollover-{ub.id}',
            )
            ub.activo = False
            ub.save(update_fields=['activo'])

    return total_contributed
