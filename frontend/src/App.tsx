import { Routes, Route } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import MainLayout from './layouts/MainLayout'
import ErrorBoundary from './components/layout/ErrorBoundary'
import HomePage from './pages/HomePage'
import BettingPage from './pages/BettingPage'
import MyBetsPage from './pages/MyBetsPage'
import ProfilePage from './pages/ProfilePage'
import BonusesPage from './pages/BonusesPage'
import AdminDashboardPage from './pages/AdminDashboardPage'
import ReportsPage from './pages/ReportsPage'
import BetManagerPage from './pages/admin/BetManagerPage'
import AdminRoute from './routes/AdminRoute'
import GameRoute from './routes/GameRoute'

function App() {
  return (
    <ErrorBoundary>
      <AuthProvider>
        <Routes>
          <Route element={<MainLayout />}>
            <Route element={<GameRoute />}>
              <Route path="/" element={<HomePage />} />
              <Route path="/betting" element={<BettingPage />} />
              <Route path="/my-bets" element={<MyBetsPage />} />
              <Route path="/profile" element={<ProfilePage />} />
              <Route path="/bonuses" element={<BonusesPage />} />
              <Route path="/live" element={<BettingPage />} />
            </Route>
            <Route element={<AdminRoute />}>
              <Route path="/admin" element={<AdminDashboardPage />} />
              <Route path="/admin/reports" element={<ReportsPage />} />
              <Route path="/admin/bets" element={<BetManagerPage />} />
            </Route>
          </Route>
        </Routes>
      </AuthProvider>
    </ErrorBoundary>
  )
}

export default App
