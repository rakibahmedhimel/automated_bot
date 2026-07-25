import { CalendarCheck2 } from 'lucide-react'
import { Link, Outlet, useParams } from 'react-router-dom'
import TestCustomerProfile from '../components/TestCustomerProfile'

export default function PublicLayout() {
  const { companyId } = useParams()
  return <div className="site-shell">
    <header className="navbar">
      <Link to="/" className="brand"><span><CalendarCheck2 size={20} /></span> Slotely</Link>
      <nav>
        {companyId && <><Link to={`/companies/${companyId}/book`}>Book</Link><Link to={`/companies/${companyId}/schedule-request`}>Request a custom time</Link><Link to={`/companies/${companyId}/appointments`}>My appointments</Link><Link to={`/companies/${companyId}/messages`}>Messages</Link><Link to={`/companies/${companyId}/chat`}>AI assistant</Link></>}
      </nav>
      <div className="nav-actions">
        {companyId && import.meta.env.VITE_ENABLE_ADMIN === 'true' && <Link className="admin-link" to={`/admin/companies/${companyId}`}>Admin</Link>}
        <TestCustomerProfile />
      </div>
    </header>
    <main><Outlet /></main>
    <footer>© 2026 Slotely · Appointments, beautifully organized.</footer>
  </div>
}
