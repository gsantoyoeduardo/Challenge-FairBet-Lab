import { useEffect, useState } from 'react'
import { operator, type ExposureSummaryItem, type ExposureItem } from '../../services/operator'
import { ChevronDown, ChevronUp, Loader2 } from 'lucide-react'

export default function ExposureChart() {
  const [summary, setSummary] = useState<ExposureSummaryItem[]>([])
  const [expandedEventId, setExpandedEventId] = useState<number | null>(null)
  const [detail, setDetail] = useState<ExposureItem[]>([])
  const [loading, setLoading] = useState(true)
  const [loadingDetail, setLoadingDetail] = useState(false)

  useEffect(() => {
    operator.getExposureSummary()
      .then(setSummary)
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const handleExpand = async (eventId: number) => {
    if (expandedEventId === eventId) {
      setExpandedEventId(null)
      setDetail([])
      return
    }
    setExpandedEventId(eventId)
    setLoadingDetail(true)
    try {
      const result = await operator.getExposure(eventId)
      setDetail(result)
    } catch {
      setDetail([])
    } finally {
      setLoadingDetail(false)
    }
  }

  if (loading) {
    return <div className="flex justify-center py-8"><Loader2 className="w-5 h-5 text-gray-500 animate-spin" /></div>
  }

  if (summary.length === 0) {
    return <p className="text-gray-500 text-center py-8 text-sm">No hay eventos con apuestas activas</p>
  }

  return (
    <div className="space-y-3">
      {summary.map((item) => (
        <div key={item.event_id} className="bg-[#1a1a1a] border border-gray-800 rounded-xl overflow-hidden">
          <button
            onClick={() => handleExpand(item.event_id)}
            className="w-full p-4 flex items-center justify-between hover:bg-[#222] transition text-left"
          >
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold text-white truncate">
                {item.team_home} vs {item.team_away}
              </p>
              <p className="text-[10px] text-gray-500 mt-0.5">
                {item.sport} · {item.total_bets} apuestas
              </p>
            </div>
            <div className="flex items-center gap-4 ml-4">
              <div className="text-right">
                <p className="text-[10px] text-gray-500">Riesgo máx</p>
                <p className="text-sm font-bold text-red-400">{parseFloat(item.max_payout).toFixed(2)} BP</p>
              </div>
              {expandedEventId === item.event_id ? (
                <ChevronUp className="w-4 h-4 text-gray-500" />
              ) : (
                <ChevronDown className="w-4 h-4 text-gray-500" />
              )}
            </div>
          </button>

          {expandedEventId === item.event_id && (
            <div className="border-t border-gray-800">
              {loadingDetail ? (
                <div className="flex justify-center py-4">
                  <Loader2 className="w-4 h-4 text-gray-500 animate-spin" />
                </div>
              ) : detail.length > 0 ? (
                <div className="divide-y divide-gray-800/30">
                  <div className="grid grid-cols-[1fr_80px_80px_100px] gap-2 px-4 py-2 text-[10px] text-gray-500 font-semibold bg-black/30">
                    <span>Seleccion</span>
                    <span className="text-center">Odds</span>
                    <span className="text-center">Apuestas</span>
                    <span className="text-center">Payout Pot.</span>
                  </div>
                  {detail.map((sel) => (
                    <div key={sel.selection_id} className="grid grid-cols-[1fr_80px_80px_100px] gap-2 px-4 py-2.5 items-center text-xs">
                      <span className="text-gray-300">{sel.selection_name}</span>
                      <span className="text-center text-primary-400">{parseFloat(sel.odds).toFixed(2)}</span>
                      <span className="text-center text-gray-400">{sel.bets_count}</span>
                      <span className="text-center text-red-400 font-semibold">{parseFloat(sel.potential_payout).toFixed(2)} BP</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500 text-center py-4 text-xs">Sin datos de exposure</p>
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
