import { Edit3, Plus, Power } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { servicesApi } from '../../api'
import { getApiError } from '../../api/client'
import { EmptyState, ErrorAlert, Field, Loading, Modal, SuccessAlert } from '../../components/UI'

const EMPTY = { name: '', description: '', duration_minutes: 30, buffer_minutes: 0 }

export default function AdminServices() {
  const { companyId } = useParams()
  const [items, setItems] = useState([])
  const [form, setForm] = useState(EMPTY)
  const [editing, setEditing] = useState(null)
  const [open, setOpen] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const load = () => servicesApi.list(companyId).then(({ data }) => setItems(data)).catch((err) => setError(getApiError(err))).finally(() => setLoading(false))
  useEffect(() => {
    let active = true
    servicesApi.list(companyId)
      .then(({ data }) => {
        if (active) setItems(data)
      })
      .catch((err) => {
        if (active) setError(getApiError(err))
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [companyId])
  const showForm = (item = null) => {
    setEditing(item); setForm(item ? { name: item.name, description: item.description || '', duration_minutes: item.duration_minutes, buffer_minutes: item.buffer_minutes } : EMPTY); setOpen(true)
  }
  const submit = async (event) => {
    event.preventDefault(); setError('')
    try {
      if (editing) await servicesApi.update(companyId, editing.id, form)
      else await servicesApi.create(companyId, form)
      setSuccess(editing ? 'Service updated.' : 'Service created.'); setOpen(false); load()
    } catch (err) { setError(getApiError(err)) }
  }
  const deactivate = async (item) => {
    try { await servicesApi.update(companyId, item.id, { is_active: false }); setSuccess('Service deactivated.'); load() } catch (err) { setError(getApiError(err)) }
  }
  return <><div className="admin-heading with-action"><div><span className="eyebrow">Service catalogue</span><h1>Services</h1><p>Create and manage bookable services. This API lists active services only; deactivated services cannot currently be reactivated here.</p></div><button className="button button-primary" onClick={() => showForm()}><Plus size={17} /> Add service</button></div>
    <ErrorAlert message={error} /><SuccessAlert message={success} />
    {loading ? <Loading /> : items.length ? <div className="admin-card-grid">{items.map((item) => <article className="admin-card service-admin-card" key={item.id}><div><span className="status-badge status-confirmed">Active</span><h2>{item.name}</h2><p>{item.description || 'No description'}</p></div><div className="service-meta"><span>{item.duration_minutes} min</span><span>{item.buffer_minutes} min buffer</span></div><div className="button-row"><button className="button button-secondary small" onClick={() => showForm(item)}><Edit3 size={15} /> Edit</button><button className="button-link danger" onClick={() => deactivate(item)}><Power size={15} /> Deactivate</button></div></article>)}</div> : <EmptyState title="No active services" text="Create your first service to start accepting bookings." />}
    <Modal open={open} title={editing ? 'Edit service' : 'Create service'} onClose={() => setOpen(false)}><form onSubmit={submit} className="stack-form">
      <Field label="Service name"><input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></Field>
      <Field label="Description"><textarea rows="3" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} /></Field>
      <div className="form-grid"><Field label="Duration (minutes)"><input required min="1" type="number" value={form.duration_minutes} onChange={(e) => setForm({ ...form, duration_minutes: Number(e.target.value) })} /></Field><Field label="Buffer (minutes)"><input min="0" type="number" value={form.buffer_minutes} onChange={(e) => setForm({ ...form, buffer_minutes: Number(e.target.value) })} /></Field></div>
      <div className="button-row"><button type="button" className="button button-secondary" onClick={() => setOpen(false)}>Cancel</button><button className="button button-primary">Save service</button></div>
    </form></Modal>
  </>
}
