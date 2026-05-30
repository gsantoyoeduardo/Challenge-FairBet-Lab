import { Outlet } from 'react-router-dom'
import AppBar from '../components/layout/AppBar'
import Footer from '../components/layout/Footer'

export default function MainLayout() {
  return (
    <div className="min-h-screen bg-black flex flex-col">
      <AppBar />
      <main className="flex-1 pt-6 pb-8 px-4">
        <Outlet />
      </main>
      <Footer />
    </div>
  )
}
