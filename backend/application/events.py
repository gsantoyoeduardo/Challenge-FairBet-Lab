from rest_framework import serializers
from infrastructure.events import Sport, Event, Market, Selection


class SportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sport
        fields = ('id', 'name', 'slug')


class SelectionSerializer(serializers.ModelSerializer):
    market_id = serializers.IntegerField(source='market.id', read_only=True)
    market_type = serializers.CharField(source='market.type', read_only=True)

    class Meta:
        model = Selection
        fields = ('id', 'name', 'odds', 'is_winner', 'market_id', 'market_type')


class MarketSerializer(serializers.ModelSerializer):
    selections = SelectionSerializer(many=True, read_only=True)

    class Meta:
        model = Market
        fields = ('id', 'type', 'name', 'is_live', 'selections')


class EventListSerializer(serializers.ModelSerializer):
    sport_name = serializers.CharField(source='sport.name', read_only=True)
    market_count = serializers.SerializerMethodField()
    main_odds = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = ('id', 'sport', 'sport_name', 'team_home', 'team_away',
                  'start_time', 'status', 'market_count', 'main_odds')

    def get_market_count(self, obj):
        return obj.markets.count()

    def get_main_odds(self, obj):
        types_by_sport = {
            'football': '1X2',
            'tennis': 'TENNIS_WINNER',
            'basketball': 'BASKET_ML',
            'volleyball': '1X2',
        }
        market_type = types_by_sport.get(obj.sport.slug, '1X2')
        mkt = obj.markets.filter(type=market_type).first()
        if mkt:
            return [{'id': s.id, 'name': s.name, 'odds': str(s.odds),
                     'market_id': mkt.id, 'market_type': mkt.type}
                    for s in mkt.selections.all()]
        return []


class EventDetailSerializer(serializers.ModelSerializer):
    sport = SportSerializer(read_only=True)
    markets = MarketSerializer(many=True, read_only=True)

    class Meta:
        model = Event
        fields = ('id', 'sport', 'team_home', 'team_away', 'start_time',
                  'status', 'created_at', 'markets')
