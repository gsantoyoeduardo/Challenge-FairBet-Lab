import { useEffect, useState } from 'react'
import { adminEvents, type AdminEvent } from '../../services/adminEvents'
import { Loader2, Search, Eye, Play, Square, XCircle, Plus, ChevronDown, ChevronUp, Shield } from 'lucide-react'
import CreateEventModal from '../../components/admin/CreateEventModal'

export default function EventManagerPage() {
  const [events, setEvents] = useState<AdminEvent[]>([])
  const [loading, setLoading] = useState(true)
  const [sportFilter, setSportFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [changingStatus, setChangingStatus] = useState<number | null>(null)
  const [createModalOpen, setCreateModalOpen] = useState(false)
  const [mensaje, setMensaje] = useState('')
  const [exposureEventId, setExposureEventId] = useState<number | null>(null)
  const [exposureData, setExposureData] = useState<{
    selection_id: number
    selection_name: string
    odds: string
    bets_count: number
    potential_payout: string
  }[]>([])
  const [loadingExposure, setLoadingExposure] = useState(false)

  const load = () => {
    setLoading(true)
    adminEvents.list({ sport: sportFilter || undefined, status: statusFilter || undefined })
      .then(setEvents)
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [sportFilter, statusFilter])

  const handleChangeStatus = async (eventId: number, newStatus: string) => {
    setChangingStatus(eventId)
    setMensaje('')
    try {
      await adminEvents.changeStatus(eventId, newStatus)
      setMensaje(`Evento actualizado a "${newStatus}"`)
      load()
    } catch (err: any) {
      setMensaje(err.response?.data?.error || 'Error al cambiar estado')
    } finally {
      setChangingStatus(null)
    }
  }

  const toggleExposure = async (eventId: number) => {
    if (exposureEventId === eventId) {
      setExposureEventId(null)
      setExposureData([])
      return
    }
    setExposureEventId(eventId)
    setLoadingExposure(true)
    setExposureData([])
    try {
      const result = await adminEvents.getExposure(eventId)
      setExposureData(result)
    } catch {
      setExposureData([])
    } finally {
      setLoadingExposure(false)
    }
  }

  const filteredEvents = events.filter(ev => {
    if (!searchQuery) return true
    const q = searchQuery.toLowerCase()
    return ev.team_home.toLowerCase().includes(q) || ev.team_away.toLowerCase().includes(q)
  })

  const statusColors: Record<string, string> = {
    programado: 'text-blue-400 bg-blue-400/10',
    en_vivo: 'text-red-400 bg-red-400/10',
    finalizado: 'text-green-400 bg-green-400/10',
    suspendido: 'text-yellow-400 bg-yellow-400/10',
    anulado: 'text-gray-400 bg-gray-400/10',
  }

  const statusLabel: Record<string, string> = {
    programado: 'Programado',
    en_vivo: 'En Vivo',
    finalizado: 'Finalizado',
    suspendido: 'Suspendido',
    anulado: 'Anulado',
  }

  const nextActions: Record<string, { label: string; status: string; icon: any; color: string }[]> = {
    programado: [
      { label: 'En Vivo', status: 'en_vivo', icon: Play, color: 'text-red-400 hover:bg-red-400/10' },
      { label: 'Suspender', status: 'suspendido', icon: Square, color: 'text-yellow-400 hover:bg-yellow-400/10' },
    ],
    en_vivo: [
      { label: 'Finalizar', status: 'finalizado', icon: Square, color: 'text-green-400 hover:bg-green-400/10' },
    ],
    suspendido: [
      { label: 'Reactivar', status: 'programado', icon: Play, color: 'text-blue-400 hover:bg-blue-400/10' },
      { label: 'Anular', status: 'anulado', icon: XCircle, color: 'text-gray-400 hover:bg-gray-400/10' },
    ],
  }

  return (
    <div className="max-w-5xl mx-auto px-4">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold">Gestion de Eventos</h1>
        <button
          onClick={() => setCreateModalOpen(true)}
          className="flex items-center gap-2 bg-primary-600 hover:bg-primary-500 text-black font-semibold px-4 py-2 rounded-lg text-sm transition"
        >
          <Plus className="w-4 h-4" />
          Nuevo Evento
        </button>
      </div>

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
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
          <input
            type="text"
            placeholder="Buscar equipo..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-[#1a1a1a] border border-gray-800 rounded-lg pl-10 pr-4 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-primary-500"
          />
        </div>
        <select
          value={sportFilter}
          onChange={(e) => setSportFilter(e.target.value)}
          className="bg-[#1a1a1a] border border-gray-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-primary-500"
        >
          <option value="">Todos los deportes</option>
          <option value="football">Futbol</option>
          <option value="tennis">Tenis</option>
          <option value="basketball">Basketball</option>
          <option value="volleyball">Voleibol</option>
        </select>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="bg-[#1a1a1a] border border-gray-800 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-primary-500"
        >
          <option value="">Todos los estados</option>
          <option value="programado">Programados</option>
          <option value="en_vivo">En Vivo</option>
          <option value="finalizado">Finalizados</option>
          <option value="suspendido">Suspendidos</option>
        </select>
      </div>

      {loading ? (
        <div className="flex justify-center py-10">
          <Loader2 className="w-6 h-6 text-gray-500 animate-spin" />
        </div>
      ) : filteredEvents.length === 0 ? (
        <div className="text-center py-10 text-gray-500">No hay eventos</div>
      ) : (
        <div className="space-y-3">
          {filteredEvents.map((ev) => {
            const actions = nextActions[ev.status] || []
            return (
              <div key={ev.id} className="bg-[#1a1a1a] border border-gray-800 rounded-xl overflow-hidden">
                <div className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-[10px] text-gray-500 uppercase">{ev.sport_name}</span>
                        <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${statusColors[ev.status]}`}>
                          {statusLabel[ev.status]}
                        </span>
                      </div>
                      <p className="text-sm font-semibold text-white truncate">
                        {ev.team_home} vs {ev.team_away}
                      </p>
                      <p className="text-[10px] text-gray-500 mt-0.5">
                        {new Date(ev.start_time).toLocaleString([], { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })}
                        {' · '}{ev.market_count} mercados
                      </p>
                    </div>

                    <div className="flex items-center gap-2 ml-4 flex-shrink-0">
                      <a
                        href={`/admin/events/${ev.id}`}
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded text-xs text-gray-400 hover:text-white hover:bg-gray-800 transition"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        Ver
                      </a>
                      <button
                        onClick={() => toggleExposure(ev.id)}
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium transition text-orange-400 hover:bg-orange-400/10"
                      >
                        <Shield className="w-3.5 h-3.5" />
                        Exposure
                      </button>
                      {actions.map((action) => {
                        const Icon = action.icon
                        return (
                          <button
                            key={action.status}
                            onClick={() => handleChangeStatus(ev.id, action.status)}
                            disabled={changingStatus === ev.id}
                            className={`flex items-center gap-1.5 px-3 py-1.5 rounded text-xs font-medium transition disabled:opacity-50 ${action.color}`}
                          >
                            <Icon className="w-3.5 h-3.5" />
                            {action.label}
                          </button>
                        )
                      })}
                      {exposureEventId === ev.id ? (
                        <ChevronUp className="w-4 h-4 text-gray-500" />
                      ) : (
                        <ChevronDown className="w-4 h-4 text-gray-500" />
                      )}
                    </div>
                  </div>
                </div>

                {exposureEventId === ev.id && (
                  <div className="border-t border-gray-800">
                    {loadingExposure ? (
                      <div className="flex justify-center py-6">
                        <Loader2 className="w-5 h-5 text-gray-500 animate-spin" />
                      </div>
                    ) : exposureData.length > 0 ? (
                      <div className="divide-y divide-gray-800/30">
                        <div className="grid grid-cols-[1fr_80px_80px_100px] gap-2 px-4 py-2 text-[10px] text-gray-500 font-semibold bg-black/30">
                          <span>Seleccion</span>
                          <span className="text-center">Odds</span>
                          <span className="text-center">Apuestas</span>
                          <span className="text-center">Payout Pot.</span>
                        </div>
                        {exposureData.map((sel) => (
                          <div key={sel.selection_id} className="grid grid-cols-[1fr_80px_80px_100px] gap-2 px-4 py-2.5 items-center text-xs">
                            <span className="text-gray-300">{sel.selection_name}</span>
                            <span className="text-center text-primary-400">{parseFloat(sel.odds).toFixed(2)}</span>
                            <span className="text-center text-gray-400">{sel.bets_count}</span>
                            <span className="text-center text-red-400 font-semibold">{parseFloat(sel.potential_payout).toFixed(2)} BP</span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-gray-500 text-center py-6 text-xs">Sin apuestas activas en este evento</p>
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}

      {createModalOpen && (
        <CreateEventModal
          onClose={() => setCreateModalOpen(false)}
          onCreated={() => { setCreateModalOpen(false); load() }}
        />
      )}
    </div>
  )
}
