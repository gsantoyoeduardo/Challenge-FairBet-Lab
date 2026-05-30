import uuid
from decimal import Decimal

from django.db import models, transaction
from rest_framework import serializers

from infrastructure.wallet import Account, LedgerEntry


class RecargarSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=18, decimal_places=4, min_value=Decimal('0.0001'))
    reference = serializers.CharField(max_length=100, required=False, allow_blank=True)
    idempotency_key = serializers.CharField(max_length=128, required=False, allow_blank=True)


class RetirarSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=18, decimal_places=4, min_value=Decimal('0.0001'))
    reference = serializers.CharField(max_length=100, required=False, allow_blank=True)
    idempotency_key = serializers.CharField(max_length=128, required=False, allow_blank=True)

class TransferirSerializer(serializers.Serializer):
    to_username = serializers.CharField()
    amount = serializers.DecimalField(max_digits=18, decimal_places=4, min_value=Decimal('0.0001'))
    idempotency_key = serializers.CharField(max_length=128, required=False, allow_blank=True)


def get_balance(user, account_type='main'):
    account = Account.objects.get(user=user, type=account_type)
    credits = LedgerEntry.objects.filter(account=account, direction='CREDIT').aggregate(
        total=models.Sum('amount')
    )['total'] or Decimal('0.0000')
    debits = LedgerEntry.objects.filter(account=account, direction='DEBIT').aggregate(
        total=models.Sum('amount')
    )['total'] or Decimal('0.0000')
    return credits - debits


def create_double_entry(from_account, to_account, amount, description, reference=''):
    tid = uuid.uuid4()
    with transaction.atomic():
        from_acc = Account.objects.select_for_update().get(id=from_account.id)
        to_acc = Account.objects.select_for_update().get(id=to_account.id)
        LedgerEntry.objects.create(
            account=from_acc,
            amount=amount,
            direction='DEBIT',
            transaction_id=tid,
            description=description,
            reference=reference,
        )
        LedgerEntry.objects.create(
            account=to_acc,
            amount=amount,
            direction='CREDIT',
            transaction_id=tid,
            description=description,
            reference=reference,
        )
        return get_balance(to_acc.user, to_acc.type) if to_acc.user else None


def recargar(user, amount, description='Recarga de cuenta', reference=''):
    from application.responsible_gaming import validate_deposit_limits
    error = validate_deposit_limits(user, amount)
    if error:
        raise ValueError(error)
    try:
        casa = Account.objects.get(type='casa')
    except Account.DoesNotExist:
        raise ValueError('Sistema no configurado: falta cuenta casa. Ejecuta seed_demo.')
    with transaction.atomic():
        casa = Account.objects.select_for_update().get(id=casa.id)
        wallet = Account.objects.select_for_update().get(user=user, type='main')
        return create_double_entry(casa, wallet, amount, description, reference)


def retirar(user, amount, description='Retiro de cuenta', reference=''):
    try:
        wallet = Account.objects.get(user=user, type='main')
    except Account.DoesNotExist:
        raise ValueError('No tienes una cuenta principal. Contacta al administrador.')
    with transaction.atomic():
        wallet = Account.objects.select_for_update().get(id=wallet.id)
        if get_balance(user, 'main') < amount:
            raise ValueError('Saldo insuficiente')
        try:
            casa = Account.objects.select_for_update().get(type='casa')
        except Account.DoesNotExist:
            raise ValueError('Sistema no configurado: falta cuenta casa. Ejecuta seed_demo.')
        return create_double_entry(wallet, casa, amount, description, reference)


def transferir(from_user, to_user, amount, description='Transferencia', reference=''):
    with transaction.atomic():
        wallet_from = Account.objects.get(user=from_user, type='main')
        wallet_to = Account.objects.get(user=to_user, type='main')
        if get_balance(from_user, 'main') < amount:
            raise ValueError('Saldo insuficiente')
        return create_double_entry(wallet_from, wallet_to, amount, description, reference)
