import { useState, useEffect, useRef } from 'react'
import { useAuth } from '../../context/AuthContext'
import { X } from 'lucide-react'

interface RegisterModalProps {
  onClose: () => void
  onLoginClick: () => void
}

export default function RegisterModal({ onClose, onLoginClick }: RegisterModalProps) {
  const [form, setForm] = useState({
    username: '',
    email: '',
    password: '',
    dni: '',
    fecha_nacimiento: '',
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [isAdult, setIsAdult] = useState(false)
  const { register } = useAuth()
  const overlayRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    document.body.style.overflow = 'hidden'
    return () => { document.body.style.overflow = '' }
  }, [])

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm({ ...form, [e.target.name]: e.target.value })
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (!/^\d{8}$/.test(form.dni)) {
      setError('El DNI debe tener exactamente 8 digitos')
      return
    }

    setLoading(true)
    try {
      await register(form)
      onClose()
    } catch (err: any) {
      if (err.response?.data) {
        const data = err.response.data
        if (typeof data === 'string') {
          setError(data)
        } else if (data.message) {
          setError(data.message)
        } else {
          const messages = Object.entries(data).flatMap(([, msgs]) =>
            Array.isArray(msgs) ? msgs : [msgs]
          )
          setError(messages.join('. ') || 'Error al registrar usuario')
        }
      } else {
        setError('Error al conectar con el servidor')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      ref={overlayRef}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm"
      onClick={(e) => { if (e.target === overlayRef.current) onClose() }}
    >
      <div className="bg-[#1a1a1a] border border-gray-800 rounded-2xl p-8 w-full max-w-md mx-4 shadow-2xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-6">
          <div>
            <img src="/LOGO.PNG" alt="FairBet" className="h-6 w-auto mb-3" />
            <h2 className="text-xl font-bold">Crear Cuenta</h2>
          </div>
          <button onClick={onClose} className="text-gray-500 hover:text-white transition">
            <X className="w-5 h-5" />
          </button>
        </div>

        {error && (
          <div className="bg-red-900/30 border border-red-800 text-red-400 px-4 py-2 rounded-lg mb-4 text-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm text-gray-400 mb-1.5">Usuario</label>
            <input
              type="text"
              name="username"
              value={form.username}
              onChange={handleChange}
              className="w-full bg-[#0a0a0a] border border-gray-700 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-primary-500 transition"
              required
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1.5">Email</label>
            <input
              type="email"
              name="email"
              value={form.email}
              onChange={handleChange}
              className="w-full bg-[#0a0a0a] border border-gray-700 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-primary-500 transition"
              required
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1.5">Contrasena</label>
            <input
              type="password"
              name="password"
              value={form.password}
              onChange={handleChange}
              className="w-full bg-[#0a0a0a] border border-gray-700 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-primary-500 transition"
              required
              minLength={8}
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1.5">DNI</label>
            <input
              type="text"
              name="dni"
              value={form.dni}
              onChange={(e) => {
                const val = e.target.value.replace(/\D/g, '')
                setForm({ ...form, dni: val })
              }}
              maxLength={8}
              inputMode="numeric"
              className="w-full bg-[#0a0a0a] border border-gray-700 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-primary-500 transition"
              required
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1.5">Fecha de Nacimiento</label>
            <input
              type="date"
              name="fecha_nacimiento"
              value={form.fecha_nacimiento}
              onChange={handleChange}
              className="w-full bg-[#0a0a0a] border border-gray-700 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:border-primary-500 transition"
              required
            />
          </div>
          <label className="flex items-start gap-2 text-xs text-gray-400 mt-1 cursor-pointer">
            <input
              type="checkbox"
              checked={isAdult}
              onChange={(e) => setIsAdult(e.target.checked)}
              className="mt-0.5 accent-primary-500"
            />
            <span>
              Declaro ser mayor de 18 años y acepto los{' '}
              <a href="#" className="text-primary-400 underline">Términos y Condiciones</a>
            </span>
          </label>
          <button
            type="submit"
            disabled={loading || !isAdult}
            className="w-full bg-primary-500 hover:bg-primary-400 disabled:opacity-50 text-black font-semibold py-2.5 rounded-lg transition"
          >
            {loading ? 'Registrando...' : 'Registrarse'}
          </button>
        </form>

        <p className="mt-5 text-center text-sm text-gray-500">
          Ya tienes cuenta?{' '}
          <button onClick={onLoginClick} className="text-primary-500 hover:text-primary-400 font-medium transition">
            Iniciar Sesion
          </button>
        </p>
      </div>
    </div>
  )
}
