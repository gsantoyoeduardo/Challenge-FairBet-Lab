"""
Módulo `application.responsible_gaming` — Casos de uso de juego responsable.

Función:
- Gestiona límites de depósito, cambios de límite, autoexclusión y
  validaciones relacionadas con el comportamiento de apuestas del usuario.

Relaciones:
- Usado por `application.betting` para validar apuestas antes de crear
  transacciones.
- Persiste datos en `infrastructure.responsible_gaming`.
"""

from decimal import Decimal
import logging
from django.utils import timezone
from rest_framework import serializers

from infrastructure.responsible_gaming import DepositLimits, LimitChangeRequest, AutoExclusion
from domain.responsible_gaming import (
    AUTOEXCLUSION_PERIODS, COOLDOWN_HOURS,
    has_cooldown_expired, is_limit_increase, validate_limit_value,
)
from domain.users import validate_profile_transition


class DepositLimitsSerializer(serializers.ModelSerializer):
    class Meta:
        model = DepositLimits
        fields = ('limite_diario', 'limite_semanal', 'limite_mensual',
                  'limite_apuesta_max', 'limite_perdida_diaria')

    def validate_limite_diario(self, value):
        # Valida que el limite diario no sea negativo.
        err = validate_limit_value(value)
        if err:
            raise serializers.ValidationError(err)
        return value

    def validate_limite_semanal(self, value):
        # Valida que el limite semanal no sea negativo.
        err = validate_limit_value(value)
        if err:
            raise serializers.ValidationError(err)
        return value

    def validate_limite_mensual(self, value):
        # Valida que el limite mensual no sea negativo.
        err = validate_limit_value(value)
        if err:
            raise serializers.ValidationError(err)
        return value

    def validate_limite_apuesta_max(self, value):
        # Valida que el limite por apuesta no sea negativo.
        err = validate_limit_value(value)
        if err:
            raise serializers.ValidationError(err)
        return value

    def validate_limite_perdida_diaria(self, value):
        # Valida que el limite de perdida diaria no sea negativo.
        err = validate_limit_value(value)
        if err:
            raise serializers.ValidationError(err)
        return value


class AutoExclusionSerializer(serializers.Serializer):
    periodo = serializers.ChoiceField(
        choices=list(AUTOEXCLUSION_PERIODS.keys()),
        help_text='7d, 30d, 90d, indefinida',
    )
    motivo = serializers.CharField(required=False, allow_blank=True, default='')


class LimitChangeRequestSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = LimitChangeRequest
        fields = ('id', 'username', 'tipo_limite', 'valor_anterior',
                  'valor_solicitado', 'estado', 'created_at', 'approved_at')
        read_only_fields = ('estado', 'created_at', 'approved_at')


def get_or_create_limits(user) -> DepositLimits:
    # Recupera los limites del usuario o crea un objeto nuevo si no existe.
    limits, _ = DepositLimits.objects.get_or_create(user=user)
    return limits


def apply_limit_change(user, tipo_limite: str, valor: Decimal) -> dict:
    # Obtiene los limites actuales del usuario.
    limits = get_or_create_limits(user)
    # Lee el valor anterior del limite solicitado.
    valor_anterior = getattr(limits, tipo_limite, Decimal('0'))

    # Si el nuevo valor es un aumento, valida cooldown de 24h.
    if is_limit_increase(valor_anterior, valor):
        last_change = LimitChangeRequest.objects.filter(
            user=user, tipo_limite=tipo_limite, estado='approved',
        ).order_by('-created_at').first()
        if not has_cooldown_expired(last_change):
            raise ValueError(
                f'Para subir el limite debes esperar {COOLDOWN_HOURS}h desde el ultimo cambio.'
            )

    # Registra la solicitud de cambio de limite como aprobada.
    change = LimitChangeRequest.objects.create(
        user=user,
        tipo_limite=tipo_limite,
        valor_anterior=valor_anterior,
        valor_solicitado=valor,
        estado='approved',
        approved_at=timezone.now(),
    )

    # Actualiza el modelo de limites del usuario.
    setattr(limits, tipo_limite, valor)
    limits.save()

    return {
        'tipo_limite': tipo_limite,
        'valor_anterior': str(valor_anterior),
        'valor_nuevo': str(valor),
        'created_at': change.created_at.isoformat(),
    }


def create_autoexclusion(user, periodo: str, motivo: str = '') -> AutoExclusion:
    # Calcula la fecha final de autoexclusión según el periodo seleccionado.
    from datetime import timedelta
    fecha_fin = None
    if periodo != 'indefinida':
        delta = AUTOEXCLUSION_PERIODS[periodo]
        fecha_fin = timezone.now() + delta

    # Crea o reusa el registro de autoexclusión del usuario.
    auto_exclusion, _ = AutoExclusion.objects.get_or_create(
        user=user,
        defaults={'fecha_inicio': timezone.now(), 'fecha_fin': fecha_fin, 'motivo': motivo, 'activa': True},
    )
    if not auto_exclusion.activa:
        # Si existía pero estaba desactivado, lo reactiva.
        auto_exclusion.fecha_inicio = timezone.now()
        auto_exclusion.fecha_fin = fecha_fin
        auto_exclusion.motivo = motivo
        auto_exclusion.activa = True
        auto_exclusion.save()

    # Cambia el estado del perfil del usuario a autoexcluido.
    profile = user.profile
    error = validate_profile_transition(profile, 'autoexcluido')
    if error:
        raise ValueError(error)
    profile.estado_cuenta = 'autoexcluido'
    profile.save()

    return auto_exclusion


def check_and_reactivate_autoexclusion():
    # Revisa autoexclusiones activas que ya vencieron y las desactiva.
    from django.utils import timezone
    logger = logging.getLogger(__name__)
    now = timezone.now()
    expired = AutoExclusion.objects.filter(activa=True, fecha_fin__isnull=False, fecha_fin__lte=now)
    count = 0
    for ae in expired:
        ae.activa = False
        ae.save()
        profile = ae.user.profile
        if profile.estado_cuenta == 'autoexcluido':
            error = validate_profile_transition(profile, 'verificado')
            if error:
                logger.error(f'Transicion invalida para {profile.user.username}: {error}')
                continue
            profile.estado_cuenta = 'verificado'
            profile.save()
        count += 1
    return count


def validate_user_limits(user, stake: Decimal) -> str | None:
    # Valida los limites de apuesta del usuario antes de permitir una apuesta.
    from decimal import Decimal
    from django.utils import timezone
    from infrastructure.betting import Bet
    from application.wallet import get_balance

    try:
        limits = user.deposit_limits
    except DepositLimits.DoesNotExist:
        # Si no tiene limites configurados, no se impone restriccion.
        return None

    if limits.limite_apuesta_max and limits.limite_apuesta_max > Decimal('0'):
        if stake > limits.limite_apuesta_max:
            return f'La apuesta excede tu limite maximo de {limits.limite_apuesta_max} BP'

    if limits.limite_perdida_diaria and limits.limite_perdida_diaria > Decimal('0'):
        hoy = timezone.now().date()
        bets_today = Bet.objects.filter(
            user=user,
            placed_at__date=hoy,
            status__in=('lost', 'cashed_out'),
        )
        perdido_hoy = sum((b.stake for b in bets_today), Decimal('0'))
        if perdido_hoy + stake > limits.limite_perdida_diaria:
            return f'Con esta apuesta excederias tu limite de perdida diaria de {limits.limite_perdida_diaria} BP'

    return None


def validate_deposit_limits(user, amount: Decimal) -> str | None:
    from datetime import timedelta
    from django.db import models
    from infrastructure.wallet import LedgerEntry

    try:
        limits = user.deposit_limits
    except DepositLimits.DoesNotExist:
        return None

    now = timezone.now()

    if limits.limite_diario and limits.limite_diario > Decimal('0'):
        hoy = now.date()
        deposited_today = LedgerEntry.objects.filter(
            account__user=user, account__type='main',
            direction='CREDIT', created_at__date=hoy,
            description__contains='Recarga',
        ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0')
        if deposited_today + amount > limits.limite_diario:
            return f'Excede el limite diario de deposito ({limits.limite_diario} BP). Llevas {deposited_today} BP hoy.'

    if limits.limite_semanal and limits.limite_semanal > Decimal('0'):
        inicio_semana = now.date() - timedelta(days=now.weekday())
        deposited_week = LedgerEntry.objects.filter(
            account__user=user, account__type='main',
            direction='CREDIT', created_at__date__gte=inicio_semana,
            description__contains='Recarga',
        ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0')
        if deposited_week + amount > limits.limite_semanal:
            return f'Excede el limite semanal de deposito ({limits.limite_semanal} BP). Llevas {deposited_week} BP esta semana.'

    if limits.limite_mensual and limits.limite_mensual > Decimal('0'):
        inicio_mes = now.replace(day=1).date()
        deposited_month = LedgerEntry.objects.filter(
            account__user=user, account__type='main',
            direction='CREDIT', created_at__date__gte=inicio_mes,
            description__contains='Recarga',
        ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0')
        if deposited_month + amount > limits.limite_mensual:
            return f'Excede el limite mensual de deposito ({limits.limite_mensual} BP). Llevas {deposited_month} BP este mes.'

    return None
