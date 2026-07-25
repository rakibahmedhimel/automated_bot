import { CalendarClock, ClipboardList, LayoutDashboard, Menu, MessageSquare, Settings2, Stethoscope, X } from 'lucide-react'
import { useState } from 'react'
import { NavLink, Outlet, useLocation, useParams } from 'react-router-dom'
import AdminErrorBoundary from '../components/AdminErrorBoundary'

export default function AdminLayout() {
  const { companyId } = useParams()
  const location = useLocation()
  const [open, setOpen] = useState(false)
  const links = [
    ['Dashboard', '', LayoutDashboard],
    ['Services', 'services', Stethoscope],
    ['Schedule', 'schedule', CalendarClock],
    ['Appointments', 'appointments', ClipboardList],
    ['Requests', 'requests', Settings2],
    ['Customer messages', 'messages', MessageSquare],
  ]
  return <div className="admin-shell">
    <button className="mobile-menu" onClick={() => setOpen(!open)} aria-label="Toggle admin menu">{open ? <X /> : <Menu />}</button>
    <aside className={open ? 'open' : ''}>
      <NavLink to="/" className="brand">Slotely <span>Admin</span></NavLink>
      <nav>{links.map(([label, path, Icon]) => <NavLink key={label} end={!path} to={`/admin/companies/${companyId}${path ? `/${path}` : ''}`} onClick={() => setOpen(false)}><Icon size={18} />{label}</NavLink>)}</nav>
      <NavLink to={`/companies/${companyId}/book`} className="view-booking">View booking page</NavLink>
    </aside>
    <main className="admin-main">
      <div className="admin-notice">Admin access is not yet protected. Authentication will be added later.</div>
      <AdminErrorBoundary key={location.pathname}><Outlet /></AdminErrorBoundary>
    </main>
  </div>
}
