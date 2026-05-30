import { useEffect, useState } from 'react'
import { operator, type OperatorMetrics } from '../services/operator'
import AdminMetrics from '../components/admin/AdminMetrics'
import { useAuth } from '../context/AuthContext'

export default function AdminDashboardPage() {
  const { user } = useAuth()
  const [metrics, setMetrics] = useState<OperatorMetrics | null>(null)

  useEffect(() => {
    operator.getMetrics().then(setMetrics).catch(() => {})
  }, [])

  if (!user) return <div className="text-gray-500 text-center py-20">Acceso restringido</div>

  return (
    <div className="max-w-5xl mx-auto px-4">
      <h1 className="text-xl font-bold mb-6">Dashboard Operador</h1>

      <div className="space-y-6">
        <AdminMetrics metrics={metrics} />
      </div>
    </div>
  )
}
