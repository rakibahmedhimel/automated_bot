import { CalendarPlus, MessageSquare } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { requestsApi, servicesApi } from '../api'
import { getApiError } from '../api/client'
import { EmptyState, ErrorAlert, Field, Loading, SuccessAlert } from '../components/UI'
import TimeSelector from '../components/TimeSelector'
import { useTestCustomer } from '../hooks/useTestCustomer'
import { formatDate, formatTime, todayInput } from '../utils/format'

const EMPTY = {
  service_id: '', requested_date: '', preferred_start_time: '',
  preferred_end_time: '', message: '',
}

export default function ScheduleRequestPage() {
  const { companyId } = useParams()
  const [profile] = useTestCustomer()
  const [services, setServices] = useState([])
  const [requests, setRequests] = useState([])
  const [form, setForm] = useState(EMPTY)
  const [created, setCreated] = useState(null)
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const serviceNames = useMemo(
    () => Object.fromEntries(services.map((item) => [item.id, item.name])),
    [services],
  )

  const loadMine = async () => {
    if (!profile.external_user_id) {
      setRequests([])
      return
    }
    const { data } = await requestsApi.mine(companyId, profile.external_user_id)
    setRequests(data)
  }
  useEffect(() => {
    let active = true
    Promise.all([
      servicesApi.list(companyId),
      profile.external_user_id
        ? requestsApi.mine(companyId, profile.external_user_id)
        : Promise.resolve({ data: [] }),
    ]).then(([serviceResponse, requestResponse]) => {
      if (!active) return
      setServices(serviceResponse.data)
      setRequests(requestResponse.data)
    }).catch((err) => {
      if (active) setError(getApiError(err))
    }).finally(() => {
      if (active) setLoading(false)
    })
    return () => { active = false }
  }, [companyId, profile.external_user_id])

  const submit = async (event) => {
    event.preventDefault()
    setError('')
    if (!form.service_id || !form.requested_date) return setError('Service and date are required.')
    if (form.requested_date < todayInput()) return setError('Requested date cannot be in the past.')
    if (!form.preferred_start_time || !form.preferred_end_time) return setError('Preferred start and end time are required.')
    if (form.preferred_start_time >= form.preferred_end_time) return setError('Preferred start must be before preferred end.')
    if (!profile.customer_name || !profile.customer_email || !profile.customer_phone) return setError('Name, email, and phone are required in your customer profile.')
    if (!profile.external_user_id) return setError('An external user ID is required to list and link your requests.')
    setSubmitting(true)
    try {
      const { data } = await requestsApi.create(companyId, {
        ...form,
        external_user_id: profile.external_user_id || null,
        customer_name: profile.customer_name,
        customer_email: profile.customer_email,
        customer_phone: profile.customer_phone,
      })
      setCreated(data)
      setForm(EMPTY)
      await loadMine()
    } catch (err) { setError(getApiError(err)) }
    finally { setSubmitting(false) }
  }

  if (loading) return <div className="page-container"><Loading /></div>
  return <section className="page-container schedule-request-page">
    <div className="page-heading"><span className="eyebrow">Flexible scheduling</span><h1>Request a custom time</h1><p>Ask the business to review a time outside currently available slots.</p></div>
    <ErrorAlert message={error} />
    {created && <div className="admin-card request-confirmation"><SuccessAlert message="Schedule request submitted." /><strong>{serviceNames[created.service_id]}</strong><span>Request ID: <span className="mono">{created.id}</span></span><span>{formatDate(created.requested_date)} · {formatTime(created.preferred_start_time)}–{formatTime(created.preferred_end_time)} · Pending</span><div className="button-row"><Link className="button button-primary small" to={`/companies/${companyId}/messages?request=${created.id}&subject=${encodeURIComponent(`${serviceNames[created.service_id]} schedule request — ${created.requested_date}`)}`}><MessageSquare size={15} /> Message company</Link><a className="button button-secondary small" href="#my-requests">View my requests</a></div></div>}
    <div className="admin-grid"><form className="admin-card stack-form" onSubmit={submit}><h2><CalendarPlus size={18} /> New request</h2><Field label="Service"><select required value={form.service_id} onChange={(event) => setForm({ ...form, service_id: event.target.value })}><option value="">Choose a service</option>{services.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></Field><Field label="Requested date"><input required type="date" min={todayInput()} value={form.requested_date} onChange={(event) => setForm({ ...form, requested_date: event.target.value })} /></Field><div className="form-grid"><TimeSelector required label="Preferred start" value={form.preferred_start_time} onChange={(value) => setForm({ ...form, preferred_start_time: value })} /><TimeSelector required label="Preferred end" value={form.preferred_end_time} onChange={(value) => setForm({ ...form, preferred_end_time: value })} /></div><Field label="Message"><textarea rows="4" value={form.message} onChange={(event) => setForm({ ...form, message: event.target.value })} /></Field><div className="profile-summary"><small>Customer profile</small><strong>{profile.customer_name || 'Name missing'}</strong><span>{profile.customer_email || 'Email missing'} · {profile.customer_phone || 'Phone missing'}</span></div><button className="button button-primary" disabled={submitting}>{submitting ? 'Sending…' : 'Send request'}</button></form>
      <div className="admin-card" id="my-requests"><h2>My requests</h2>{requests.length ? <div className="simple-list request-customer-list">{requests.map((item) => <div key={item.id}><span><strong>{serviceNames[item.service_id] || 'Service'}</strong><small>{formatDate(item.requested_date)} · {formatTime(item.preferred_start_time)}–{formatTime(item.preferred_end_time)}</small></span><span><span className={`status-badge status-${item.status}`}>{item.status}</span><Link className="button-link" to={`/companies/${companyId}/messages?request=${item.id}&subject=${encodeURIComponent(`${serviceNames[item.service_id] || 'Service'} schedule request — ${item.requested_date}`)}`}>Message company</Link></span></div>)}</div> : <EmptyState title="No schedule requests" text="Requests submitted with your external user ID appear here." />}</div>
    </div>
  </section>
}
