import { CalendarClock, CalendarDays, ClipboardList, Stethoscope } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { dashboardApi } from '../../api'
import { getApiError } from '../../api/client'
import { StatusBadge } from '../../components/Cards'
import { EmptyState, ErrorAlert, Loading } from '../../components/UI'
import { DAY_NAMES, formatDate, formatTime } from '../../utils/format'

export default function AdminDashboard() {
  const { companyId } = useParams()
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  useEffect(() => { dashboardApi.get(companyId).then((response) => setData(response.data)).catch((err) => setError(getApiError(err))) }, [companyId])
  if (!data && !error) return <Loading label="Loading dashboard" />
  return <><div className="admin-heading"><span className="eyebrow">Workspace overview</span><h1>{data?.company?.name || 'Dashboard'}</h1><p>Everything happening across your schedule.</p></div><ErrorAlert message={error} />
    {data && <><div className="summary-grid">
      {[[Stethoscope,'Active services',data.services.length],[CalendarDays,'Upcoming bookings',data.upcoming_appointments.length],[ClipboardList,'Pending requests',data.pending_schedule_requests.length],[CalendarClock,'Schedule periods',data.weekly_schedule.length]].map(([Icon,label,value]) => <div className="summary-card" key={label}><Icon /><span>{label}</span><strong>{value}</strong></div>)}
    </div>
    <div className="admin-grid">
      <section className="admin-card span-two"><div className="card-heading"><h2>Upcoming appointments</h2></div>{data.upcoming_appointments.length ? <div className="table-wrap"><table><thead><tr><th>Date</th><th>Time</th><th>Customer</th><th>Status</th></tr></thead><tbody>{data.upcoming_appointments.slice(0, 8).map((item) => <tr key={item.id}><td>{formatDate(item.appointment_date)}</td><td>{formatTime(item.start_time)}</td><td>{item.customer_name || item.external_user_id || 'Guest'}</td><td><StatusBadge status={item.status} /></td></tr>)}</tbody></table></div> : <EmptyState title="No upcoming bookings" />}</section>
      <section className="admin-card"><div className="card-heading"><h2>Weekly hours</h2></div>{data.weekly_schedule.length ? <div className="simple-list">{data.weekly_schedule.map((item) => <div key={item.id}><strong>{DAY_NAMES[item.day_of_week]}</strong><span>{formatTime(item.start_time)} – {formatTime(item.end_time)}</span></div>)}</div> : <EmptyState title="No weekly schedule" />}</section>
      <section className="admin-card"><div className="card-heading"><h2>Pending requests</h2></div>{data.pending_schedule_requests.length ? <div className="simple-list">{data.pending_schedule_requests.slice(0, 5).map((item) => <div key={item.id}><strong>{item.customer_name || 'Guest'}</strong><span>{formatDate(item.requested_date)} · {formatTime(item.preferred_start_time)}</span></div>)}</div> : <EmptyState title="No pending requests" />}</section>
      <section className="admin-card span-two"><div className="card-heading"><h2>Overrides & breaks</h2></div><div className="two-column-list"><div><h3>Overrides</h3>{data.schedule_overrides.length ? data.schedule_overrides.map((item) => <p key={item.id}>{formatDate(item.date)} · {item.is_closed ? 'Closed' : 'Custom hours'}</p>) : <p>No upcoming overrides.</p>}</div><div><h3>Breaks</h3>{data.breaks.length ? data.breaks.map((item) => <p key={item.id}>{formatDate(item.date)} · {formatTime(item.start_time)}–{formatTime(item.end_time)}</p>) : <p>No upcoming breaks.</p>}</div></div></section>
    </div></>}
  </>
}
