"""
Controladores para la API de `bonuses`.

Función:
- Listar bonos disponibles, reclamar bonos y consultar los bonos del
    usuario con estado de rollover.

Relaciones:
- Delegan la lógica a `application.bonuses` y usan `infrastructure.bonuses`.
"""

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiExample

from application.bonuses import (
    BonusSerializer, UserBonusSerializer, ApplyBonusSerializer,
    get_available_bonuses, apply_bonus, get_user_bonuses,
)
from infrastructure.bonuses import Bonus


class BonusAvailableView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = BonusSerializer

    @extend_schema(
        summary='Listar bonos disponibles',
        description='Devuelve todos los bonos que el usuario puede reclamar.',
        responses={200: BonusSerializer(many=True)},
    )
    def get(self, request):
        bonuses = get_available_bonuses(request.user)
        return Response(BonusSerializer(bonuses, many=True).data)


class ApplyBonusView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ApplyBonusSerializer

    @extend_schema(
        summary='Reclamar bono',
        description='Aplica un bono y acredita el saldo en la cuenta de bonos.',
        request=ApplyBonusSerializer,
        responses={201: None},
        examples=[
            OpenApiExample('Bienvenida', value={'bonus_id': 1}),
        ],
    )
    def post(self, request):
        serializer = ApplyBonusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            result = apply_bonus(
                request.user,
                serializer.validated_data['bonus_id'],
                serializer.validated_data.get('deposit_amount', 0),
            )
            return Response(result, status=status.HTTP_201_CREATED)
        except Bonus.DoesNotExist:
            return Response({'error': 'Bono no encontrado'}, status=status.HTTP_404_NOT_FOUND)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class MyBonusesView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserBonusSerializer

    @extend_schema(
        summary='Mis bonos',
        description='Devuelve el estado de los bonos del usuario y el progreso de rollover.',
        responses={200: UserBonusSerializer(many=True)},
    )
    def get(self, request):
        user_bonuses = get_user_bonuses(request.user)
        return Response(UserBonusSerializer(user_bonuses, many=True).data)
