import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { useBalanceStore } from '../../store/balanceStore'
import { wallet as walletService } from '../../services/auth'
import {
  X, Wallet, Bell, ArrowDownToLine, ArrowUpFromLine,
  User, Clock, Gift, Settings, LogOut, Shield, Gamepad2
} from 'lucide-react'
import WithdrawModal from '../wallet/WithdrawModal'

interface UserPanelProps {
  onClose: () => void
  onDeposit: () => void
}

export default function UserPanel({ onClose, onDeposit }: UserPanelProps) {
  const navigate = useNavigate()
  const { user, logout, isAdminMode, enableAdminMode, disableAdminMode } = useAuth()
  const { balance, setBalance, bonusBalance, setBonusBalance } = useBalanceStore()
  const [withdrawOpen, setWithdrawOpen] = useState(false)
  const panelRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    document.body.style.overflow = 'hidden'
    return () => { document.body.style.overflow = '' }
  }, [])

  useEffect(() => {
    if (user) {
      walletService.getBalance().then((data) => setBalance(parseFloat(data.balance)))
      walletService.getBonusBalance().then((data) => setBonusBalance(parseFloat(data.balance)))
    }
  }, [user, setBalance, setBonusBalance])

  const handleLogout = () => {
    logout()
    onClose()
  }

  return (
    <>
      <div
        className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      />
      <div
        ref={panelRef}
        className="fixed right-0 top-0 h-full w-80 bg-[#111] border-l border-gray-800 z-50 shadow-2xl flex flex-col animate-slide-in"
      >
        <div className="flex items-center justify-between p-5 border-b border-gray-800">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-primary-600 flex items-center justify-center">
              <User className="w-5 h-5 text-black" />
            </div>
            <div>
              <p className="font-semibold text-sm">{user?.username}</p>
              <p className="text-xs text-gray-500">{user?.email}</p>
            </div>
          </div>
          <button onClick={onClose} className="text-gray-500 hover:text-white transition">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-5 border-b border-gray-800 space-y-3">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Wallet className="w-4 h-4 text-white" />
              <span className="text-xs text-gray-500 uppercase tracking-wide">Saldo Real</span>
            </div>
            <p className="text-xl font-bold text-white">{balance.toFixed(4)} BP</p>
          </div>
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Gift className="w-4 h-4 text-primary-500" />
              <span className="text-xs text-gray-500 uppercase tracking-wide">Saldo Bono</span>
            </div>
            <p className="text-lg font-semibold text-primary-400">{bonusBalance.toFixed(4)} BP</p>
          </div>
          <div className="border-t border-gray-800 pt-2 flex justify-between items-center">
            <span className="text-xs text-gray-500 uppercase">Total</span>
            <span className="text-sm font-bold text-green-400">{(balance + bonusBalance).toFixed(4)} BP</span>
          </div>
        </div>

        {user?.is_staff && (
          <div className="p-3 border-b border-gray-800">
            <button
              onClick={() => {
                if (isAdminMode) {
                  disableAdminMode()
                  navigate('/')
                } else {
                  enableAdminMode()
                  navigate('/admin')
                }
                onClose()
              }}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition text-sm ${
                isAdminMode
                  ? 'bg-primary-600/10 text-primary-400 hover:bg-primary-600/20'
                  : 'bg-gray-800/50 text-gray-300 hover:bg-gray-800'
              }`}
            >
              {isAdminMode ? (
                <>
                  <Gamepad2 className="w-4 h-4" />
                  Cambiar a Modo Juego
                </>
              ) : (
                <>
                  <Shield className="w-4 h-4" />
                  Cambiar a Modo Admin
                </>
              )}
            </button>
          </div>
        )}

        <div className="flex-1 overflow-y-auto p-3">
          <button className="w-full flex items-center gap-3 px-4 py-3 rounded-lg hover:bg-[#1a1a1a] transition text-sm text-gray-300">
            <Bell className="w-4 h-4 text-gray-500" />
            Notificaciones
          </button>
          <button
            onClick={() => { onClose(); onDeposit() }}
            className="w-full flex items-center gap-3 px-4 py-3 rounded-lg hover:bg-[#1a1a1a] transition text-sm text-gray-300"
          >
            <ArrowDownToLine className="w-4 h-4 text-primary-500" />
            Depositar
          </button>
          <button
            onClick={() => setWithdrawOpen(true)}
            className="w-full flex items-center gap-3 px-4 py-3 rounded-lg hover:bg-[#1a1a1a] transition text-sm text-gray-300"
          >
            <ArrowUpFromLine className="w-4 h-4 text-orange-500" />
            Retirar
          </button>
          <button
            onClick={() => { onClose(); navigate('/bonuses') }}
            className="w-full flex items-center gap-3 px-4 py-3 rounded-lg hover:bg-[#1a1a1a] transition text-sm text-gray-300"
          >
            <Gift className="w-4 h-4 text-primary-500" />
            Bonos
          </button>
          <button
            onClick={() => { onClose(); navigate('/profile') }}
            className="w-full flex items-center gap-3 px-4 py-3 rounded-lg hover:bg-[#1a1a1a] transition text-sm text-gray-300"
          >
            <User className="w-4 h-4 text-gray-500" />
            Mi Perfil
          </button>
          <button
            onClick={() => { onClose(); navigate('/my-bets') }}
            className="w-full flex items-center gap-3 px-4 py-3 rounded-lg hover:bg-[#1a1a1a] transition text-sm text-gray-300"
          >
            <Clock className="w-4 h-4 text-gray-500" />
            Historial
          </button>
          <button
            onClick={() => { onClose(); navigate('/profile') }}
            className="w-full flex items-center gap-3 px-4 py-3 rounded-lg hover:bg-[#1a1a1a] transition text-sm text-gray-300"
          >
            <Settings className="w-4 h-4 text-gray-500" />
            Control
          </button>
        </div>

        <div className="p-3 border-t border-gray-800">
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-4 py-3 rounded-lg hover:bg-red-900/20 transition text-sm text-red-400"
          >
            <LogOut className="w-4 h-4" />
            Cerrar Sesion
          </button>
        </div>
      </div>

      {withdrawOpen && (
        <WithdrawModal onClose={() => setWithdrawOpen(false)} />
      )}
    </>
  )
}
