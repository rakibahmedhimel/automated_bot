import { KeyRound, Trash2 } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { superadminApi } from '../api'
import { getApiError } from '../api/client'
import { ErrorAlert, Field, SuccessAlert } from '../components/UI'

export default function SuperadminSettingsPage() {
  const [secret, setSecret] = useState(
    () => sessionStorage.getItem('slotely_superadmin_secret') || '',
  )
  const [apiKey, setApiKey] = useState('')
  const [setting, setSetting] = useState(null)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [loading, setLoading] = useState(false)

  const rememberSecret = (value) => {
    setSecret(value)
    if (value) sessionStorage.setItem('slotely_superadmin_secret', value)
    else sessionStorage.removeItem('slotely_superadmin_secret')
  }
  const load = async () => {
    setLoading(true); setError(''); setSuccess('')
    try {
      const { data } = await superadminApi.getOpenAI(secret)
      setSetting(data)
    } catch (err) { setError(getApiError(err)) }
    finally { setLoading(false) }
  }
  const save = async (event) => {
    event.preventDefault()
    setLoading(true); setError(''); setSuccess('')
    try {
      const { data } = await superadminApi.updateOpenAI(secret, apiKey)
      setSetting(data)
      setApiKey('')
      setSuccess('OpenAI credential updated. The full key is no longer available in this page.')
    } catch (err) { setError(getApiError(err)) }
    finally { setLoading(false) }
  }
  const remove = async () => {
    setLoading(true); setError(''); setSuccess('')
    try {
      const { data } = await superadminApi.deleteOpenAI(secret)
      setSetting(data)
      setSuccess('Stored credential removed. Environment fallback is now used when configured.')
    } catch (err) { setError(getApiError(err)) }
    finally { setLoading(false) }
  }

  return <main className="superadmin-page"><div className="superadmin-card">
    <Link to="/" className="brand">Slotely <span>Super admin</span></Link>
    <div className="admin-dev-warning">Temporary super-admin protection is enabled. Replace this with real authentication before production.</div>
    <span className="eyebrow">Global configuration</span><h1>OpenAI credential</h1><p>This setting is global and is not accessible to company admins.</p>
    <ErrorAlert message={error} /><SuccessAlert message={success} />
    <div className="stack-form"><Field label="Temporary super-admin secret"><input type="password" autoComplete="off" value={secret} onChange={(event) => rememberSecret(event.target.value)} /></Field><button className="button button-secondary" disabled={!secret || loading} onClick={load}>Load current setting</button></div>
    {setting && <div className="credential-status"><KeyRound /><div><small>Current credential</small><strong>{setting.masked_key || 'Not configured'}</strong><span>{setting.updated_at ? `Updated ${new Date(setting.updated_at).toLocaleString()}` : 'Environment fallback or no stored key'}</span></div></div>}
    <form className="stack-form" onSubmit={save}><Field label="New OpenAI API key" hint="The key is sent once and is never stored in browser storage."><input required type="password" autoComplete="new-password" value={apiKey} onChange={(event) => setApiKey(event.target.value)} placeholder="sk-…" /></Field><div className="button-row"><button className="button button-primary" disabled={!secret || !apiKey || loading}>Save encrypted key</button><button type="button" className="button button-danger" disabled={!secret || loading} onClick={remove}><Trash2 size={16} /> Delete stored key</button></div></form>
  </div></main>
}
