import { useEffect, useState } from 'react'
import { betting, type Bet } from '../services/betting'
import { ChevronDown, ChevronUp } from 'lucide-react'

export default function MyBetsPage() {
  const [bets, setBets] = useState<Bet[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('')
  const [expandedBetId, setExpandedBetId] = useState<number | null>(null)

  useEffect(() => {
    betting.misApuestas(filter ? { status: filter } : undefined)
      .then(setBets)
      .finally(() => setLoading(false))
  }, [filter])

  const toggleExpand = (betId: number) => {
    setExpandedBetId(prev => prev === betId ? null : betId)
  }

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
    <div className="max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Mis Apuestas</h1>

      <div className="flex gap-2 mb-6 flex-wrap">
        {['', 'accepted', 'won', 'lost', 'cashed_out'].map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-4 py-1.5 rounded-lg text-sm font-medium transition ${
              filter === f ? 'bg-primary-500 text-black' : 'bg-[#1a1a1a] border border-gray-800 text-gray-300 hover:text-white'
            }`}
          >
            {f === '' ? 'Todas' : f === 'won' ? 'Ganadas' : f === 'lost' ? 'Perdidas' : f === 'cashed_out' ? 'Cash-out' : 'Activas'}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="text-center py-10 text-gray-500">Cargando apuestas...</div>
      ) : bets.length === 0 ? (
        <div className="text-center py-10 text-gray-500">No tienes apuestas aun</div>
      ) : (
        <div className="space-y-3">
          {bets.map((bet) => (
            <div key={bet.id} className="bg-[#1a1a1a] border border-gray-800 rounded-xl overflow-hidden">
              <button
                onClick={() => toggleExpand(bet.id)}
                className="w-full p-4 flex items-center justify-between hover:bg-[#222] transition text-left"
              >
                <div>
                  <span className="text-xs text-gray-500">
                    #{bet.id} - {new Date(bet.placed_at).toLocaleDateString()}
                  </span>
                </div>
                <div className="flex items-center gap-3">
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

              <div className="px-4 pb-3">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-300">Stake: <span className="text-white font-semibold">{parseFloat(bet.stake).toFixed(2)} BP</span></span>
                  <span className="text-gray-300">Cuota: <span className="text-primary-400 font-semibold">{parseFloat(bet.total_odds).toFixed(2)}</span></span>
                  {bet.payout && (
                    <span className={`font-semibold ${bet.status === 'won' ? 'text-green-400' : bet.status === 'cashed_out' ? 'text-blue-400' : 'text-red-400'}`}>
                      Payout: {parseFloat(bet.payout).toFixed(2)} BP
                    </span>
                  )}
                </div>
              </div>

              {expandedBetId === bet.id && bet.selections && bet.selections.length > 0 && (
                <div className="border-t border-gray-800 bg-black/40 p-4 space-y-2">
                  <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">Selecciones</p>
                  {bet.selections.map((sel, idx) => (
                    <div key={idx} className="flex items-start gap-3 bg-[#111] border border-gray-800 rounded-lg p-3">
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
                        <p className="text-[10px] text-gray-600 mt-0.5">{sel.market_name}</p>
                      </div>
                      <div className="text-right flex-shrink-0">
                        <span className="text-sm font-bold text-primary-400">{parseFloat(sel.odds_at_time).toFixed(2)}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
      <p className="text-[9px] text-gray-600 mt-4 text-center">
        Juega con responsabilidad. El juego en exceso puede causar adicción.
      </p>
    </div>
  )
}
