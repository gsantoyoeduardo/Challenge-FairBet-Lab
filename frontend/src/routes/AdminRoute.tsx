import { useEffect, useRef } from 'react'
import { Navigate, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function AdminRoute() {
  const { user, loading, isAdminMode } = useAuth()
  const navigate = useNavigate()
  const prevAdminModeRef = useRef(isAdminMode)

  useEffect(() => {
    if (!loading && user?.is_staff && !isAdminMode && prevAdminModeRef.current) {
      navigate('/', { replace: true })
    }
    prevAdminModeRef.current = isAdminMode
  }, [isAdminMode, loading, user?.is_staff, navigate])

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
