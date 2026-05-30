import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { adminEvents, type AdminEventDetail } from '../../services/adminEvents'
import { ArrowLeft, CheckCircle, XCircle, Loader2, Square } from 'lucide-react'

export default function EventDetailAdminPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [event, setEvent] = useState<AdminEventDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [processing, setProcessing] = useState<number | null>(null)
  const [mensaje, setMensaje] = useState('')

  const load = () => {
    if (!id) return
    setLoading(true)
    adminEvents.detail(Number(id))
      .then(setEvent)
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [id])

  const handleSetWinner = async (selectionId: number, isWinner: boolean) => {
    setProcessing(selectionId)
    setMensaje('')
    try {
      await adminEvents.setSelectionWinner(selectionId, isWinner)
      setMensaje(`Seleccion marcada como ${isWinner ? 'ganadora' : 'perdedora'}`)
      load()
    } catch (err: any) {
      setMensaje(err.response?.data?.error || 'Error')
    } finally {
      setProcessing(null)
    }
  }

  const handleSuspendMarket = async (marketId: number) => {
    setProcessing(marketId)
    setMensaje('')
    try {
      await adminEvents.suspendMarket(marketId, 60)
      setMensaje('Mercado suspendido por 60 segundos')
      load()
    } catch (err: any) {
      setMensaje(err.response?.data?.error || 'Error')
    } finally {
      setProcessing(null)
    }
  }

  if (loading) {
    return (
      <div className="max-w-5xl mx-auto px-4 flex justify-center py-10">
        <Loader2 className="w-6 h-6 text-gray-500 animate-spin" />
      </div>
    )
  }

  if (!event) {
    return (
      <div className="max-w-5xl mx-auto px-4 text-center py-10 text-gray-500">
        Evento no encontrado
      </div>
    )
  }

  const statusColors: Record<string, string> = {
    programado: 'text-blue-400 bg-blue-400/10',
    en_vivo: 'text-red-400 bg-red-400/10',
    finalizado: 'text-green-400 bg-green-400/10',
    suspendido: 'text-yellow-400 bg-yellow-400/10',
    anulado: 'text-gray-400 bg-gray-400/10',
  }

  return (
    <div className="max-w-5xl mx-auto px-4">
      <button
        onClick={() => navigate('/admin/events')}
        className="flex items-center gap-1.5 text-xs text-gray-400 hover:text-white transition mb-4"
      >
        <ArrowLeft className="w-3.5 h-3.5" />
        Volver a Eventos
      </button>

      {mensaje && (
        <div className={`border rounded-lg px-4 py-3 mb-4 text-sm ${
          mensaje.startsWith('Error')
            ? 'bg-red-900/20 border-red-800 text-red-400'
            : 'bg-green-900/20 border-green-800 text-green-400'
        }`}>
          {mensaje}
        </div>
      )}

      <div className="bg-[#1a1a1a] border border-gray-800 rounded-xl px-4 py-3 mb-6">
        <div className="flex items-center justify-between mb-1">
          <span className="text-[10px] text-gray-500 uppercase">
            {event.sport.name} · {new Date(event.start_time).toLocaleString([], { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })}
          </span>
          <span className={`text-[10px] px-2 py-0.5 rounded font-medium ${statusColors[event.status]}`}>
            {event.status === 'en_vivo' ? 'EN VIVO' : event.status}
          </span>
        </div>
        <p className="text-sm font-bold tracking-tight">
          {event.team_home} <span className="text-gray-600 mx-1.5">vs</span> {event.team_away}
        </p>
      </div>

      <div className="space-y-4">
        {event.markets.map((market) => (
          <div key={market.id} className="bg-[#1a1a1a] border border-gray-800 rounded-xl overflow-hidden">
            <div className="flex items-center justify-between px-4 py-3 border-b border-gray-800/50">
              <div>
                <span className="text-xs font-semibold text-white">{market.name}</span>
                <span className="text-[10px] text-gray-500 ml-2">({market.type})</span>
              </div>
              <button
                onClick={() => handleSuspendMarket(market.id)}
                disabled={processing === market.id}
                className="flex items-center gap-1.5 text-[10px] text-gray-400 hover:text-yellow-400 transition disabled:opacity-50"
              >
                <Square className="w-3 h-3" />
                Suspender
              </button>
            </div>

            <div className="divide-y divide-gray-800/30">
              {market.selections.map((sel) => (
                <div key={sel.id} className="px-4 py-3 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className="text-sm text-white">{sel.name}</span>
                    <span className="text-sm font-bold text-primary-400">{parseFloat(sel.odds).toFixed(2)}</span>
                    {sel.is_winner !== null && (
                      <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${
                        sel.is_winner ? 'text-green-400 bg-green-400/10' : 'text-red-400 bg-red-400/10'
                      }`}>
                        {sel.is_winner ? 'Ganadora' : 'Perdedora'}
                      </span>
                    )}
                  </div>
                  {sel.is_winner === null && (
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleSetWinner(sel.id, true)}
                        disabled={processing === sel.id}
                        className="flex items-center gap-1.5 text-[10px] text-green-400 hover:bg-green-400/10 px-2 py-1 rounded transition disabled:opacity-50"
                      >
                        <CheckCircle className="w-3 h-3" />
                        Ganadora
                      </button>
                      <button
                        onClick={() => handleSetWinner(sel.id, false)}
                        disabled={processing === sel.id}
                        className="flex items-center gap-1.5 text-[10px] text-red-400 hover:bg-red-400/10 px-2 py-1 rounded transition disabled:opacity-50"
                      >
                        <XCircle className="w-3 h-3" />
                        Perdedora
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
