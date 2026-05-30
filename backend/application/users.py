"""
Módulo `application.users` — Casos de uso relacionados con usuarios.

Función:
- Provee serializadores y lógica de registro, creación de perfil y cuenta
    wallet inicial. Orquesta creación atómica de `User`, `UserProfile` y
    `Account`.

Relaciones:
- Usado por `controllers/users.py` para endpoints de registro/login/me.
- Interactúa con `infrastructure.users.UserProfile` y `infrastructure.wallet.Account`.
"""

from django.contrib.auth import get_user_model
from rest_framework import serializers
from django.db import transaction

from infrastructure.users import UserProfile
from infrastructure.wallet import Account
from domain.users import validate_dni

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    dni = serializers.CharField(max_length=8, min_length=8)
    fecha_nacimiento = serializers.DateField()
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'dni', 'fecha_nacimiento')

    def validate_dni(self, value):
        if not validate_dni(value):
            raise serializers.ValidationError('DNI peruano invalido')
        if UserProfile.objects.filter(dni=value).exists():
            raise serializers.ValidationError('DNI ya registrado')
        return value

    def validate_fecha_nacimiento(self, value):
        from datetime import date
        today = date.today()
        age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
        if age < 18:
            raise serializers.ValidationError('Debes ser mayor de 18 años para registrarte')
        return value

    @transaction.atomic
    def create(self, validated_data):
        dni = validated_data.pop('dni')
        fecha_nacimiento = validated_data.pop('fecha_nacimiento')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
        )
        UserProfile.objects.create(
            user=user,
            dni=dni,
            fecha_nacimiento=fecha_nacimiento,
        )
        Account.objects.create(user=user, type='main')
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class TokenResponseSerializer(serializers.Serializer):
    access = serializers.CharField(help_text='Token de acceso (usar este en Swagger Authorize)')
    refresh = serializers.CharField(help_text='Token de refresco')
    user = serializers.DictField()


class UserSerializer(serializers.ModelSerializer):
    dni = serializers.CharField(source='profile.dni', read_only=True)
    estado_cuenta = serializers.CharField(source='profile.estado_cuenta', read_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'dni', 'estado_cuenta', 'date_joined', 'is_staff')
