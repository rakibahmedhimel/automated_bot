import { Archive, Bot, MessageCircle, Pencil, Plus, Send } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { useParams } from 'react-router-dom'
import { chatApi } from '../api'
import { getApiError } from '../api/client'
import { EmptyState, ErrorAlert, Field, Loading, Modal } from '../components/UI'
import { useTestCustomer } from '../hooks/useTestCustomer'

export default function ChatPage() {
  const { companyId } = useParams()
  const [profile] = useTestCustomer()
  const externalUserId = profile.external_user_id
  const [sessions, setSessions] = useState([])
  const [sessionId, setSessionId] = useState('')
  const [messages, setMessages] = useState([])
  const [content, setContent] = useState('')
  const [loading, setLoading] = useState(true)
  const [responding, setResponding] = useState(false)
  const [error, setError] = useState('')
  const [renameOpen, setRenameOpen] = useState(false)
  const [renameTitle, setRenameTitle] = useState('')
  const endRef = useRef(null)
  const messageListRef = useRef(null)
  const shouldAutoScroll = useRef(true)
  const [showJump, setShowJump] = useState(false)

  const scrollToLatest = (behavior = 'smooth') => {
    endRef.current?.scrollIntoView({ behavior, block: 'end' })
    shouldAutoScroll.current = true
    setShowJump(false)
  }

  useEffect(() => {
    chatApi.sessions(companyId, externalUserId)
      .then(({ data }) => {
        setSessions(data)
        setSessionId((current) => current || data[0]?.id || '')
      })
      .catch((err) => setError(getApiError(err)))
      .finally(() => setLoading(false))
  }, [companyId, externalUserId])
  useEffect(() => {
    if (!sessionId) return
    shouldAutoScroll.current = true
    chatApi.messages(companyId, sessionId).then(({ data }) => setMessages(data)).catch((err) => setError(getApiError(err))).finally(() => setLoading(false))
  }, [companyId, sessionId])
  useEffect(() => {
    if (shouldAutoScroll.current) {
      requestAnimationFrame(() => scrollToLatest(messages.length ? 'smooth' : 'auto'))
    }
  }, [messages, responding])

  const trackScroll = () => {
    const element = messageListRef.current
    if (!element) return
    const nearBottom = (
      element.scrollHeight
      - element.scrollTop
      - element.clientHeight
      < 80
    )
    shouldAutoScroll.current = nearBottom
    setShowJump(!nearBottom)
  }

  const createSession = async () => {
    setError('')
    try {
      const { data } = await chatApi.createSession(companyId, { external_user_id: externalUserId || null })
      setSessions((items) => [data, ...items]); setSessionId(data.id)
    } catch (err) { setError(getApiError(err)) }
  }
  const send = async (event) => {
    event.preventDefault()
    if (!content.trim() || !sessionId) return
    const text = content.trim(); setContent(''); setResponding(true); setError('')
    shouldAutoScroll.current = true
    setMessages((items) => [...items, { id: `local-${Date.now()}`, role: 'user', content: text }])
    try {
      const { data } = await chatApi.send(companyId, sessionId, {
        content: text,
        customer_name: profile.customer_name || null,
        customer_email: profile.customer_email || null,
        customer_phone: profile.customer_phone || null,
      })
      setMessages((items) => [...items, data.message])
      const sessionsResponse = await chatApi.sessions(companyId, externalUserId)
      setSessions(sessionsResponse.data)
    } catch (err) { setError(getApiError(err)) } finally { setResponding(false) }
  }
  const archive = async () => {
    if (!sessionId) return
    try {
      await chatApi.archive(companyId, sessionId)
      setSessions((items) => items.filter((item) => item.id !== sessionId)); setSessionId(''); setMessages([])
    } catch (err) { setError(getApiError(err)) }
  }
  const rename = async (event) => {
    event.preventDefault()
    if (!renameTitle.trim()) return
    try {
      const { data } = await chatApi.rename(companyId, sessionId, renameTitle.trim())
      setSessions((items) => items.map((item) => item.id === data.id ? data : item))
      setRenameOpen(false)
    } catch (err) { setError(getApiError(err)) }
  }

  return <section className="chat-page page-container">
    <div className="page-heading"><span className="eyebrow"><Bot size={15} /> AI receptionist</span><h1>How can we help?</h1><p>Ask about services, availability, booking, or cancellation.</p></div>
    <ErrorAlert message={error} />
    <div className="chat-shell">
      <aside className="chat-sidebar">
        <div className="profile-summary"><small>Chatting as</small><strong>{profile.customer_name || externalUserId}</strong><span>{externalUserId}</span></div>
        <button className="button button-primary full" onClick={createSession}><Plus size={16} /> New conversation</button>
        <div className="session-list">{sessions.map((session) => <button key={session.id} className={session.id === sessionId ? 'active' : ''} onClick={() => setSessionId(session.id)}><MessageCircle size={16} /><span>{session.title || 'Conversation'}<small>{new Date(session.created_at).toLocaleDateString()}</small></span></button>)}</div>
      </aside>
      <div className="conversation">
        <div className="conversation-head"><div><Bot size={19} /><span><strong>Slotely assistant</strong><small>Usually replies instantly</small></span></div>{sessionId && <div className="row-actions"><button className="icon-button" onClick={() => { const current = sessions.find((item) => item.id === sessionId); setRenameTitle(current?.title || ''); setRenameOpen(true) }} title="Rename conversation"><Pencil size={17} /></button><button className="icon-button" onClick={archive} title="Archive conversation"><Archive size={18} /></button></div>}</div>
        <div className="message-list" ref={messageListRef} onScroll={trackScroll}>{loading ? <Loading label="Loading conversation" /> : !sessionId ? <EmptyState title="Start a conversation" text="Create a session to talk with the booking assistant." /> : <>
          {messages.map((message) => <div key={message.id} className={`message ${message.role}`}><span>{message.content}</span></div>)}
          {responding && <div className="message assistant typing"><i></i><i></i><i></i></div>}<div ref={endRef} />
        </>}{showJump && <button type="button" className="jump-latest" onClick={() => scrollToLatest()}>Jump to latest</button>}</div>
        <form className="message-form" onSubmit={send}><input value={content} onChange={(event) => setContent(event.target.value)} disabled={!sessionId || responding} placeholder={sessionId ? 'Type your message…' : 'Start a conversation first'} aria-label="Chat message" /><button type="submit" disabled={!content.trim() || responding}><Send size={18} /></button></form>
      </div>
    </div>
    <Modal open={renameOpen} title="Rename conversation" onClose={() => setRenameOpen(false)}><form className="stack-form" onSubmit={rename}><Field label="Conversation title" hint="Use 2–6 words."><input value={renameTitle} onChange={(event) => setRenameTitle(event.target.value)} maxLength="80" /></Field><div className="button-row"><button type="button" className="button button-secondary" onClick={() => setRenameOpen(false)}>Cancel</button><button className="button button-primary">Rename</button></div></form></Modal>
  </section>
}
