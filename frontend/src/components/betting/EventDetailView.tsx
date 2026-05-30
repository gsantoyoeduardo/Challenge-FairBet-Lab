import { useEffect, useState } from 'react'
import { ArrowLeft } from 'lucide-react'
import { events as eventsService, type EventDetail, type Market } from '../../services/events'

interface EventDetailViewProps {
  eventId: number
  onBack: () => void
  onSelect: (selectionId: number, odds: string, name: string, event: any) => void
  selectedIds: Set<number>
}

interface Category {
  title: string
  types: string[]
}

const CATEGORIES: Record<string, Category[]> = {
  football: [
    { title: 'Rápidas', types: ['1X2', 'DOUBLE_CHANCE', 'DRAW_NO_BET', 'BTTS'] },
    { title: 'Goles', types: ['OU_05', 'OU_15', 'OU_25', 'OU_35', 'OU_45', 'GOAL_BANDS'] },
    { title: 'Equipo', types: ['HOME_OU_15', 'AWAY_OU_05', 'EXACT_GOALS_HOME', 'EXACT_GOALS_AWAY'] },
    { title: 'MARCAN', types: ['BTTS_OU25', 'BTTS_1H', 'CLEAN_HOME', 'CLEAN_AWAY'] },
    { title: 'Hándicap', types: ['HC_0', 'HC_M05', 'HC_M1', 'HC_M15', 'HC_M2', 'HC_EURO'] },
    { title: '1T', types: ['HT_1X2', 'HT_OU_15', 'HT_FT'] },
    { title: 'Córneres', types: ['CORNERS_OU', 'CORNERS_HC'] },
    { title: 'Tarjetas', types: ['CARDS_OU'] },
    { title: 'Exacto', types: ['CORRECT_SCORE'] },
    { title: 'Otros', types: ['ODD_EVEN', 'FIRST_SCORE', 'MULTI_HOME', 'MULTI_AWAY', 'PENALTY', 'WIN_TO_NIL', 'WIN_BOTH_HALVES'] },
  ],
  tennis: [
    { title: 'Rápidas', types: ['TENNIS_WINNER'] },
    { title: 'Hándicap', types: ['TENNIS_HC', 'TENNIS_HC_GAMES'] },
    { title: 'Totales', types: ['TENNIS_TOTAL'] },
    { title: 'Sets', types: ['TENNIS_SET'] },
    { title: 'Set 1/2', types: ['TENNIS_SET1', 'TENNIS_SET1_TOT', 'TENNIS_SET2', 'TENNIS_SET2_TOT'] },
    { title: 'Otros', types: ['TENNIS_BOTH'] },
  ],
  basketball: [
    { title: 'Rápidas', types: ['BASKET_ML'] },
    { title: 'Spread', types: ['BASKET_SPREAD', 'BASKET_HT_SPR'] },
    { title: 'Totales', types: ['BASKET_TOTAL', 'BASKET_HOME_TOT'] },
    { title: 'Mitad', types: ['BASKET_HT_ML'] },
    { title: 'Cuartos', types: ['BASKET_Q1', 'BASKET_Q2'] },
    { title: 'Otros', types: ['BASKET_RACE20', 'BASKET_PAR_IMP'] },
  ],
  volleyball: [
    { title: 'Rápidas', types: ['1X2'] },
    { title: 'Sets', types: ['OU_15', 'OU_25', 'OU_35', 'TOTAL_SETS'] },
    { title: 'Hándicap', types: ['HC_0', 'HC_M15'] },
    { title: 'Otros', types: ['PAR_IMPAR'] },
  ],
}

export default function EventDetailView({ eventId, onBack, onSelect, selectedIds }: EventDetailViewProps) {
  const [event, setEvent] = useState<EventDetail | null>(null)
  const [tab, setTab] = useState(0)

  useEffect(() => {
    eventsService.detail(eventId).then((data) => {
      setEvent(data)
      setTab(0)
    })
  }, [eventId])

  if (!event) return <div className="text-gray-500 text-sm py-20 text-center">Cargando partido...</div>

  const marketMap = new Map<string, Market>()
  event.markets.forEach((m) => marketMap.set(m.type, m))

  const sportCat = CATEGORIES[event.sport.slug] || CATEGORIES.football

  const currentCat = sportCat[tab] || sportCat[0]
  const mkts = currentCat.types.map((t) => marketMap.get(t)).filter(Boolean) as Market[]

  return (
    <div className="space-y-3">
      <button onClick={onBack} className="flex items-center gap-1.5 text-xs text-gray-400 hover:text-white transition">
        <ArrowLeft className="w-3.5 h-3.5" />
        Volver
      </button>

      <div className="bg-[#1a1a1a] border border-gray-800 rounded-xl px-4 py-3">
        <div className="flex items-center justify-between mb-1">
          <span className="text-[10px] text-gray-500 uppercase">
            {event.sport.name} · {new Date(event.start_time).toLocaleString([], { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })}
          </span>
          {event.status === 'en_vivo' && (
            <span className="flex items-center gap-1.5 text-[10px] text-red-500 font-semibold">
              <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />EN VIVO
            </span>
          )}
        </div>
        <p className="text-sm font-bold tracking-tight">
          {event.team_home} <span className="text-gray-600 mx-1.5">vs</span> {event.team_away}
        </p>
      </div>

      <div className="flex gap-0.5 overflow-x-auto scrollbar-none">
        {sportCat.map((cat, idx) => {
          const count = cat.types.map((t) => marketMap.get(t)).filter(Boolean).length
          if (count === 0) return null
          return (
            <button
              key={idx}
              onClick={() => setTab(idx)}
              className={`flex-shrink-0 px-2.5 py-1.5 rounded text-[11px] font-semibold transition whitespace-nowrap ${
                tab === idx
                  ? 'bg-primary-500 text-black'
                  : 'bg-[#1a1a1a] text-gray-400 hover:text-white border border-gray-800'
              }`}
            >
              {cat.title}
            </button>
          )
        })}
      </div>

      <div className="bg-[#1a1a1a] border border-gray-800 rounded-xl overflow-hidden">
        <div className="divide-y divide-gray-800/30 max-h-[calc(100vh-340px)] overflow-y-auto">
          {mkts.map((m) => (
            <div key={m.id} className="px-4 py-2.5 flex items-center gap-3 hover:bg-[#111]/50 transition">
              <span className="text-xs text-gray-400 w-28 flex-shrink-0">{m.name}</span>
              <div className="flex gap-1.5 flex-wrap flex-1 justify-end">
                {m.selections.map((s) => {
                  const isSel = selectedIds.has(s.id)
                  return (
                    <button
                      key={s.id}
                      onClick={() => onSelect(s.id, s.odds, s.name, event)}
                      className={`min-w-[65px] px-2.5 py-1.5 rounded text-xs font-semibold transition-all ${
                        isSel
                          ? 'bg-primary-500 text-black'
                          : 'bg-black hover:bg-[#252525] text-gray-300 border border-gray-800 hover:border-gray-600'
                      }`}
                    >
                      <span className="block text-[10px] text-gray-500 text-center">
                        {s.name.length > 10 ? s.name.slice(0, 10) : s.name}
                      </span>
                      <span className={`block text-center ${isSel ? 'text-black' : 'text-primary-400'}`}>
                        {parseFloat(s.odds).toFixed(2)}
                      </span>
                    </button>
                  )
                })}
              </div>
            </div>
          ))}
        </div>
      </div>
      <p className="text-[9px] text-gray-600 mt-2 text-center">
        Juega con responsabilidad. El juego en exceso puede causar adicción.
      </p>
    </div>
  )
}
