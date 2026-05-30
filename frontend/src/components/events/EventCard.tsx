import { useState, useEffect } from 'react'
import { events as eventsService, type EventItem, type Selection } from '../../services/events'

interface EventCardProps {
  event: EventItem
  onSelect: (selectionId: number, odds: string, name: string, event: EventItem) => void
  selectedIds: Set<number>
  compact?: boolean
  featured?: boolean
  onViewDetail?: (eventId: number) => void
}

export default function EventCard({ event, onSelect, selectedIds, compact, featured, onViewDetail }: EventCardProps) {
  const [selections, setSelections] = useState<Selection[]>([])
  const [expanded, setExpanded] = useState(false)
  const isLive = event.status === 'en_vivo'

  const mainOdds = event.main_odds || []

  useEffect(() => {
    if (expanded && selections.length === 0) {
      eventsService.detail(event.id).then((d) => {
        const allSelections = d.markets.flatMap((m) => m.selections)
        setSelections(allSelections)
      })
    }
  }, [expanded, event.id, selections.length])

  if (compact) {
    return (
      <div className="bg-[#1a1a1a] border border-gray-800 rounded-lg p-3 flex items-center gap-3">
        <div className="flex-1 min-w-0">
          <p className="text-xs font-medium truncate">{event.team_home} vs {event.team_away}</p>
          <p className="text-[10px] text-gray-500 mt-0.5">
            {new Date(event.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </p>
        </div>
        <div className="flex gap-1">
          {mainOdds.slice(0, 3).map((o) => {
            const isSel = selectedIds.has(o.id)
            return (
              <button
                key={o.id}
                onClick={(e) => { e.stopPropagation(); onSelect(o.id, o.odds, o.name, event) }}
                className={`px-3 py-1 rounded text-xs font-semibold transition ${
                  isSel ? 'bg-primary-500 text-black' : 'bg-black hover:bg-primary-500 hover:text-black'
                }`}
              >
                {parseFloat(o.odds).toFixed(2)}
              </button>
            )
          })}
        </div>
      </div>
    )
  }

  if (featured) {
    return (
      <div className="bg-[#1a1a1a] border border-gray-800 rounded-xl p-4 hover:border-gray-700 transition min-h-[180px]">
        <div className="flex items-center gap-2 mb-3">
          <span className="text-[10px] text-primary-400 uppercase">{event.sport_name}</span>
          {isLive && (
            <span className="text-[10px] text-red-500 font-semibold flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />EN VIVO
            </span>
          )}
        </div>
        <p className="font-bold text-sm mb-1">{event.team_home}</p>
        <p className="font-bold text-sm mb-3">{event.team_away}</p>
        <p className="text-xs text-gray-500 mb-3">
          {new Date(event.start_time).toLocaleString([], { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })}
        </p>
        <div className="flex gap-1.5 mb-2">
          {mainOdds.slice(0, 3).map((o) => {
            const isSel = selectedIds.has(o.id)
            return (
              <button
                key={o.id}
                onClick={(e) => { e.stopPropagation(); onSelect(o.id, o.odds, o.name, event) }}
                className={`flex-1 py-1.5 rounded text-xs font-semibold transition ${
                  isSel ? 'bg-primary-500 text-black' : 'bg-black hover:bg-[#252525] text-gray-300'
                }`}
              >
                <span className="block text-[10px] text-gray-500">{o.name}</span>
                <span className={isSel ? 'text-black' : 'text-primary-400'}>{parseFloat(o.odds).toFixed(2)}</span>
              </button>
            )
          })}
        </div>
        <button
          onClick={(e) => { e.stopPropagation(); onViewDetail?.(event.id) }}
          className="w-full bg-black hover:bg-[#252525] py-2 rounded-lg text-xs text-gray-300 transition"
        >
          Ver más ({event.market_count} mercados)
        </button>
      </div>
    )
  }

  return (
    <div className="bg-[#1a1a1a] border border-gray-800 rounded-xl overflow-hidden hover:border-gray-700 transition">
      <div className="p-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs text-primary-400 font-medium uppercase">{event.sport_name}</span>
          {isLive && (
            <span className="flex items-center gap-1.5 text-xs text-red-500 font-semibold">
              <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
              EN VIVO
            </span>
          )}
        </div>
        <div className="text-center mb-3 cursor-pointer" onClick={() => onViewDetail?.(event.id)}>
          <p className="font-semibold text-sm">{event.team_home}</p>
          <p className="text-xs text-gray-500 my-1">vs</p>
          <p className="font-semibold text-sm">{event.team_away}</p>
        </div>
        <p className="text-xs text-gray-500 text-center mb-3">
          {new Date(event.start_time).toLocaleString([], { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })}
        </p>
        <div className="flex gap-1.5 mb-2">
          {mainOdds.slice(0, 3).map((o) => {
            const isSel = selectedIds.has(o.id)
            return (
              <button
                key={o.id}
                onClick={(e) => { e.stopPropagation(); onSelect(o.id, o.odds, o.name, event) }}
                className={`flex-1 py-2 rounded text-xs font-semibold transition ${
                  isSel ? 'bg-primary-500 text-black' : 'bg-black hover:bg-[#252525] text-gray-300'
                }`}
              >
                <span className="block text-[10px] text-gray-500">{o.name}</span>
                <span className={isSel ? 'text-black' : 'text-primary-400'}>{parseFloat(o.odds).toFixed(2)}</span>
              </button>
            )
          })}
        </div>
        {!expanded ? (
          <button
            onClick={() => setExpanded(true)}
            className="w-full text-xs text-gray-500 hover:text-white transition py-1 border-t border-gray-800 mt-2 pt-2"
          >
            + {event.market_count - mainOdds.length} mercados más
          </button>
        ) : (
          <div className="space-y-2 mt-2 border-t border-gray-800 pt-2">
            {selections
              .filter((s) => !mainOdds.find((m) => m.id === s.id))
              .map((sel) => {
                const isSelected = selectedIds.has(sel.id)
                return (
                  <button
                    key={sel.id}
                    onClick={() => onSelect(sel.id, sel.odds, sel.name, event)}
                    disabled={event.status !== 'programado' && event.status !== 'en_vivo'}
                    className={`w-full flex items-center justify-between px-3 py-1.5 rounded text-xs transition ${
                      isSelected
                        ? 'bg-primary-500 text-black font-semibold'
                        : 'bg-black hover:bg-[#252525] text-gray-300 disabled:opacity-40'
                    }`}
                  >
                    <span>{sel.name}</span>
                    <span className="font-bold text-primary-400">{parseFloat(sel.odds).toFixed(2)}</span>
                  </button>
                )
              })}
          </div>
        )}
      </div>
    <p className="text-[9px] text-gray-600 mt-2 text-center">
      Juega con responsabilidad. El juego en exceso puede causar adicci�n.
    </p>
    </div>
  )
}
