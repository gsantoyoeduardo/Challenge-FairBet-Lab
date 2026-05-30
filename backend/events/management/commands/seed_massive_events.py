from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import random

from infrastructure.events import Sport, Event, Market, Selection
from domain.events import (
    generate_1X2, generate_double_chance, generate_draw_no_bet,
    generate_ou_goals, generate_btts, generate_btts_ou25,
    generate_ht_ft, generate_correct_score, generate_handicap,
    generate_tennis_winner, generate_tennis_handicap, generate_set_betting,
    generate_basket_spread, SET_BETS, rand_odds,
    calculate_odds_with_margin, MARGIN_FACTOR,
)

random.seed(42)

SPORTS = {
    'football': {'name': 'Futbol', 'leagues': {
        'liga1': 'Liga 1 Peru', 'premier': 'Premier League', 'laliga': 'La Liga',
        'champions': 'Champions League', 'libertadores': 'Copa Libertadores',
        'seriea': 'Serie A', 'bundesliga': 'Bundesliga', 'ligue1': 'Ligue 1',
    }},
    'tennis': {'name': 'Tenis', 'leagues': {'atp': 'ATP', 'wta': 'WTA'}},
    'basketball': {'name': 'Basketball', 'leagues': {'nba': 'NBA', 'euroliga': 'EuroLeague'}},
    'volleyball': {'name': 'Voleibol', 'leagues': {'lnv': 'Liga Nacional', 'world': 'Mundial'}},
}

FOOTBALL_TEAMS = {
    'liga1': ['Alianza Lima', 'Universitario', 'Sporting Cristal', 'Cienciano',
              'Melgar', 'Cusco FC', 'Sport Boys', 'Municipal', 'UTC', 'ADT',
              'Cesar Vallejo', 'Carlos Mannucci', 'Alianza Atletico', 'Binacional',
              'Sport Huancayo', 'Cantolao', 'Union Comercio', 'Grau'],
    'premier': ['Manchester City', 'Liverpool', 'Arsenal', 'Chelsea', 'Tottenham',
                'Manchester United', 'Newcastle', 'Aston Villa', 'Brighton', 'West Ham',
                'Crystal Palace', 'Fulham', 'Wolves', 'Everton', 'Brentford',
                'Nottingham Forest', 'Bournemouth', 'Luton Town'],
    'laliga': ['Real Madrid', 'Barcelona', 'Atletico Madrid', 'Sevilla', 'Real Sociedad',
               'Villarreal', 'Betis', 'Athletic Club', 'Valencia', 'Osasuna',
               'Getafe', 'Celta Vigo', 'Mallorca', 'Alaves', 'Las Palmas',
               'Rayo Vallecano', 'Cadiz', 'Granada'],
    'champions': ['Bayern Munich', 'PSG', 'Inter Milan', 'AC Milan', 'Napoli',
                  'Borussia Dortmund', 'RB Leipzig', 'Porto', 'Benfica', 'Ajax',
                  'Galatasaray', 'Celtic', 'Shakhtar Donetsk', 'FC Copenhagen',
                  'Red Star Belgrade', 'Young Boys', 'Antwerp', 'Real Sociedad'],
    'libertadores': ['Flamengo', 'Palmeiras', 'River Plate', 'Boca Juniors', 'Santos',
                     'Fluminense', 'Sao Paulo', 'Racing', 'Independiente', 'Nacional',
                     'Penarol', 'Olimpia', 'Cerro Porteno', 'Bolivar', 'LDU Quito',
                     'Barcelona SC', 'Junior', 'Atletico Mineiro'],
    'seriea': ['Juventus', 'Inter Milan', 'AC Milan', 'Napoli', 'Roma',
               'Lazio', 'Atalanta', 'Fiorentina', 'Torino', 'Bologna',
               'Udinese', 'Sassuolo', 'Monza', 'Genoa', 'Lecce', 'Empoli', 'Salernitana', 'Verona'],
    'bundesliga': ['Bayern Munich', 'Borussia Dortmund', 'RB Leipzig', 'Bayer Leverkusen',
                   'Wolfsburg', 'Eintracht Frankfurt', 'Freiburg', 'Hoffenheim',
                   'Borussia Monchengladbach', 'Stuttgart', 'Werder Bremen', 'Augsburg',
                   'Mainz', 'Union Berlin', 'Bochum', 'Heidenheim', 'Darmstadt', 'Koln'],
    'ligue1': ['PSG', 'Marseille', 'Lens', 'Lyon', 'Monaco', 'Rennes',
               'Lille', 'Nice', 'Toulouse', 'Montpellier', 'Strasbourg',
               'Reims', 'Lorient', 'Brest', 'Nantes', 'Clermont', 'Le Havre', 'Metz'],
}

TENNIS_PLAYERS = {
    'atp': ['Djokovic', 'Alcaraz', 'Sinner', 'Medvedev', 'Rublev',
            'Zverev', 'Tsitsipas', 'Rune', 'Ruud', 'Fritz',
            'Tiafoe', 'Shelton', 'Norrie', 'Paul', 'Khachanov'],
    'wta': ['Swiatek', 'Sabalenka', 'Gauff', 'Rybakina', 'Pegula',
            'Jabeur', 'Vondrousova', 'Muchova', 'Sakkari', 'Keys',
            'Bencic', 'Haddad Maia', 'Ostapenko', 'Kvitova', 'Garcia'],
}

BASKETBALL_TEAMS = {
    'nba': ['Lakers', 'Celtics', 'Warriors', 'Bucks', 'Nuggets',
            'Heat', 'Suns', '76ers', 'Mavericks', 'Knicks',
            'Cavaliers', 'Grizzlies', 'Kings', 'Clippers', 'Thunder',
            'Timberwolves', 'Pelicans', 'Hawks'],
    'euroliga': ['Real Madrid', 'Barcelona', 'Fenerbahce', 'Olympiacos', 'Panathinaikos',
                 'Anadolu Efes', 'CSKA Moscow', 'Zalgiris', 'Maccabi Tel Aviv', 'Bayern Munich',
                 'Monaco', 'Virtus Bologna', 'Partizan', 'Valencia', 'Baskonia',
                 'Crvena Zvezda', 'Alba Berlin', 'ASVEL'],
}

VOLLEYBALL_TEAMS = {
    'lnv': ['Regatas Lima', 'Alianza Lima Voley', 'Circolo Sportivo Italiano', 'Universidad San Martin',
            'Golazo', 'Tupac Amaru', 'Deportivo Wanka', 'Latino Amisa',
            'Geminis', 'Sparta', 'Circolo', 'Rebaza Acosta'],
    'world': ['Brasil', 'Polonia', 'USA', 'Italia', 'Francia', 'Japon',
              'Argentina', 'Eslovenia', 'Rusia', 'Serbia', 'Iran', 'Canada'],
}


class Command(BaseCommand):
    help = 'Seed masivo de eventos deportivos con todos los mercados'

    def handle(self, *args, **kwargs):
        total = 0
        for sport_key, sport_data in SPORTS.items():
            sport, _ = Sport.objects.get_or_create(slug=sport_key, defaults={'name': sport_data['name']})
            self.stdout.write(f'Creando eventos de {sport.name}...')

            for league_key, league_name in sport_data['leagues'].items():
                if sport_key == 'football':
                    teams = FOOTBALL_TEAMS.get(league_key, [])
                    base_time = timezone.now() + timedelta(hours=random.randint(1, 48))
                    for day in range(min(len(teams) // 2, 9)):
                        t1 = teams[day * 2 % len(teams)]
                        t2 = teams[(day * 2 + 1) % len(teams)]
                        if t1 == t2:
                            t2 = teams[(day * 2 + 3) % len(teams)]
                        start = base_time + timedelta(days=day)
                        status_val = random.choice(['programado', 'programado', 'programado', 'programado', 'en_vivo'])
                        ev, created = Event.objects.get_or_create(
                            sport=sport, team_home=t1, team_away=t2,
                            defaults={'start_time': start, 'status': status_val},
                        )
                        if created:
                            create_football_markets(ev)
                            total += 1

                elif sport_key == 'tennis':
                    players = TENNIS_PLAYERS.get(league_key, [])
                    base_time = timezone.now() + timedelta(hours=random.randint(1, 72))
                    for i in range(min(40, len(players) * 3)):
                        p1 = players[i % len(players)]
                        p2 = players[(i + random.randint(1, len(players) - 1)) % len(players)]
                        if p1 == p2:
                            continue
                        start = base_time + timedelta(hours=i * 2)
                        status_val = random.choice(['programado', 'programado', 'programado', 'en_vivo'])
                        ev, created = Event.objects.get_or_create(
                            sport=sport, team_home=p1, team_away=p2,
                            defaults={'start_time': start, 'status': status_val},
                        )
                        if created:
                            create_tennis_markets(ev)
                            total += 1

                elif sport_key == 'basketball':
                    teams = BASKETBALL_TEAMS.get(league_key, [])
                    base_time = timezone.now() + timedelta(hours=random.randint(1, 72))
                    for day in range(min(len(teams) // 2, 9)):
                        t1 = teams[day * 2 % len(teams)]
                        t2 = teams[(day * 2 + 1) % len(teams)]
                        start = base_time + timedelta(hours=day * 3)
                        status_val = random.choice(['programado', 'programado', 'en_vivo'])
                        ev, created = Event.objects.get_or_create(
                            sport=sport, team_home=t1, team_away=t2,
                            defaults={'start_time': start, 'status': status_val},
                        )
                        if created:
                            create_basketball_markets(ev)
                            total += 1

                elif sport_key == 'volleyball':
                    teams = VOLLEYBALL_TEAMS.get(league_key, [])
                    base_time = timezone.now() + timedelta(hours=random.randint(1, 72))
                    for day in range(min(len(teams) // 2, 6)):
                        t1 = teams[day * 2 % len(teams)]
                        t2 = teams[(day * 2 + 1) % len(teams)]
                        start = base_time + timedelta(hours=day * 4)
                        status_val = random.choice(['programado', 'programado', 'en_vivo'])
                        ev, created = Event.objects.get_or_create(
                            sport=sport, team_home=t1, team_away=t2,
                            defaults={'start_time': start, 'status': status_val},
                        )
                        if created:
                            create_simple_markets(ev)
                            total += 1

        self.stdout.write(self.style.SUCCESS(f'Total eventos creados: {total}'))


def mk(event, mkt_type, name, selections_list):
    """Helper: create Market + Selections"""
    m = Market.objects.create(event=event, type=mkt_type, name=name)
    for sel_name, sel_odds in selections_list:
        Selection.objects.create(market=m, name=sel_name, odds=sel_odds)


def create_football_markets(event):
    from django.conf import settings
    margin = Decimal(settings.EVENTS_MARGIN_FACTOR)
    raw_1X2 = generate_1X2()
    o1, oX, o2 = calculate_odds_with_margin(raw_1X2, margin) if margin > 0 else raw_1X2
    mk(event, '1X2', 'Ganador de Partido', [('Local', o1), ('Empate', oX), ('Visitante', o2)])

    dc = generate_double_chance(o1, oX, o2)
    mk(event, 'DOUBLE_CHANCE', 'Doble Oportunidad', [('1X', dc[0]), ('12', dc[1]), ('X2', dc[2])])

    dnb = generate_draw_no_bet(o1, oX)
    mk(event, 'DRAW_NO_BET', 'Draw No Bet', [('Local', dnb[0]), ('Visitante', dnb[1])])

    for ou_type, ou_name, low in [('OU_05', 'Over/Under 0.5', 1.10), ('OU_15', 'Over/Under 1.5', 1.20),
                                   ('OU_25', 'Over/Under 2.5', 1.60), ('OU_35', 'Over/Under 3.5', 1.60),
                                   ('OU_45', 'Over/Under 4.5', 1.60)]:
        ov, un = generate_ou_goals(low, low + 0.70)
        mk(event, ou_type, ou_name, [('Over', ov), ('Under', un)])

    btts = generate_btts()
    mk(event, 'BTTS', 'Ambos Equipos Anotan', [('Si', btts[0]), ('No', btts[1])])

    btts_ou = generate_btts_ou25()
    mk(event, 'BTTS_OU25', 'BTTS + O/U 2.5', [
        ('Si + Over 2.5', btts_ou[0]), ('Si + Under 2.5', btts_ou[1]),
        ('No + Over 2.5', btts_ou[2]), ('No + Under 2.5', btts_ou[3]),
    ])

    oh, uh = generate_ou_goals(1.30, 2.00)
    mk(event, 'HOME_OU_15', 'Goles Local O/U 1.5', [('Over 1.5', oh), ('Under 1.5', uh)])
    oa, ua = generate_ou_goals(1.20, 1.80)
    mk(event, 'AWAY_OU_05', 'Goles Visitante O/U 0.5', [('Over 0.5', oa), ('Under 0.5', ua)])

    htft = generate_ht_ft()
    from domain.events import HT_FT_COMBOS
    mk(event, 'HT_FT', 'Descanso/Final', list(zip(HT_FT_COMBOS, htft)))

    ht_o = generate_1X2()
    mk(event, 'HT_1X2', '1er Tiempo 1X2', [('Local HT', ht_o[0]), ('Empate HT', ht_o[1]), ('Visitante HT', ht_o[2])])

    ht_ou = generate_ou_goals()
    mk(event, 'HT_OU_15', '1er Tiempo O/U 1.5', [('Over 1.5', ht_ou[0]), ('Under 1.5', ht_ou[1])])

    for hc_type, hc_name, away_label in [('HC_0', 'HC 0', 'Visitante 0'), ('HC_M05', 'HC -0.5', 'Visitante +0.5'),
                               ('HC_M1', 'HC -1', 'Visitante +1'), ('HC_M15', 'HC -1.5', 'Visitante +1.5'),
                               ('HC_M2', 'HC -2', 'Visitante +2')]:
        h1, h2 = generate_handicap()
        mk(event, hc_type, f'Handicap {hc_name}', [(f'Local {hc_name}', h1), (away_label, h2)])

    eh1, eX, eh2 = generate_1X2()
    mk(event, 'HC_EURO', 'Handicap Europeo -1', [('Local -1', eh1), ('Empate -1', eX), ('Visitante -1', eh2)])

    cs = generate_correct_score()
    from domain.events import CORRECT_SCORES
    mk(event, 'CORRECT_SCORE', 'Marcador Exacto', list(zip(CORRECT_SCORES, cs)))

    oe = generate_ou_goals()
    mk(event, 'ODD_EVEN', 'Par/Impar Goles', [('Par', oe[0]), ('Impar', oe[1])])

    b1h = generate_btts()
    mk(event, 'BTTS_1H', 'Ambos Marcan 1T', [('Si', b1h[0]), ('No', b1h[1])])

    cs_h = generate_ou_goals(1.50, 3.00)
    mk(event, 'CLEAN_HOME', 'Clean Sheet Local', [('Si', cs_h[0]), ('No', cs_h[1])])

    cs_a = generate_ou_goals(1.50, 3.00)
    mk(event, 'CLEAN_AWAY', 'Clean Sheet Visitante', [('Si', cs_a[0]), ('No', cs_a[1])])

    fs = generate_1X2()
    mk(event, 'FIRST_SCORE', 'Primer Equipo en Anotar', [('Local', fs[0]), ('Visitante', fs[2]), ('Sin Goles', fs[1])])

    mgh = generate_ou_goals(1.10, 3.50)
    mk(event, 'MULTI_HOME', 'Multi-Goles Local', [('1+', mgh[0]), ('2+', mgh[1]), ('3+', mgh[1] * 2)])

    mga = generate_ou_goals(1.10, 3.50)
    mk(event, 'MULTI_AWAY', 'Multi-Goles Visitante', [('1+', mga[0]), ('2+', mga[1]), ('3+', mga[1] * 2)])

    co = generate_ou_goals(1.70, 2.10)
    mk(event, 'CORNERS_OU', 'Corneres O/U 9.5', [('Over 9.5', co[0]), ('Under 9.5', co[1])])

    ch1, ch2 = generate_handicap()
    mk(event, 'CORNERS_HC', 'Handicap Corneres -1.5', [('Local -1.5', ch1), ('Visitante +1.5', ch2)])

    ct_o, ct_u = generate_ou_goals(1.75, 2.05)
    mk(event, 'CARDS_OU', 'Tarjetas O/U 4.5', [('Over 4.5', ct_o), ('Under 4.5', ct_u)])

    wtn_h, wtn_a, wtn_n = generate_1X2()
    mk(event, 'WIN_TO_NIL', 'Ganar a Cero', [('Local', wtn_h), ('Visitante', wtn_a), ('Ninguno', wtn_n)])

    wbh_h, wbh_a, wbh_n = generate_1X2()
    mk(event, 'WIN_BOTH_HALVES', 'Ganar Ambos Tiempos', [('Local', wbh_h), ('Visitante', wbh_a), ('Ninguno', wbh_n)])

    gb1, gb2, gb3 = generate_ou_goals(1.30, 2.00)[0], generate_ou_goals(1.80, 3.00)[0], generate_ou_goals(3.00, 8.00)[0]
    mk(event, 'GOAL_BANDS', 'Bandas de Goles', [('0-1', gb1), ('2-3', gb2), ('4+', gb3)])

    pen_si, pen_no = generate_btts()
    mk(event, 'PENALTY', 'Penalti en el Partido', [('Si', pen_si), ('No', pen_no)])

    eg_h0, eg_h1, eg_h2, eg_h3 = [rand_odds(1.60, 12.00) for _ in range(4)]
    mk(event, 'EXACT_GOALS_HOME', 'Goles Exactos Local', [('0', eg_h0), ('1', eg_h1), ('2', eg_h2), ('3+', eg_h3)])

    eg_a0, eg_a1, eg_a2, eg_a3 = [rand_odds(1.60, 12.00) for _ in range(4)]
    mk(event, 'EXACT_GOALS_AWAY', 'Goles Exactos Visitante', [('0', eg_a0), ('1', eg_a1), ('2', eg_a2), ('3+', eg_a3)])


def create_tennis_markets(event):
    from django.conf import settings
    margin = Decimal(settings.EVENTS_MARGIN_FACTOR)
    p1, p2 = event.team_home, event.team_away
    raw_tennis = generate_tennis_winner()
    w1, w2 = calculate_odds_with_margin(raw_tennis, margin) if margin > 0 else raw_tennis
    mk(event, 'TENNIS_WINNER', 'Ganador del Partido', [(p1, w1), (p2, w2)])

    h1, h2 = generate_tennis_handicap()
    mk(event, 'TENNIS_HC', 'Handicap Juegos', [(f'{p1} -3.5', h1), (f'{p2} +3.5', h2)])

    hg1, hg2 = generate_handicap()
    mk(event, 'TENNIS_HC_GAMES', 'Handicap Games -1.5', [(f'{p1} -1.5', hg1), (f'{p2} +1.5', hg2)])

    o1, u1 = generate_ou_goals(1.70, 2.10)
    mk(event, 'TENNIS_TOTAL', 'Total Juegos O/U 22.5', [('Over 22.5', o1), ('Under 22.5', u1)])

    sb = generate_set_betting()
    mk(event, 'TENNIS_SET', 'Set Betting', list(zip(SET_BETS, sb)))

    s1w1, s1w2 = generate_tennis_winner()
    mk(event, 'TENNIS_SET1', 'Primer Set', [(p1, s1w1), (p2, s1w2)])

    s1o, s1u = generate_ou_goals(1.70, 2.10)
    mk(event, 'TENNIS_SET1_TOT', 'Juegos Set 1 O/U 9.5', [('Over 9.5', s1o), ('Under 9.5', s1u)])

    s2w1, s2w2 = generate_tennis_winner()
    mk(event, 'TENNIS_SET2', 'Ganador Set 2', [(p1, s2w1), (p2, s2w2)])

    s2o, s2u = generate_ou_goals(1.70, 2.10)
    mk(event, 'TENNIS_SET2_TOT', 'Juegos Set 2 O/U 9.5', [('Over 9.5', s2o), ('Under 9.5', s2u)])

    bs1, bs2 = generate_btts()
    mk(event, 'TENNIS_BOTH', 'Ambos Ganan Set', [('Si', bs1), ('No', bs2)])


def create_basketball_markets(event):
    from django.conf import settings
    margin = Decimal(settings.EVENTS_MARGIN_FACTOR)
    raw_ml = generate_1X2()
    o1, _, o2 = calculate_odds_with_margin(raw_ml, margin) if margin > 0 else raw_ml
    mk(event, 'BASKET_ML', 'Moneyline', [('Local', o1), ('Visitante', o2)])

    s1, s2 = generate_basket_spread()
    mk(event, 'BASKET_SPREAD', 'Spread', [('Local -5.5', s1), ('Visitante +5.5', s2)])

    to, tu = generate_ou_goals(1.80, 2.00)
    mk(event, 'BASKET_TOTAL', 'Total Puntos O/U 215.5', [('Over 215.5', to), ('Under 215.5', tu)])

    hs1, hs2 = generate_basket_spread()
    mk(event, 'BASKET_HT_SPR', 'Handicap Mitad', [('Local HT -2.5', hs1), ('Visitante HT +2.5', hs2)])

    ho1, _, ho2 = generate_1X2()
    mk(event, 'BASKET_HT_ML', 'Mitad 1X2', [('Local HT', ho1), ('Visitante HT', ho2)])

    hto, htu = generate_ou_goals(1.80, 2.00)
    mk(event, 'BASKET_HOME_TOT', 'Puntos Local O/U 105.5', [('Over 105.5', hto), ('Under 105.5', htu)])

    q1l, _, q1v = generate_1X2()
    t1, t2 = event.team_home, event.team_away
    mk(event, 'BASKET_Q1', 'Ganador 1er Cuarto', [(t1, q1l), ('Empate', q1l * 5), (t2, q1v)])

    q2l, _, q2v = generate_1X2()
    mk(event, 'BASKET_Q2', 'Ganador 2do Cuarto', [(t1, q2l), ('Empate', q2l * 5), (t2, q2v)])

    r20l, r20v = generate_btts()
    mk(event, 'BASKET_RACE20', 'Carrera a 20 Puntos', [(t1, r20l), (t2, r20v)])

    pi, pp = generate_ou_goals(1.80, 2.00)
    mk(event, 'BASKET_PAR_IMP', 'Total Par/Impar', [('Par', pi), ('Impar', pp)])


def create_simple_markets(event):
    from django.conf import settings
    margin = Decimal(settings.EVENTS_MARGIN_FACTOR)
    raw_1X2 = generate_1X2()
    o1, _, o2 = calculate_odds_with_margin(raw_1X2, margin) if margin > 0 else raw_1X2
    mk(event, '1X2', 'Ganador del Partido', [('Local', o1), ('Visitante', o2)])
    to, tu = generate_ou_goals(1.80, 2.00)
    mk(event, 'OU_25', 'Total Sets O/U 2.5', [('Over 2.5', to), ('Under 2.5', tu)])
    ou15_o, ou15_u = generate_ou_goals(1.40, 3.00)
    mk(event, 'OU_15', 'Total Sets O/U 1.5', [('Over 1.5', ou15_o), ('Under 1.5', ou15_u)])
    ou35_o, ou35_u = generate_ou_goals(1.70, 2.10)
    mk(event, 'OU_35', 'Total Sets O/U 3.5', [('Over 3.5', ou35_o), ('Under 3.5', ou35_u)])
    s1, s2 = generate_basket_spread()
    mk(event, 'HC_0', 'Handicap 0', [('Local 0', s1), ('Visitante 0', s2)])
    hm1, hm2 = generate_handicap()
    mk(event, 'HC_M15', 'Handicap -1.5', [('Local -1.5', hm1), ('Visitante +1.5', hm2)])
    pi, pp = generate_ou_goals(1.80, 2.00)
    mk(event, 'PAR_IMPAR', 'Total Puntos Par/Impar', [('Par', pi), ('Impar', pp)])
    ts3, ts31, ts32, ts23, ts13, ts03 = generate_set_betting()
    mk(event, 'TOTAL_SETS', 'Total Sets Exactos', [
        ('3-0', ts3), ('3-1', ts31), ('3-2', ts32),
        ('2-3', ts23), ('1-3', ts13), ('0-3', ts03),
    ])
