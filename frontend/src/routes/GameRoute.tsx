import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function GameRoute() {
  const { user, loading, isAdminMode } = useAuth()

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-dark-950">
        <div className="text-primary-500 text-xl">Cargando...</div>
      </div>
    )
  }

  if (!user) {
    return <Navigate to="/" replace />
  }

  if (user.is_staff && isAdminMode) {
    return <Navigate to="/admin" replace />
  }

  return <Outlet />
}
