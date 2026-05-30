import { useState } from 'react'
import { X, Loader2 } from 'lucide-react'
import { adminEvents } from '../../services/adminEvents'

interface CreateEventModalProps {
  onClose: () => void
  onCreated: () => void
}

export default function CreateEventModal({ onClose, onCreated }: CreateEventModalProps) {
  const [sportSlug, setSportSlug] = useState('football')
  const [teamHome, setTeamHome] = useState('')
  const [teamAway, setTeamAway] = useState('')
  const [startTime, setStartTime] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    if (!teamHome.trim() || !teamAway.trim() || !startTime) {
      setError('Todos los campos son requeridos')
      return
    }
    setLoading(true)
    try {
      await adminEvents.create({
        sport_slug: sportSlug,
        team_home: teamHome.trim(),
        team_away: teamAway.trim(),
        start_time: startTime,
      })
      onCreated()
    } catch (err: any) {
      setError(err.response?.data?.error || 'Error al crear evento')
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm" onClick={onClose} />
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div className="bg-[#1a1a1a] border border-gray-800 rounded-xl w-full max-w-md overflow-hidden">
          <div className="flex items-center justify-between p-5 border-b border-gray-800">
            <h2 className="text-lg font-bold">Nuevo Evento</h2>
            <button onClick={onClose} className="text-gray-500 hover:text-white transition">
              <X className="w-5 h-5" />
            </button>
          </div>

          <form onSubmit={handleSubmit} className="p-5 space-y-4">
            {error && (
              <div className="bg-red-900/20 border border-red-800 text-red-400 px-3 py-2 rounded-lg text-xs">
                {error}
              </div>
            )}

            <div>
              <label className="block text-xs text-gray-400 mb-1">Deporte</label>
              <select
                value={sportSlug}
                onChange={(e) => setSportSlug(e.target.value)}
                className="w-full bg-black border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-primary-500"
              >
                <option value="football">Futbol</option>
                <option value="tennis">Tenis</option>
                <option value="basketball">Basketball</option>
                <option value="volleyball">Voleibol</option>
              </select>
            </div>

            <div>
              <label className="block text-xs text-gray-400 mb-1">Equipo Local</label>
              <input
                type="text"
                value={teamHome}
                onChange={(e) => setTeamHome(e.target.value)}
                placeholder="Ej: Alianza Lima"
                className="w-full bg-black border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-primary-500"
              />
            </div>

            <div>
              <label className="block text-xs text-gray-400 mb-1">Equipo Visitante</label>
              <input
                type="text"
                value={teamAway}
                onChange={(e) => setTeamAway(e.target.value)}
                placeholder="Ej: Universitario"
                className="w-full bg-black border border-gray-700 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-primary-500"
              />
            </div>

            <div>
              <label className="block text-xs text-gray-400 mb-1">Fecha y Hora</label>
              <input
                type="datetime-local"
                value={startTime}
                onChange={(e) => setStartTime(e.target.value)}
                className="w-full bg-black border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-primary-500"
              />
            </div>

            <div className="flex gap-3 pt-2">
              <button
                type="button"
                onClick={onClose}
                className="flex-1 bg-black border border-gray-700 text-gray-300 font-semibold px-4 py-2 rounded-lg text-sm hover:bg-gray-800 transition"
              >
                Cancelar
              </button>
              <button
                type="submit"
                disabled={loading}
                className="flex-1 bg-primary-600 hover:bg-primary-500 disabled:opacity-50 text-black font-semibold px-4 py-2 rounded-lg text-sm transition flex items-center justify-center gap-2"
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Crear'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </>
  )
}
