from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from users.models import UserProfile
from wallet.models import Account
from application.wallet import recargar
from decimal import Decimal

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed usuarios demo, cuenta casa, wallets inicializadas y bonos'

    def handle(self, *args, **kwargs):
        casa_user, _ = User.objects.get_or_create(
            username='sistema_casa',
            defaults={'email': 'casa@fairbet.internal'},
        )
        if not casa_user.has_usable_password():
            casa_user.set_password('sistema_casa_internal_2024')
            casa_user.save()
        Account.objects.get_or_create(user=casa_user, type='casa')
        Account.objects.get_or_create(user=casa_user, type='apuestas_pendientes')
        self.stdout.write(self.style.SUCCESS('Cuentas casa y apuestas_pendientes creadas'))

        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@fairbet.com',
                'is_staff': True,
                'is_superuser': True,
            },
        )
        if created or not admin_user.has_usable_password():
            admin_user.set_password('admin1234')
            admin_user.is_staff = True
            admin_user.is_superuser = True
            admin_user.save()
        Account.objects.get_or_create(user=admin_user, type='main')
        Account.objects.get_or_create(user=admin_user, type='bonus')
        UserProfile.objects.get_or_create(
            user=admin_user,
            defaults={
                'dni': '00000001',
                'fecha_nacimiento': '1990-01-01',
                'estado_cuenta': 'verificado',
            },
        )
        self.stdout.write(self.style.SUCCESS('Superusuario admin creado con cuentas wallet y perfil verificado'))

        demo_users = [
            {
                'username': 'demo1',
                'email': 'demo1@fairbet.com',
                'password': 'demo1234',
                'dni': '12345678',
                'balance': Decimal('1000.0000'),
            },
            {
                'username': 'demo2',
                'email': 'demo2@fairbet.com',
                'password': 'demo1234',
                'dni': '87654321',
                'balance': Decimal('500.0000'),
            },
        ]

        for data in demo_users:
            user, created = User.objects.get_or_create(
                username=data['username'],
                defaults={'email': data['email']},
            )
            if created:
                user.set_password(data['password'])
                user.save()
                UserProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        'dni': data['dni'],
                        'fecha_nacimiento': '1990-01-01',
                        'estado_cuenta': 'verificado',
                    },
                )
                Account.objects.get_or_create(user=user, type='main')
                Account.objects.get_or_create(user=user, type='bonus')
                recargar(user, data['balance'], f'Saldo inicial para {data["username"]}')
                self.stdout.write(self.style.SUCCESS(
                    f'Creado {data["username"]} (verificado) con balance {data["balance"]}'
                ))
            else:
                Account.objects.get_or_create(user=user, type='bonus')
                self.stdout.write(self.style.WARNING(f'{data["username"]} ya existe'))

        from infrastructure.bonuses import Bonus
        bono_bienvenida, _ = Bonus.objects.get_or_create(
            tipo='bienvenida',
            nombre='Bono de Bienvenida 100%',
            defaults={
                'descripcion': '100% de tu primer deposito hasta 100 BP. Rollover x5.',
                'porcentaje': 100,
                'monto_max': Decimal('100.0000'),
                'rollover_requerido': 5,
            },
        )
        bono_recarga, _ = Bonus.objects.get_or_create(
            tipo='recarga',
            nombre='Bono de Recarga 50%',
            defaults={
                'descripcion': '50% extra en cada recarga hasta 50 BP. Rollover x3.',
                'porcentaje': 50,
                'monto_max': Decimal('50.0000'),
                'rollover_requerido': 3,
            },
        )
        self.stdout.write(self.style.SUCCESS(
            f'Bonos creados: {bono_bienvenida.nombre}, {bono_recarga.nombre}'
        ))

        from django.core.management import call_command
        self.stdout.write('Sembrando eventos deportivos...')
        call_command('seed_massive_events')

        self.stdout.write(self.style.SUCCESS('Seed completo'))
