import { MessageSquare, Search, XCircle } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { Link } from 'react-router-dom'
import { appointmentsApi, servicesApi } from '../api'
import { getApiError } from '../api/client'
import { AppointmentCard } from '../components/Cards'
import { EmptyState, ErrorAlert, Field, Loading, Modal, SuccessAlert } from '../components/UI'
import { useTestCustomer } from '../hooks/useTestCustomer'

export default function MyAppointmentsPage() {
  const { companyId } = useParams()
  const [profile] = useTestCustomer()
  const [externalUserId, setExternalUserId] = useState(profile.external_user_id)
  const [email, setEmail] = useState(profile.customer_email)
  const [mode, setMode] = useState('external')
  const [appointments, setAppointments] = useState([])
  const [services, setServices] = useState({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [cancelTarget, setCancelTarget] = useState(null)
  const [reason, setReason] = useState('')

  useEffect(() => {
    servicesApi.list(companyId)
      .then(({ data }) => setServices(Object.fromEntries(data.map((item) => [item.id, item.name]))))
      .catch((err) => setError(getApiError(err)))
    if (profile.external_user_id) {
      appointmentsApi.mine(companyId, profile.external_user_id)
        .then(({ data }) => setAppointments(data))
        .catch((err) => setError(getApiError(err)))
        .finally(() => setLoading(false))
    }
  }, [companyId, profile.external_user_id])

  const search = async () => {
    const value = mode === 'external' ? externalUserId : email
    if (!value.trim()) return setError(`Enter an ${mode === 'external' ? 'external user ID' : 'email address'}.`)
    setLoading(true); setError(''); setSuccess('')
    try {
      const response = mode === 'external' ? await appointmentsApi.mine(companyId, value) : await appointmentsApi.lookup(companyId, value)
      setAppointments(response.data)
    } catch (err) {
      setError(getApiError(err))
    } finally {
      setLoading(false)
    }
  }

  const cancel = async () => {
    setLoading(true); setError('')
    try {
      await appointmentsApi.cancel(companyId, cancelTarget.id, reason)
      setCancelTarget(null); setReason(''); setSuccess('Appointment cancelled.')
      await search()
    } catch (err) {
      setError(getApiError(err))
    } finally {
      setLoading(false)
    }
  }

  return <section className="page-container narrow-page">
    <div className="page-heading"><span className="eyebrow">Your schedule</span><h1>My appointments</h1><p>Find, review, and manage your upcoming bookings.</p></div>
    <div className="lookup-card">
      <div className="segmented"><button className={mode === 'external' ? 'active' : ''} onClick={() => setMode('external')}>External user ID</button><button className={mode === 'email' ? 'active' : ''} onClick={() => setMode('email')}>Email lookup</button></div>
      {mode === 'external' ? <Field label="External user ID"><input value={externalUserId} onChange={(event) => setExternalUserId(event.target.value)} placeholder="Your platform user ID" /></Field> : <Field label="Email address"><input type="email" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="you@example.com" /></Field>}
      <button className="button button-primary" onClick={search} disabled={loading}><Search size={17} /> Find appointments</button>
    </div>
    <ErrorAlert message={error} /><SuccessAlert message={success} />
    {loading && !cancelTarget ? <Loading label="Loading appointments" /> : appointments.length ? <div className="appointment-list">{appointments.map((appointment) => <AppointmentCard key={appointment.id} appointment={appointment} serviceName={services[appointment.service_id]} actions={<><Link className="button-link" to={`/companies/${companyId}/messages?appointment=${appointment.id}&subject=${encodeURIComponent(`${services[appointment.service_id] || 'Service'} appointment — ${appointment.appointment_date}`)}`}><MessageSquare size={15} /> Message company</Link>{appointment.status === 'confirmed' && <button className="button-link danger" onClick={() => setCancelTarget(appointment)}><XCircle size={15} /> Cancel</button>}</>} />)}</div> : <EmptyState title="No appointments loaded" text="Use your external user ID or booking email to find them." />}
    <Modal open={Boolean(cancelTarget)} title="Cancel appointment?" onClose={() => setCancelTarget(null)}>
      <p>This action will mark the appointment as cancelled.</p><Field label="Reason (optional)"><textarea rows="3" value={reason} onChange={(event) => setReason(event.target.value)} placeholder="Tell the business why you need to cancel" /></Field>
      <div className="button-row"><button className="button button-secondary" onClick={() => setCancelTarget(null)}>Keep appointment</button><button className="button button-danger" onClick={cancel} disabled={loading}>Cancel appointment</button></div>
    </Modal>
  </section>
}
