import { useState } from 'react'
import { useAuth } from '../../context/AuthContext'
import { useBalanceStore } from '../../store/balanceStore'
import { wallet as walletService } from '../../services/auth'
import { Wallet, User, ChevronDown, Menu, X, Shield } from 'lucide-react'
import { useEffect } from 'react'
import LoginModal from '../auth/LoginModal'
import RegisterModal from '../auth/RegisterModal'
import UserPanel from '../user/UserPanel'
import DepositModal from '../wallet/DepositModal'

export default function AppBar() {
  const { user, isAdminMode } = useAuth()
  const { balance, setBalance, bonusBalance, setBonusBalance } = useBalanceStore()

  const [loginOpen, setLoginOpen] = useState(false)
  const [registerOpen, setRegisterOpen] = useState(false)
  const [userPanelOpen, setUserPanelOpen] = useState(false)
  const [depositOpen, setDepositOpen] = useState(false)
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  useEffect(() => {
    if (user) {
      walletService.getBalance().then((data) => setBalance(parseFloat(data.balance)))
      walletService.getBonusBalance().then((data) => setBonusBalance(parseFloat(data.balance)))
    } else {
      setBalance(0)
      setBonusBalance(0)
    }
  }, [user, setBalance, setBonusBalance])

  const openRegister = () => {
    setLoginOpen(false)
    setRegisterOpen(true)
  }

  const openLogin = () => {
    setRegisterOpen(false)
    setLoginOpen(true)
  }

  return (
    <>
      <header className="bg-[#000000] border-b border-gray-800 sticky top-0 z-40">
        <div className="mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-8">
            <a href="/" className="flex items-center gap-2 flex-shrink-0">
              <img src="/LOGO.PNG" alt="FairBet" className="h-12 w-auto" />
            </a>
            {isAdminMode && (
              <nav className="hidden lg:flex gap-1">
                <a href="/admin" className="px-3 py-2 text-sm text-gray-300 hover:text-primary-400 transition rounded-lg">
                  Inicio
                </a>
                <a href="/admin/bets" className="px-3 py-2 text-sm text-gray-300 hover:text-primary-400 transition rounded-lg">
                  Apuestas
                </a>
                <a href="/admin/reports" className="px-3 py-2 text-sm text-gray-300 hover:text-primary-400 transition rounded-lg">
                  Reportes
                </a>
              </nav>
            )}
            {!isAdminMode && (
            <nav className="hidden lg:flex gap-1">
              <a href="/betting" className="px-3 py-2 text-sm text-gray-300 hover:text-primary-400 transition rounded-lg">
                Apuesta Deportiva
              </a>
              <a href="/live" className="px-3 py-2 text-sm text-gray-300 hover:text-primary-400 transition rounded-lg">
                Apuestas en Vivo
              </a>
              <a href="/about" className="px-3 py-2 text-sm text-gray-300 hover:text-primary-400 transition rounded-lg">
                Acerca de Nosotros
              </a>
              <a href="/help" className="px-3 py-2 text-sm text-gray-300 hover:text-primary-400 transition rounded-lg">
                Ayuda
              </a>
            </nav>
            )}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="lg:hidden text-gray-400 hover:text-white transition"
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>

          <div className="flex items-center gap-3">
            {user ? (
              <>
                {!isAdminMode && (
                  <>
                    <div className="flex items-center gap-2 bg-[#1a1a1a] px-4 py-2 rounded-lg border border-gray-800">
                      <Wallet className="w-4 h-4 text-primary-500" />
                      <span className="font-semibold text-primary-400 text-sm">
                        {(balance + bonusBalance).toFixed(4)} BP
                      </span>
                    </div>
                    <button
                      onClick={() => setDepositOpen(true)}
                      className="bg-primary-600 hover:bg-primary-700 text-black font-semibold px-4 py-2 rounded-lg text-sm transition"
                    >
                      + Depositar
                    </button>
                  </>
                )}
                <button
                  onClick={() => setUserPanelOpen(true)}
                  className="flex items-center gap-2 bg-[#1a1a1a] hover:bg-[#252525] px-3 py-2 rounded-lg border border-gray-800 transition"
                >
                  <div className="w-7 h-7 rounded-full bg-primary-600 flex items-center justify-center">
                    <User className="w-4 h-4 text-black" />
                  </div>
                  <span className="text-sm text-gray-300 hidden sm:block">{user.username}</span>
                  <ChevronDown className="w-4 h-4 text-gray-500" />
                </button>
              </>
            ) : (
              <>
                <button
                  onClick={() => setLoginOpen(true)}
                  className="text-sm text-gray-300 hover:text-white px-4 py-2 transition"
                >
                  Ingresar
                </button>
                <button
                  onClick={() => setRegisterOpen(true)}
                  className="bg-primary-500 hover:bg-primary-400 text-black font-semibold px-5 py-2 rounded-lg text-sm transition"
                >
                  Registrarse
                </button>
              </>
            )}
          </div>
        </div>
      </header>

      {mobileMenuOpen && (
        <div className="lg:hidden bg-black border-b border-gray-800 px-4 py-3 space-y-1">
          {isAdminMode ? (
            <>
              <a href="/admin" onClick={() => setMobileMenuOpen(false)} className="block px-3 py-2 text-sm text-gray-300 hover:text-primary-400 rounded-lg">
                Inicio
              </a>
              <a href="/admin/bets" onClick={() => setMobileMenuOpen(false)} className="block px-3 py-2 text-sm text-gray-300 hover:text-primary-400 rounded-lg">
                Apuestas
              </a>
              <a href="/admin/reports" onClick={() => setMobileMenuOpen(false)} className="block px-3 py-2 text-sm text-gray-300 hover:text-primary-400 rounded-lg">
                Reportes
              </a>
            </>
          ) : (
            <>
              <a href="/betting" onClick={() => setMobileMenuOpen(false)} className="block px-3 py-2 text-sm text-gray-300 hover:text-primary-400 rounded-lg">
                Apuesta Deportiva
              </a>
              <a href="/live" onClick={() => setMobileMenuOpen(false)} className="block px-3 py-2 text-sm text-gray-300 hover:text-primary-400 rounded-lg">
                Apuestas en Vivo
              </a>
              <a href="/about" onClick={() => setMobileMenuOpen(false)} className="block px-3 py-2 text-sm text-gray-300 hover:text-primary-400 rounded-lg">
                Acerca de Nosotros
              </a>
              <a href="/help" onClick={() => setMobileMenuOpen(false)} className="block px-3 py-2 text-sm text-gray-300 hover:text-primary-400 rounded-lg">
                Ayuda
              </a>
            </>
          )}
        </div>
      )}

      {loginOpen && (
        <LoginModal
          onClose={() => setLoginOpen(false)}
          onRegisterClick={openRegister}
        />
      )}

      {registerOpen && (
        <RegisterModal
          onClose={() => setRegisterOpen(false)}
          onLoginClick={openLogin}
        />
      )}

      {userPanelOpen && (
        <UserPanel
          onClose={() => setUserPanelOpen(false)}
          onDeposit={() => { setUserPanelOpen(false); setDepositOpen(true) }}
        />
      )}

      {depositOpen && (
        <DepositModal onClose={() => setDepositOpen(false)} />
      )}
    </>
  )
}
