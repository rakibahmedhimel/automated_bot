import { Filter } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { appointmentsApi } from '../../api'
import { getApiError } from '../../api/client'
import { StatusBadge } from '../../components/Cards'
import { EmptyState, ErrorAlert, Field, Loading, SuccessAlert } from '../../components/UI'
import { formatDate, formatTime } from '../../utils/format'

const STATUSES = ['confirmed', 'cancelled', 'completed', 'no_show']

export default function AdminAppointments() {
  const { companyId } = useParams()
  const [items, setItems] = useState([])
  const [filters, setFilters] = useState({ status: '', start_date: '', end_date: '' })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const load = async () => {
    setLoading(true); setError('')
    try { const { data } = await appointmentsApi.list(companyId, Object.fromEntries(Object.entries(filters).filter(([, value]) => value))); setItems(data) } catch (err) { setError(getApiError(err)) } finally { setLoading(false) }
  }
  useEffect(() => {
    appointmentsApi.list(companyId, {})
      .then(({ data }) => setItems(data))
      .catch((err) => setError(getApiError(err)))
      .finally(() => setLoading(false))
  }, [companyId])
  const updateStatus = async (id, status) => {
    try { await appointmentsApi.status(companyId, id, status); setSuccess('Appointment status updated.'); load() } catch (err) { setError(getApiError(err)) }
  }
  return <><div className="admin-heading"><span className="eyebrow">Booking operations</span><h1>Appointments</h1><p>Review and update every appointment.</p></div>
    <div className="filter-bar"><Field label="Status"><select value={filters.status} onChange={(e) => setFilters({ ...filters, status: e.target.value })}><option value="">All statuses</option>{STATUSES.map((status) => <option key={status}>{status}</option>)}</select></Field><Field label="From"><input type="date" value={filters.start_date} onChange={(e) => setFilters({ ...filters, start_date: e.target.value })} /></Field><Field label="To"><input type="date" value={filters.end_date} onChange={(e) => setFilters({ ...filters, end_date: e.target.value })} /></Field><button className="button button-primary" onClick={load}><Filter size={16} /> Apply filters</button></div>
    <ErrorAlert message={error} /><SuccessAlert message={success} />
    {loading ? <Loading /> : items.length ? <div className="admin-card table-wrap"><table><thead><tr><th>Date & time</th><th>Customer</th><th>Service</th><th>Status</th><th>Update</th></tr></thead><tbody>{items.map((item) => <tr key={item.id}><td><strong>{formatDate(item.appointment_date)}</strong><br /><small>{formatTime(item.start_time)} – {formatTime(item.end_time)}</small></td><td>{item.customer_name || 'Guest'}<br /><small>{item.customer_email || item.external_user_id || '—'}</small></td><td><small>{item.service_id}</small></td><td><StatusBadge status={item.status} /></td><td><select aria-label="Update appointment status" value={item.status} onChange={(e) => updateStatus(item.id, e.target.value)}>{STATUSES.map((status) => <option key={status}>{status}</option>)}</select></td></tr>)}</tbody></table></div> : <EmptyState title="No appointments match these filters" />}
  </>
}
