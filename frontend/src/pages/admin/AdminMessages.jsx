import { Send } from 'lucide-react'
import { useCallback, useEffect, useRef, useState } from 'react'
import { useLocation, useParams } from 'react-router-dom'
import { conversationsApi } from '../../api'
import { getApiError } from '../../api/client'
import { EmptyState, ErrorAlert, Loading } from '../../components/UI'

export default function AdminMessages() {
  const { companyId } = useParams()
  const location = useLocation()
  const linkedRequestId = new URLSearchParams(location.search).get('request')
  const [conversations, setConversations] = useState([])
  const [selected, setSelected] = useState(null)
  const [messages, setMessages] = useState([])
  const [text, setText] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [sending, setSending] = useState(false)
  const messageListRef = useRef(null)

  const load = useCallback(async () => {
    try {
      const { data } = await conversationsApi.adminList(companyId)
      setConversations(data)
      setSelected((current) => {
        const linked = data.find((item) => item.schedule_request_id === linkedRequestId)
        if (linked) return linked
        if (!current) return data[0] || null
        return data.find((item) => item.id === current.id) || data[0] || null
      })
    } catch (err) { setError(getApiError(err)) }
    finally { setLoading(false) }
  }, [companyId, linkedRequestId])
  const loadMessages = useCallback(async () => {
    if (!selected) return
    try {
      const { data } = await conversationsApi.adminMessages(companyId, selected.id)
      setMessages(data)
    } catch (err) { setError(getApiError(err)) }
  }, [companyId, selected])

  useEffect(() => {
    const timer = setTimeout(load, 0)
    return () => clearTimeout(timer)
  }, [load])
  useEffect(() => {
    const initial = setTimeout(loadMessages, 0)
    const polling = setInterval(() => { load(); loadMessages() }, 10000)
    return () => { clearTimeout(initial); clearInterval(polling) }
  }, [load, loadMessages])
  useEffect(() => {
    const element = messageListRef.current
    if (element) element.scrollTop = element.scrollHeight
  }, [messages])

  const send = async (event) => {
    event?.preventDefault()
    if (!text.trim() || !selected || sending) return
    setSending(true)
    setError('')
    try {
      await conversationsApi.adminSend(companyId, selected.id, text.trim())
      setText('')
      await loadMessages()
      await load()
    } catch (err) { setError(getApiError(err)) }
    finally { setSending(false) }
  }
  const toggleStatus = async () => {
    try {
      const { data } = await conversationsApi.adminStatus(
        companyId,
        selected.id,
        selected.status === 'open' ? 'closed' : 'open',
      )
      setSelected(data)
      await load()
    } catch (err) { setError(getApiError(err)) }
  }

  return <section>
    <div className="admin-heading"><span className="eyebrow">Customer care</span><h1>Customer messages</h1><p>Keep appointment questions separate from the AI booking assistant.</p></div>
    <div className="admin-dev-warning">Development admin mode — identity is not authenticated.</div>
    <ErrorAlert message={error} />
    {loading ? <Loading /> : <div className="support-shell admin-support">
      <aside>{conversations.map((item) => <button className={selected?.id === item.id ? 'active' : ''} key={item.id} onClick={() => setSelected(item)}><strong>{item.subject}</strong><span>{item.customer_name || item.customer_email || item.external_user_id}</span>{item.appointment_id && <small>Linked appointment</small>}{item.schedule_request_id && <small>Linked schedule request</small>}<small>{item.latest_message || 'No messages yet'}</small><small>{item.status}</small></button>)}</aside>
      <div className="support-thread">{selected ? <>
        <header><div><strong>{selected.subject}</strong><small>{selected.customer_name || 'Customer'} · {selected.customer_email}</small><small>{selected.appointment_id ? `Appointment ${selected.appointment_id}` : selected.schedule_request_id ? `Request ${selected.schedule_request_id}` : 'General conversation'}</small></div><button className="button button-secondary small" onClick={toggleStatus}>{selected.status === 'open' ? 'Close' : 'Reopen'}</button></header>
        <div className="support-messages" ref={messageListRef}>{messages.map((item) => <div className={`support-message ${item.sender_type}`} key={item.id}><span>{item.content}</span></div>)}</div>
        <form onSubmit={send}><textarea rows="2" value={text} onChange={(event) => setText(event.target.value)} onKeyDown={(event) => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); send() } }} disabled={selected.status === 'closed' || sending} placeholder={selected.status === 'closed' ? 'Reopen this conversation to reply' : 'Reply to customer…'} /><button aria-label="Send reply" disabled={selected.status === 'closed' || sending || !text.trim()}>{sending ? '…' : <Send size={17} />}</button></form>
      </> : <EmptyState title="No customer messages" text="New conversations will appear here." />}</div>
    </div>}
  </section>
}
