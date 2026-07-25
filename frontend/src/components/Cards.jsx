import { ArrowRight, Building2, Clock3 } from 'lucide-react'
import { Link } from 'react-router-dom'
import { formatDate, formatTime } from '../utils/format'

export function CompanyCard({ company }) {
  return <article className="glass-card company-card">
    <div className="icon-tile"><Building2 size={22} /></div>
    <div><h3>{company.name}</h3><p>{company.description || `Appointments in ${company.timezone}`}</p></div>
    <Link className="text-link" to={`/companies/${company.id}/book`}>Book now <ArrowRight size={16} /></Link>
  </article>
}

export function ServiceCard({ service, selected, onClick }) {
  return <button type="button" className={`service-card ${selected ? 'selected' : ''}`} onClick={onClick}>
    <div><h3>{service.name}</h3><p>{service.description || 'Professional appointment service'}</p></div>
    <span><Clock3 size={15} /> {service.duration_minutes} min{service.buffer_minutes ? ` + ${service.buffer_minutes} buffer` : ''}</span>
  </button>
}

export function StatusBadge({ status }) {
  return <span className={`status-badge status-${status}`}>{status?.replace('_', ' ')}</span>
}

export function AppointmentCard({ appointment, serviceName, actions }) {
  return <article className="appointment-card">
    <div className="appointment-date"><strong>{formatDate(appointment.appointment_date)}</strong><span>{formatTime(appointment.start_time)} – {formatTime(appointment.end_time)}</span></div>
    <div><h3>{serviceName || 'Appointment'}</h3><p>{appointment.customer_name || 'Guest'} · {appointment.customer_email || appointment.external_user_id || 'No contact details'}</p><small>Service ID: {appointment.service_id}</small></div>
    <div className="appointment-actions"><StatusBadge status={appointment.status} />{actions}</div>
  </article>
}
