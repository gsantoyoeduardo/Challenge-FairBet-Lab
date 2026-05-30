import { useState } from 'react'
import { operator } from '../services/operator'
import { Download } from 'lucide-react'

export default function ReportsPage() {
  const now = new Date()
  const [mes, setMes] = useState(now.getMonth() + 1)
  const [anio, setAnio] = useState(now.getFullYear())

  const handleDownload = async () => {
    const blob = await operator.downloadReport(mes, anio)
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `reporte_${anio}_${String(mes).padStart(2, '0')}.csv`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const meses = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']

  return (
    <div className="max-w-xl mx-auto px-4">
      <h1 className="text-xl font-bold mb-6">Reportes MINCETUR</h1>

      <div className="bg-[#1a1a1a] border border-gray-800 rounded-xl p-6">
        <p className="text-xs text-gray-500 mb-6">
          Descarga el reporte mensual de apuestas en formato CSV para cumplimiento regulatorio.
          Incluye: fecha, usuario, tipo de apuesta, stake, payout, resultado, evento y mercado.
        </p>

        <div className="grid grid-cols-2 gap-4 mb-6">
          <div>
            <label className="block text-xs text-gray-400 mb-1.5">Mes</label>
            <select
              value={mes}
              onChange={(e) => setMes(Number(e.target.value))}
              className="w-full bg-black border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary-500"
            >
              {meses.map((m, i) => (
                <option key={i} value={i + 1}>{m}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1.5">Año</label>
            <input
              type="number"
              value={anio}
              onChange={(e) => setAnio(Number(e.target.value))}
              className="w-full bg-black border border-gray-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-primary-500"
            />
          </div>
        </div>

        <button
          onClick={handleDownload}
          className="w-full bg-primary-500 hover:bg-primary-400 text-black font-bold py-3 rounded-lg transition text-sm flex items-center justify-center gap-2"
        >
          <Download className="w-4 h-4" />
          Descargar CSV
        </button>
      </div>
    </div>
  )
}
