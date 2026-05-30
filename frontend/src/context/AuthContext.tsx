import { createContext, useContext, useState, useEffect, type ReactNode } from 'react'
import { auth } from '../services/auth'
import type { User } from '../types'
import { useBalanceStore } from '../store/balanceStore'

interface AuthContextType {
  user: User | null
  loading: boolean
  isAdminMode: boolean
  enableAdminMode: () => void
  disableAdminMode: () => void
  login: (username: string, password: string) => Promise<void>
  register: (data: { username: string; email: string; password: string; dni: string; fecha_nacimiento: string }) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [isAdminMode, setIsAdminMode] = useState(false)

  useEffect(() => {
    const token = localStorage.getItem('access_token')
    if (token) {
      auth.getMe()
        .then((fetchedUser) => {
          setUser(fetchedUser)
          if (fetchedUser.is_staff) {
            const savedMode = localStorage.getItem('admin_mode')
            setIsAdminMode(savedMode === 'true')
          }
        })
        .catch(() => localStorage.removeItem('access_token'))
        .finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [])

  const login = async (username: string, password: string) => {
    const data = await auth.login(username, password)
    localStorage.setItem('access_token', data.access)
    localStorage.setItem('refresh_token', data.refresh)
    setUser(data.user)
    if (data.user.is_staff) {
      setIsAdminMode(true)
      localStorage.setItem('admin_mode', 'true')
    }
  }

  const register = async (data: { username: string; email: string; password: string; dni: string; fecha_nacimiento: string }) => {
    useBalanceStore.getState().setBalance(0)
    useBalanceStore.getState().setBonusBalance(0)
    const result = await auth.register(data)
    localStorage.setItem('access_token', result.access)
    localStorage.setItem('refresh_token', result.refresh)
    setUser(result.user)
  }

  const logout = () => {
    auth.logout()
    localStorage.removeItem('admin_mode')
    useBalanceStore.getState().setBalance(0)
    useBalanceStore.getState().setBonusBalance(0)
    setUser(null)
    setIsAdminMode(false)
  }

  const enableAdminMode = () => {
    setIsAdminMode(true)
    localStorage.setItem('admin_mode', 'true')
  }

  const disableAdminMode = () => {
    setIsAdminMode(false)
    localStorage.setItem('admin_mode', 'false')
  }

  return (
    <AuthContext.Provider value={{ user, loading, isAdminMode, enableAdminMode, disableAdminMode, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
