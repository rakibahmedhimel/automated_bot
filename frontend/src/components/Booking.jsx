import { Check } from 'lucide-react'

export function BookingStepper({ current }) {
  const steps = ['Service', 'Date & time', 'Your details', 'Confirm']
  return <ol className="stepper">{steps.map((step, index) => {
    const number = index + 1
    return <li key={step} className={number <= current ? 'active' : ''}>
      <span>{number < current ? <Check size={14} /> : number}</span><small>{step}</small>
    </li>
  })}</ol>
}

export function TimeSlotGrid({ slots, selected, onSelect }) {
  return <div className="slot-grid">{slots.map((slot) =>
    <button key={`${slot.start_time}-${slot.end_time}`} type="button" className={selected?.start_time === slot.start_time ? 'selected' : ''} onClick={() => onSelect(slot)}>
      {slot.start_time.slice(0, 5)}
    </button>,
  )}</div>
}
