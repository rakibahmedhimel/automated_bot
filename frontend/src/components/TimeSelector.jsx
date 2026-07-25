import { useState } from 'react'

const HOURS = Array.from({ length: 12 }, (_, index) =>
  String(index + 1).padStart(2, '0'))
const MINUTES = ['00', '10', '20', '30', '40', '50']

function parseTime(value) {
  if (!value) return { hour: '', minute: '', period: '' }
  const [rawHour, minute] = value.split(':')
  const hour24 = Number(rawHour)
  return {
    hour: String(hour24 % 12 || 12).padStart(2, '0'),
    minute,
    period: hour24 >= 12 ? 'PM' : 'AM',
  }
}

function toBackendTime(parts) {
  if (!parts.hour || !parts.minute || !parts.period) return ''
  let hour = Number(parts.hour) % 12
  if (parts.period === 'PM') hour += 12
  return `${String(hour).padStart(2, '0')}:${parts.minute}:00`
}

export default function TimeSelector({ label, value, onChange, required = false }) {
  const [parts, setParts] = useState(() => parseTime(value))
  const [lastValue, setLastValue] = useState(value)
  if (value !== lastValue) {
    setLastValue(value)
    setParts(parseTime(value))
  }
  const update = (field, nextValue) => {
    const next = { ...parts, [field]: nextValue }
    setParts(next)
    onChange(toBackendTime(next))
  }
  return <fieldset className="time-selector">
    <legend>{label}</legend>
    <label><span>Hour</span><select required={required} aria-label={`${label} hour`} value={parts.hour} onChange={(event) => update('hour', event.target.value)}><option value="">--</option>{HOURS.map((hour) => <option key={hour}>{hour}</option>)}</select></label>
    <label><span>Minute</span><select required={required} aria-label={`${label} minute`} value={parts.minute} onChange={(event) => update('minute', event.target.value)}><option value="">--</option>{MINUTES.map((minute) => <option key={minute}>{minute}</option>)}</select></label>
    <label><span>AM/PM</span><select required={required} aria-label={`${label} AM or PM`} value={parts.period} onChange={(event) => update('period', event.target.value)}><option value="">--</option><option>AM</option><option>PM</option></select></label>
  </fieldset>
}
