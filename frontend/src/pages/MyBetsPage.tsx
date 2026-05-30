import { useEffect, useState } from 'react'
import { betting, type Bet } from '../services/betting'

export default function MyBetsPage() {
  const [bets, setBets] = useState<Bet[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('')

  useEffect(() => {
    betting.misApuestas(filter ? { status: filter } : undefined)
      .then(setBets)
      .finally(() => setLoading(false))
  }, [filter])

  const statusColors: Record<string, string> = {
    accepted: 'text-yellow-400 bg-yellow-400/10',
    won: 'text-green-400 bg-green-400/10',
    lost: 'text-red-400 bg-red-400/10',
    cashed_out: 'text-blue-400 bg-blue-400/10',
    cancelled: 'text-gray-400 bg-gray-400/10',
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
            <div key={bet.id} className="bg-[#1a1a1a] border border-gray-800 rounded-xl p-4">
              <div className="flex items-center justify-between mb-2">
                <div>
                  <span className="text-xs text-gray-500">
                    #{bet.id} - {new Date(bet.placed_at).toLocaleDateString()}
                  </span>
                </div>
                <span className={`text-xs px-2 py-0.5 rounded font-medium ${statusColors[bet.status]}`}>
                  {bet.status === 'accepted' ? 'Activa' : bet.status === 'won' ? 'Ganada' : bet.status === 'lost' ? 'Perdida' : bet.status === 'cashed_out' ? 'Cash-out' : bet.status}
                </span>
              </div>
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
          ))}
        </div>
      )}
      <p className="text-[9px] text-gray-600 mt-4 text-center">
        Juega con responsabilidad. El juego en exceso puede causar adicción.
      </p>
    </div>
  )
}
