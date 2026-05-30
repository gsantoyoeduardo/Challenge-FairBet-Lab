import { useEffect, useState } from 'react'
import { adminBetting, type AdminBet } from '../../services/adminBetting'
import { adminEvents } from '../../services/adminEvents'
import { CheckCircle, XCircle, Loader2, ChevronDown, ChevronUp, Search, Shield } from 'lucide-react'

export default function BetManagerPage() {
  const [bets, setBets] = useState<AdminBet[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<'active' | 'all'>('active')
  const [expandedBetId, setExpandedBetId] = useState<number | null>(null)
  const [liquidating, setLiquidating] = useState<number | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [mensaje, setMensaje] = useState('')
  const [exposureCache, setExposureCache] = useState<Record<number, {
    selection_id: number
    selection_name: string
    odds: string
    bets_count: number
    potential_payout: string
  }[]>>({})
  const [loadingExposure, setLoadingExposure] = useState(false)

  const load = () => {
    setLoading(true)
    const loader = filter === 'active'
      ? adminBetting.getActiveBets()
      : adminBetting.getAllBets()
    loader.then(setBets).finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [filter])

  useEffect(() => {
    if (!expandedBetId) return
    const bet = bets.find(b => b.id === expandedBetId)
    if (!bet) return

    const eventIds = [...new Set(bet.selections.map(s => s.event_id))]
    const missing = eventIds.filter(id => !(id in exposureCache))
    if (missing.length === 0) return

    setLoadingExposure(true)
    Promise.all(missing.map(id => adminEvents.getExposure(id).then(data => ({ id, data })).catch(() => ({ id, data: [] }))))
      .then(results => {
        setExposureCache(prev => {
          const next = { ...prev }
          results.forEach(r => { next[r.id] = r.data })
          return next
        })
      })
      .finally(() => setLoadingExposure(false))
  }, [expandedBetId, bets])

  const handleLiquidate = async (betId: number, markAsWon: boolean) => {
    setLiquidating(betId)
    setMensaje('')
    try {
      const bet = bets.find(b => b.id === betId)
      if (!bet) return
      const winningIds = markAsWon ? bet.selections.map(s => s.selection_id) : []
      await adminBetting.liquidateBet(betId, winningIds)
      setMensaje(`Apuesta #${betId} liquidada como ${markAsWon ? 'Ganada' : 'Perdida'}`)
      load()
    } catch (err: any) {
      setMensaje(err.response?.data?.error || 'Error al liquidar')
    } finally {
      setLiquidating(null)
    }
  }

  const filteredBets = bets.filter(bet => {
    if (!searchQuery) return true
    const q = searchQuery.toLowerCase()
    return (
      bet.username.toLowerCase().includes(q) ||
      bet.id.toString().includes(q) ||
      bet.selections.some(s =>
        s.selection_name.toLowerCase().includes(q) ||
        s.event.home.toLowerCase().includes(q) ||
        s.event.away.toLowerCase().includes(q)
      )
    )
  })

  const statusColors: Record<string, string> = {
    accepted: 'text-yellow-400 bg-yellow-400/10',
    won: 'text-green-400 bg-green-400/10',
    lost: 'text-red-400 bg-red-400/10',
    cashed_out: 'text-blue-400 bg-blue-400/10',
    cancelled: 'text-gray-400 bg-gray-400/10',
  }

  const statusLabel: Record<string, string> = {
    accepted: 'Activa',
    won: 'Ganada',
    lost: 'Perdida',
    cashed_out: 'Cash-out',
    cancelled: 'Cancelada',
  }

  return (
    <div className="max-w-5xl mx-auto px-4">
      <h1 className="text-xl font-bold mb-6">Gestion de Apuestas</h1>

      {mensaje && (
        <div className={`border rounded-lg px-4 py-3 mb-4 text-sm ${
          mensaje.startsWith('Error')
            ? 'bg-red-900/20 border-red-800 text-red-400'
            : 'bg-green-900/20 border-green-800 text-green-400'
        }`}>
          {mensaje}
        </div>
      )}

      <div className="flex gap-3 mb-6 flex-wrap">
        <div className="flex gap-2">
          {(['active', 'all'] as const).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-4 py-1.5 rounded-lg text-sm font-medium transition ${
                filter === f ? 'bg-primary-500 text-black' : 'bg-[#1a1a1a] border border-gray-800 text-gray-300 hover:text-white'
              }`}
            >
              {f === 'active' ? 'Activas' : 'Todas'}
            </button>
          ))}
        </div>
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
          <input
            type="text"
            placeholder="Buscar por usuario, evento o seleccion..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-[#1a1a1a] border border-gray-800 rounded-lg pl-10 pr-4 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-primary-500"
          />
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center py-10">
          <Loader2 className="w-6 h-6 text-gray-500 animate-spin" />
        </div>
      ) : filteredBets.length === 0 ? (
        <div className="text-center py-10 text-gray-500">No hay apuestas</div>
      ) : (
        <div className="space-y-3">
          {filteredBets.map((bet) => (
            <div key={bet.id} className="bg-[#1a1a1a] border border-gray-800 rounded-xl overflow-hidden">
              <button
                onClick={() => setExpandedBetId(prev => prev === bet.id ? null : bet.id)}
                className="w-full p-4 flex items-center justify-between hover:bg-[#222] transition text-left"
              >
                <div className="flex items-center gap-4">
                  <span className="text-sm font-mono text-gray-400">#{bet.id}</span>
                  <span className="text-sm text-white">{bet.username}</span>
                  <span className="text-sm text-gray-400">
                    {new Date(bet.placed_at).toLocaleDateString()} {new Date(bet.placed_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
                <div className="flex items-center gap-4">
                  <div className="text-right">
                    <span className="text-sm text-gray-400">Stake: </span>
                    <span className="text-sm font-semibold text-white">{parseFloat(bet.stake).toFixed(2)} BP</span>
                  </div>
                  <span className="text-sm text-primary-400 font-semibold">x{parseFloat(bet.total_odds).toFixed(2)}</span>
                  <span className={`text-xs px-2 py-0.5 rounded font-medium ${statusColors[bet.status]}`}>
                    {statusLabel[bet.status] || bet.status}
                  </span>
                  {expandedBetId === bet.id ? (
                    <ChevronUp className="w-4 h-4 text-gray-500" />
                  ) : (
                    <ChevronDown className="w-4 h-4 text-gray-500" />
                  )}
                </div>
              </button>

              {expandedBetId === bet.id && (
                <div className="border-t border-gray-800">
                  <div className="p-4 space-y-2 bg-black/40">
                    <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">Selecciones</p>
                    {bet.selections.map((sel, idx) => (
                      <div key={idx} className="flex items-center gap-3 bg-[#111] border border-gray-800 rounded-lg p-3">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="text-xs font-semibold text-white">{sel.selection_name}</span>
                            <span className="text-[10px] px-1.5 py-0.5 rounded bg-primary-600/20 text-primary-400 font-medium">
                              {sel.market_type}
                            </span>
                          </div>
                          <p className="text-xs text-gray-500">
                            {sel.event.home} vs {sel.event.away}
                          </p>
                        </div>
                        <span className="text-sm font-bold text-primary-400">{parseFloat(sel.odds_at_time).toFixed(2)}</span>
                      </div>
                    ))}
                  </div>

                  {(() => {
                    const seenEvents = new Map<number, { home: string; away: string }>()
                    bet.selections.forEach(sel => {
                      if (!seenEvents.has(sel.event_id)) {
                        seenEvents.set(sel.event_id, { home: sel.event.home, away: sel.event.away })
                      }
                    })
                    const uniqueEventIds = [...seenEvents.keys()]
                    if (uniqueEventIds.length === 0) return null
                    return (
                      <div className="p-4 border-t border-gray-800 space-y-4">
                        <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide flex items-center gap-1.5">
                          <Shield className="w-3.5 h-3.5 text-orange-400" />
                          Exposure por Evento
                        </p>
                        {uniqueEventIds.map(eventId => {
                          const ev = seenEvents.get(eventId)!
                          const data = exposureCache[eventId]
                          return (
                            <div key={eventId} className="bg-[#111] border border-gray-800 rounded-lg overflow-hidden">
                              <div className="px-3 py-2 bg-black/30 border-b border-gray-800/50">
                                <p className="text-xs font-semibold text-white">{ev.home} vs {ev.away}</p>
                              </div>
                              {loadingExposure && !data ? (
                                <div className="flex justify-center py-3">
                                  <Loader2 className="w-4 h-4 text-gray-500 animate-spin" />
                                </div>
                              ) : data && data.length > 0 ? (
                                <div className="divide-y divide-gray-800/30">
                                  <div className="grid grid-cols-[1fr_70px_70px_90px] gap-2 px-3 py-1.5 text-[10px] text-gray-500 font-semibold">
                                    <span>Seleccion</span>
                                    <span className="text-center">Odds</span>
                                    <span className="text-center">Apuestas</span>
                                    <span className="text-center">Payout Pot.</span>
                                  </div>
                                  {data.map(sel => (
                                    <div key={sel.selection_id} className="grid grid-cols-[1fr_70px_70px_90px] gap-2 px-3 py-2 items-center text-xs">
                                      <span className="text-gray-300 truncate">{sel.selection_name}</span>
                                      <span className="text-center text-primary-400">{parseFloat(sel.odds).toFixed(2)}</span>
                                      <span className="text-center text-gray-400">{sel.bets_count}</span>
                                      <span className="text-center text-red-400 font-semibold">{parseFloat(sel.potential_payout).toFixed(2)} BP</span>
                                    </div>
                                  ))}
                                </div>
                              ) : (
                                <p className="text-gray-500 text-center py-3 text-xs">Sin datos de exposure</p>
                              )}
                            </div>
                          )
                        })}
                      </div>
                    )
                  })()}

                  {bet.status === 'accepted' && (
                    <div className="p-4 border-t border-gray-800 flex gap-3">
                      <button
                        onClick={() => handleLiquidate(bet.id, true)}
                        disabled={liquidating === bet.id}
                        className="flex items-center gap-2 bg-green-600 hover:bg-green-500 disabled:opacity-50 text-white font-semibold px-4 py-2 rounded-lg text-sm transition"
                      >
                        <CheckCircle className="w-4 h-4" />
                        Marcar Ganada
                      </button>
                      <button
                        onClick={() => handleLiquidate(bet.id, false)}
                        disabled={liquidating === bet.id}
                        className="flex items-center gap-2 bg-red-600 hover:bg-red-500 disabled:opacity-50 text-white font-semibold px-4 py-2 rounded-lg text-sm transition"
                      >
                        <XCircle className="w-4 h-4" />
                        Marcar Perdida
                      </button>
                    </div>
                  )}

                  {bet.status !== 'accepted' && bet.payout && (
                    <div className="p-4 border-t border-gray-800">
                      <span className={`text-sm font-semibold ${
                        bet.status === 'won' ? 'text-green-400' :
                        bet.status === 'cashed_out' ? 'text-blue-400' : 'text-red-400'
                      }`}>
                        Payout: {parseFloat(bet.payout).toFixed(2)} BP
                      </span>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
