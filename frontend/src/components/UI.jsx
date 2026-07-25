import { AlertCircle, CalendarDays, LoaderCircle } from 'lucide-react'

export function Loading({ label = 'Loading' }) {
  return <div className="loading"><LoaderCircle className="animate-spin" size={20} /> {label}…</div>
}

export function SkeletonCards({ count = 3 }) {
  return <div className="skeleton-grid" aria-label="Loading content">
    {Array.from({ length: count }, (_, index) => <div className="skeleton-card" key={index}><i></i><span></span><span></span><span></span></div>)}
  </div>
}

export function ErrorAlert({ message }) {
  if (!message) return null
  return <div className="alert alert-error" role="alert"><AlertCircle size={18} /> <span>{message}</span></div>
}

export function SuccessAlert({ message }) {
  if (!message) return null
  return <div className="alert alert-success">{message}</div>
}

export function EmptyState({ title = 'Nothing here yet', text = 'New items will appear here.' }) {
  return <div className="empty-state"><CalendarDays size={26} /><h3>{title}</h3><p>{text}</p></div>
}

export function Field({ label, error, children, hint }) {
  return <label className="field"><span>{label}</span>{children}{hint && <small>{hint}</small>}{error && <small className="field-error">{error}</small>}</label>
}

export function Modal({ open, title, children, onClose }) {
  if (!open) return null
  return <div className="modal-backdrop" role="presentation" onMouseDown={onClose}>
    <div className="modal-card" role="dialog" aria-modal="true" aria-label={title} onMouseDown={(event) => event.stopPropagation()}>
      <h2>{title}</h2>{children}
    </div>
  </div>
}
