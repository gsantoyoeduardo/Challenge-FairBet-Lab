import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function AdminRoute() {
  const { user, loading, isAdminMode } = useAuth()
  const location = useLocation()

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-dark-950">
        <div className="text-primary-500 text-xl">Cargando...</div>
      </div>
    )
  }

  if (!user || !user.is_staff) {
    return <Navigate to="/" replace />
  }

  if (!isAdminMode) {
    return <Navigate to="/" replace />
  }

  return <Outlet />
}
