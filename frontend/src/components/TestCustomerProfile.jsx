import { UserRound } from 'lucide-react'
import { useState } from 'react'
import { useTestCustomer } from '../hooks/useTestCustomer'
import { Field, Modal, SuccessAlert } from './UI'

export default function TestCustomerProfile() {
  const [profile, saveProfile] = useTestCustomer()
  const [draft, setDraft] = useState(profile)
  const [open, setOpen] = useState(false)
  const [saved, setSaved] = useState('')

  const submit = (event) => {
    event.preventDefault()
    saveProfile(draft)
    setSaved('Test customer profile saved on this device.')
  }

  return <>
    <button className="profile-button" type="button" onClick={() => { setDraft(profile); setSaved(''); setOpen(true) }}>
      <UserRound size={16} /><span>{profile.customer_name || 'Test profile'}</span>
    </button>
    <Modal open={open} title="Test customer profile" onClose={() => setOpen(false)}>
      <p>Temporary development identity stored only in this browser.</p>
      <SuccessAlert message={saved} />
      <form className="stack-form" onSubmit={submit}>
        <Field label="External user ID" hint="A test UUID is generated automatically when this is empty."><input value={draft.external_user_id} onChange={(event) => setDraft({ ...draft, external_user_id: event.target.value })} /></Field>
        <Field label="Customer name"><input value={draft.customer_name} onChange={(event) => setDraft({ ...draft, customer_name: event.target.value })} /></Field>
        <Field label="Email"><input type="email" value={draft.customer_email} onChange={(event) => setDraft({ ...draft, customer_email: event.target.value })} /></Field>
        <Field label="Phone"><input type="tel" value={draft.customer_phone} onChange={(event) => setDraft({ ...draft, customer_phone: event.target.value })} /></Field>
        <div className="button-row"><button type="button" className="button button-secondary" onClick={() => setOpen(false)}>Close</button><button className="button button-primary">Save profile</button></div>
      </form>
    </Modal>
  </>
}
