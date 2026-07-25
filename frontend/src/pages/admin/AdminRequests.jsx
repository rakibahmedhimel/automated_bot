import { MessageSquare } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { requestsApi, servicesApi } from '../../api'
import { getApiError } from '../../api/client'
import { StatusBadge } from '../../components/Cards'
import { EmptyState, ErrorAlert, Field, Loading, Modal, SuccessAlert } from '../../components/UI'
import { formatDate, formatTime } from '../../utils/format'

export default function AdminRequests() {
  const { companyId } = useParams()
  const [items, setItems] = useState([])
  const [services, setServices] = useState({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [approval, setApproval] = useState(null)
  const [approvalDate, setApprovalDate] = useState('')
  const [approvalTime, setApprovalTime] = useState('')

  const load = () => requestsApi.list(companyId)
    .then(({ data }) => setItems(data))
    .catch((err) => setError(getApiError(err)))
    .finally(() => setLoading(false))

  useEffect(() => {
    let active = true
    Promise.all([requestsApi.list(companyId), servicesApi.list(companyId)])
      .then(([requestResponse, serviceResponse]) => {
        if (!active) return
        setItems(requestResponse.data)
        setServices(Object.fromEntries(serviceResponse.data.map((item) => [item.id, item.name])))
      })
      .catch((err) => {
        if (active) setError(getApiError(err))
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => { active = false }
  }, [companyId])

  const reject = async (id) => {
    setError('')
    try {
      await requestsApi.status(companyId, id, {
        status: 'rejected',
        create_appointment: false,
      })
      setSuccess('Request rejected.')
      await load()
    } catch (err) { setError(getApiError(err)) }
  }
  const showApproval = (item) => {
    setApproval(item)
    setApprovalDate(item.requested_date)
    setApprovalTime(item.preferred_start_time || '')
  }
  const approveWithAppointment = async (event) => {
    event.preventDefault()
    setError('')
    try {
      await requestsApi.status(companyId, approval.id, {
        status: 'approved',
        create_appointment: true,
        appointment_date: approvalDate,
        start_time: approvalTime,
      })
      setSuccess('Request approved and a confirmed appointment was created.')
      setApproval(null)
      await load()
    } catch (err) { setError(getApiError(err)) }
  }

  return <>
    <div className="admin-heading"><span className="eyebrow">Manual review</span><h1>Schedule requests</h1><p>Review customer requests for times outside normal availability.</p></div>
    <ErrorAlert message={error} /><SuccessAlert message={success} />
    {loading ? <Loading /> : items.length ? <div className="request-grid">{items.map((item) => <article className="admin-card request-card" key={item.id}>
      <div className="request-head"><div><h2>{item.customer_name || 'Guest request'}</h2><p>{item.customer_email || item.external_user_id || 'No contact details'} · {item.customer_phone || 'No phone'}</p></div><StatusBadge status={item.status} /></div>
      <dl><div><dt>Service</dt><dd>{services[item.service_id] || item.service_id}</dd></div><div><dt>Date</dt><dd>{formatDate(item.requested_date)}</dd></div><div><dt>Preferred time</dt><dd>{formatTime(item.preferred_start_time)} – {formatTime(item.preferred_end_time)}</dd></div><div><dt>Created</dt><dd>{new Date(item.created_at).toLocaleString()}</dd></div></dl>
      {item.message && <blockquote>{item.message}</blockquote>}
      <Link className="button-link" to={`/admin/companies/${companyId}/messages?request=${item.id}`}><MessageSquare size={15} /> Linked conversation</Link>
      {item.status === 'pending' && <div className="button-row"><button className="button button-primary small" onClick={() => showApproval(item)}>Approve with appointment</button><button className="button button-secondary small" onClick={() => reject(item.id)}>Reject</button></div>}
    </article>)}</div> : <EmptyState title="No schedule requests" />}
    <Modal open={Boolean(approval)} title="Approve and create appointment" onClose={() => setApproval(null)}><p>The request is approved only after the selected time passes availability validation and a confirmed appointment is created.</p><form className="stack-form" onSubmit={approveWithAppointment}><Field label="Appointment date"><input required type="date" value={approvalDate} onChange={(event) => setApprovalDate(event.target.value)} /></Field><Field label="Start time"><input required type="time" value={approvalTime} onChange={(event) => setApprovalTime(event.target.value)} /></Field><div className="button-row"><button type="button" className="button button-secondary" onClick={() => setApproval(null)}>Cancel</button><button className="button button-primary">Verify and approve</button></div></form></Modal>
  </>
}
