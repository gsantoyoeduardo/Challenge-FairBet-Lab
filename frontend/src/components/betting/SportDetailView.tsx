import { useEffect, useState } from 'react'
import { ArrowLeft } from 'lucide-react'
import { events as eventsService, type EventDetail } from '../../services/events'

interface SportDetailViewProps {
  sportSlug: string
  sportName: string
  onBack: () => void
  onSelect: (selectionId: number, odds: string, name: string, event: any) => void
  selectedIds: Set<number>
  onSelectEvent: (eventId: number) => void
}

const SPORT_MARKETS: Record<string, string[]> = {
  football: ['1X2', 'DOUBLE_CHANCE', 'OU_25', 'BTTS', 'HC_0', 'HT_1X2', 'CORRECT_SCORE'],
  tennis: ['TENNIS_WINNER', 'TENNIS_HC', 'TENNIS_TOTAL', 'TENNIS_SET', 'TENNIS_SET1', 'TENNIS_BOTH'],
  basketball: ['BASKET_ML', 'BASKET_SPREAD', 'BASKET_TOTAL', 'BASKET_Q1', 'BASKET_RACE20', 'BASKET_PAR_IMP'],
  volleyball: ['1X2', 'OU_15', 'OU_25', 'HC_0', 'HC_M15', 'PAR_IMPAR', 'TOTAL_SETS'],
}

export default function SportDetailView({ sportSlug, sportName, onBack, onSelect, selectedIds, onSelectEvent }: SportDetailViewProps) {
  const [events, setEvents] = useState<EventDetail[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    eventsService.list({ sport: sportSlug }).then((evs) => {
      Promise.all(evs.map((e) => eventsService.detail(e.id))).then(setEvents).finally(() => setLoading(false))
    })
  }, [sportSlug])

  if (loading) return <div className="text-gray-500 text-sm py-10 text-center">Cargando {sportName}...</div>

  const displayTypes = SPORT_MARKETS[sportSlug] || ['1X2', 'OU_25', 'BTTS', 'HC_0']

  return (
    <div className="space-y-6">
      <button onClick={onBack} className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition">
        <ArrowLeft className="w-4 h-4" />
        Volver a todos
      </button>

      <h2 className="text-lg font-bold text-primary-400">{sportName}</h2>

      {events.map((ev) => (
        <div key={ev.id} className="bg-[#1a1a1a] border border-gray-800 rounded-xl p-5">
          <div className="flex items-center justify-between mb-4 cursor-pointer" onClick={() => onSelectEvent(ev.id)}>
            <div>
              <p className="font-bold">{ev.team_home} vs {ev.team_away}</p>
              <p className="text-xs text-gray-500 mt-1">
                {new Date(ev.start_time).toLocaleString([], { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })}
                {ev.status === 'en_vivo' && <span className="ml-2 text-red-500">● EN VIVO</span>}
              </p>
            </div>
            <span className="text-xs text-primary-400">{ev.markets.length} mercados</span>
          </div>
          <div className="flex flex-wrap gap-3">
            {ev.markets.filter(m => displayTypes.includes(m.type)).map((m) => (
              <div key={m.id} className="flex gap-1 items-center bg-black rounded-lg px-2 py-1.5">
                <span className="text-[10px] text-gray-500 min-w-[60px]">{m.name}</span>
                <div className="flex gap-1">
                  {m.selections.map((s) => {
                    const isSel = selectedIds.has(s.id)
                    return (
                      <button
                        key={s.id}
                        onClick={() => onSelect(s.id, s.odds, s.name, ev)}
                        className={`px-2 py-0.5 rounded text-xs font-semibold transition ${
                          isSel ? 'bg-primary-500 text-black' : 'bg-[#1a1a1a] hover:bg-[#252525] text-gray-300'
                        }`}
                      >
                        {s.name === 'Local' || s.name === 'Empate' || s.name === 'Visitante'
                          ? s.name.charAt(0)
                          : s.name.length > 10 ? s.name.slice(0, 10) : s.name}
                        <span className="ml-1 text-primary-400">{parseFloat(s.odds).toFixed(2)}</span>
                      </button>
                    )
                  })}
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
      <p className="text-[9px] text-gray-600 mt-2 text-center">
        Juega con responsabilidad. El juego en exceso puede causar adicción.
      </p>
    </div>
  )
}
