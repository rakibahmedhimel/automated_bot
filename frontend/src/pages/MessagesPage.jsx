import { MessageSquarePlus, Send } from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import { useLocation, useParams } from 'react-router-dom'
import { conversationsApi } from '../api'
import { getApiError } from '../api/client'
import { EmptyState, ErrorAlert, Field, Loading, Modal } from '../components/UI'
import { useTestCustomer } from '../hooks/useTestCustomer'

export default function MessagesPage() {
  const { companyId } = useParams()
  const location = useLocation()
  const [profile] = useTestCustomer()
  const [conversations, setConversations] = useState([])
  const [selected, setSelected] = useState(null)
  const [messages, setMessages] = useState([])
  const [text, setText] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const query = new URLSearchParams(location.search)
  const appointmentId = query.get('appointment')
  const scheduleRequestId = query.get('request')
  const requestedSubject = query.get('subject')
  const [creating, setCreating] = useState(false)
  const [subject, setSubject] = useState(requestedSubject || 'Appointment question')
  const [initialMessage, setInitialMessage] = useState('')
  const identity = {
    external_user_id: profile.external_user_id || undefined,
    customer_email: profile.customer_email || undefined,
  }

  const loadConversations = useCallback(async () => {
    if (!profile.external_user_id && !profile.customer_email) {
      setLoading(false)
      return
    }
    try {
      const { data } = await conversationsApi.mine(companyId, {
        external_user_id: profile.external_user_id || undefined,
        customer_email: profile.customer_email || undefined,
      })
      setConversations(data)
      const linked = data.find((item) =>
        (appointmentId && item.appointment_id === appointmentId)
        || (scheduleRequestId && item.schedule_request_id === scheduleRequestId))
      setSelected((current) => linked || current || data[0] || null)
      if ((appointmentId || scheduleRequestId) && !linked) setCreating(true)
    } catch (err) {
      setError(getApiError(err))
    } finally {
      setLoading(false)
    }
  }, [companyId, profile.external_user_id, profile.customer_email, appointmentId, scheduleRequestId])

  const loadMessages = useCallback(async () => {
    if (!selected) return
    try {
      const { data } = await conversationsApi.messages(companyId, selected.id, {
        external_user_id: profile.external_user_id || undefined,
        customer_email: profile.customer_email || undefined,
      })
      setMessages(data)
    } catch (err) {
      setError(getApiError(err))
    }
  }, [companyId, selected, profile.external_user_id, profile.customer_email])

  useEffect(() => {
    const timer = setTimeout(loadConversations, 0)
    return () => clearTimeout(timer)
  }, [loadConversations])
  useEffect(() => {
    const initial = setTimeout(loadMessages, 0)
    const polling = setInterval(loadMessages, 10000)
    return () => { clearTimeout(initial); clearInterval(polling) }
  }, [loadMessages])

  const create = async () => {
    setError('')
    try {
      const { data } = await conversationsApi.create(companyId, {
        ...identity,
        customer_name: profile.customer_name || null,
        appointment_id: appointmentId || null,
        schedule_request_id: scheduleRequestId || null,
        subject,
        initial_message: initialMessage || null,
      })
      setCreating(false); setInitialMessage(''); setSelected(data)
      await loadConversations()
    } catch (err) { setError(getApiError(err)) }
  }

  const send = async (event) => {
    event.preventDefault()
    if (!text.trim() || !selected) return
    try {
      await conversationsApi.send(companyId, selected.id, { ...identity, content: text })
      setText('')
      await loadMessages()
    } catch (err) { setError(getApiError(err)) }
  }

  return <section className="page-container messages-page">
    <div className="page-heading with-action"><div><span className="eyebrow">Direct support</span><h1>Messages</h1><p>Talk with the business about appointments and schedule requests.</p></div><button className="button button-primary" onClick={() => setCreating(true)}><MessageSquarePlus size={17} /> New conversation</button></div>
    <ErrorAlert message={error} />
    {loading ? <Loading /> : !profile.external_user_id && !profile.customer_email ? <EmptyState title="Add your customer profile" text="An external user ID or email is needed to load private conversations." /> : <div className="support-shell">
      <aside>{conversations.map((item) => <button className={selected?.id === item.id ? 'active' : ''} key={item.id} onClick={() => setSelected(item)}><strong>{item.subject}</strong>{item.appointment_id && <span>Appointment linked</span>}{item.schedule_request_id && <span>Schedule request linked</span>}<small>{item.status}</small></button>)}</aside>
      <div className="support-thread">
        {selected ? <><header><strong>{selected.subject}</strong><span className={`status-badge status-${selected.status}`}>{selected.status}</span></header><div className="support-messages">{messages.map((item) => <div className={`support-message ${item.sender_type}`} key={item.id}><span>{item.content}</span></div>)}</div><form onSubmit={send}><input value={text} onChange={(event) => setText(event.target.value)} placeholder={selected.status === 'closed' ? 'This conversation is closed' : 'Write a message…'} disabled={selected.status === 'closed'} /><button disabled={selected.status === 'closed'}><Send size={17} /></button></form></> : <EmptyState title="No conversation selected" text="Start a conversation to contact the business." />}
      </div>
    </div>}
    <Modal open={creating} title="New conversation" onClose={() => setCreating(false)}><div className="stack-form"><Field label="Subject"><input value={subject} onChange={(event) => setSubject(event.target.value)} /></Field><Field label="Message (optional)"><textarea rows="4" value={initialMessage} onChange={(event) => setInitialMessage(event.target.value)} /></Field><button className="button button-primary" onClick={create}>Start conversation</button></div></Modal>
  </section>
}
