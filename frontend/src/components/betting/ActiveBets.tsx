import { useEffect, useState } from 'react'
import { Loader2 } from 'lucide-react'
import { betting, type Bet } from '../../services/betting'
import { useBalanceStore } from '../../store/balanceStore'
import { wallet as walletService } from '../../services/auth'

export default function ActiveBets() {
  const [bets, setBets] = useState<Bet[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('')
  const [cashingOut, setCashingOut] = useState<number | null>(null)
  const [mensaje, setMensaje] = useState('')
  const { setBalance } = useBalanceStore()

  const load = () => {
    setLoading(true)
    betting.misApuestas(filter ? { status: filter } : undefined)
      .then(setBets)
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [filter])

  const handleCashOut = async (betId: number) => {
    setMensaje('')
    setCashingOut(betId)
    try {
      await betting.cashOut(betId, {})
      walletService.getBalance().then((d) => setBalance(parseFloat(d.balance)))
      setMensaje(`Cash-out de apuesta #${betId} realizado`)
      load()
    } catch (err: any) {
      setMensaje(err.response?.data?.error || 'Error al hacer cash-out')
    } finally {
      setCashingOut(null)
    }
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
    <div>
      <div className="flex gap-1 mb-4 flex-wrap">
        {['', 'accepted', 'won', 'lost', 'cashed_out'].map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-2.5 py-1 rounded text-[10px] font-medium transition ${
              filter === f
                ? 'bg-primary-500 text-black'
                : 'bg-black border border-gray-700 text-gray-400 hover:text-white'
            }`}
          >
            {f === '' ? 'Todas' : f === 'accepted' ? 'Activas' : f === 'won' ? 'Gan.' : f === 'lost' ? 'Perd.' : 'C-out'}
          </button>
        ))}
      </div>

      {mensaje && (
        <div className="bg-green-900/20 border border-green-800 text-green-400 px-3 py-2 rounded-lg text-[10px] mb-2">
          {mensaje}
        </div>
      )}

      {loading ? (
        <div className="flex justify-center py-8"><Loader2 className="w-5 h-5 text-gray-500 animate-spin" /></div>
      ) : bets.length === 0 ? (
        <p className="text-xs text-gray-500 text-center py-8">No tienes apuestas</p>
      ) : (
        <div className="space-y-2 max-h-[500px] overflow-y-auto">
          {bets.map((bet) => (
            <div key={bet.id} className="bg-black border border-gray-800 rounded-lg p-3">
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-[10px] text-gray-500">
                  #{bet.id} - {new Date(bet.placed_at).toLocaleDateString()}
                </span>
                <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${statusColors[bet.status] || 'text-gray-400 bg-gray-400/10'}`}>
                  {statusLabel[bet.status] || bet.status}
                </span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-400">
                  Stake: <span className="text-white font-semibold">{parseFloat(bet.stake).toFixed(2)}</span>
                </span>
                <span className="text-primary-400 font-semibold">x{parseFloat(bet.total_odds).toFixed(2)}</span>
              </div>
              {bet.payout && (
                <div className="mt-1 text-xs">
                  <span className={`font-semibold ${bet.status === 'won' ? 'text-green-400' : bet.status === 'cashed_out' ? 'text-blue-400' : 'text-red-400'}`}>
                    Payout: {parseFloat(bet.payout).toFixed(2)} BP
                  </span>
                </div>
              )}
              {bet.status === 'accepted' && (
                <button
                  onClick={() => handleCashOut(bet.id)}
                  disabled={cashingOut === bet.id}
                  className="w-full mt-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white font-semibold py-1.5 rounded text-[10px] transition"
                >
                  {cashingOut === bet.id ? 'Procesando...' : 'Cash-out'}
                </button>
              )}
            </div>
          ))}
        </div>
      )}
      <p className="text-[9px] text-gray-600 mt-2 text-center">
        Juega con responsabilidad. El juego en exceso puede causar adicción.
      </p>
    </div>
  )
}
