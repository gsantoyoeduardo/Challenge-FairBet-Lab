import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from channels.db import database_sync_to_async


class EventOddsConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.event_id = self.scope['url_route']['kwargs']['event_id']
        self.group_name = f'event_{self.event_id}'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        odds_data = await self.get_odds_data()
        await self.send(text_data=json.dumps(odds_data))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def odds_update(self, event):
        await self.send(text_data=json.dumps(event['data']))

    async def recotizacion(self, event):
        await self.send(text_data=json.dumps({
            'type': 'recotizacion',
            'selection_id': event['selection_id'],
            'old_odds': str(event['old_odds']),
            'new_odds': str(event['new_odds']),
        }))

    async def market_suspension(self, event):
        await self.send(text_data=json.dumps({
            'type': 'market_suspension',
            'reason': event.get('reason', 'evento_critico'),
            'duration': event.get('duration', 30),
        }))

    @database_sync_to_async
    def get_odds_data(self):
        from infrastructure.events import Event
        try:
            event = Event.objects.prefetch_related(
                'markets__selections'
            ).get(id=self.event_id)
        except Event.DoesNotExist:
            return {'error': 'Evento no encontrado'}

        markets = []
        for market in event.markets.all():
            selections = [
                {'id': s.id, 'name': s.name, 'odds': str(s.odds)}
                for s in market.selections.all()
            ]
            markets.append({
                'id': market.id,
                'type': market.type,
                'name': market.name,
                'selections': selections,
            })
        return {
            'type': 'odds_data',
            'event_id': event.id,
            'status': event.status,
            'markets': markets,
        }


def suspender_mercado_por_evento_critico(event_id: int, segundos: int = 30):
    from django.utils import timezone
    from infrastructure.events import Market
    now = timezone.now()
    until = now + timezone.timedelta(seconds=segundos)
    Market.objects.filter(event_id=event_id).update(suspended_until=until)
    channel_layer = get_channel_layer()
    group_name = f'event_{event_id}'
    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            'type': 'market_suspension',
            'reason': 'evento_critico',
            'duration': segundos,
        },
    )


def enviar_actualizacion_odds(event_id: int, selection_id: int, old_odds, new_odds):
    channel_layer = get_channel_layer()
    group_name = f'event_{event_id}'
    payload = {
        'type': 'odds_update',
        'data': {
            'type': 'odds_update',
            'event_id': event_id,
            'selection_id': selection_id,
            'old_odds': str(old_odds),
            'new_odds': str(new_odds),
        },
    }
    async_to_sync(channel_layer.group_send)(group_name, payload)
