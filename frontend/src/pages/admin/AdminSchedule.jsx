import { Edit3, Plus, Trash2 } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { scheduleApi } from '../../api'
import { getApiError } from '../../api/client'
import { EmptyState, ErrorAlert, Field, Loading, SuccessAlert } from '../../components/UI'
import { DAY_NAMES, formatDate, formatTime } from '../../utils/format'

const period = () => ({ start_time: '09:00', end_time: '17:00' })
const validPeriods = (periods) => periods.every((item) => item.start_time < item.end_time)

export default function AdminSchedule() {
  const { companyId } = useParams()
  const [weekly, setWeekly] = useState([])
  const [overrides, setOverrides] = useState([])
  const [breaks, setBreaks] = useState([])
  const [weeklyForm, setWeeklyForm] = useState({ day_of_week: 0, periods: [period()] })
  const [weeklyEdit, setWeeklyEdit] = useState(null)
  const [overrideForm, setOverrideForm] = useState({ date: '', is_closed: false, reason: '', periods: [period()] })
  const [breakForm, setBreakForm] = useState({ date: '', start_time: '12:00', end_time: '13:00', break_type: 'lunch', reason: '' })
  const [breakEdit, setBreakEdit] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const load = async () => {
    setLoading(true)
    try {
      const [weeklyResponse, overrideResponse, breakResponse] = await Promise.all([scheduleApi.weekly(companyId), scheduleApi.overrides(companyId), scheduleApi.breaks(companyId)])
      setWeekly(weeklyResponse.data); setOverrides(overrideResponse.data); setBreaks(breakResponse.data)
    } catch (err) { setError(getApiError(err)) } finally { setLoading(false) }
  }
  useEffect(() => {
    Promise.all([scheduleApi.weekly(companyId), scheduleApi.overrides(companyId), scheduleApi.breaks(companyId)])
      .then(([weeklyResponse, overrideResponse, breakResponse]) => {
        setWeekly(weeklyResponse.data)
        setOverrides(overrideResponse.data)
        setBreaks(breakResponse.data)
      })
      .catch((err) => setError(getApiError(err)))
      .finally(() => setLoading(false))
  }, [companyId])
  const fail = (err) => setError(getApiError(err))
  const successReload = (message) => { setSuccess(message); setError(''); load() }

  const submitWeekly = async (event) => {
    event.preventDefault()
    if (!validPeriods(weeklyForm.periods)) return setError('Every weekly period must start before it ends.')
    try {
      if (weeklyEdit) {
        await scheduleApi.updateWeekly(companyId, weeklyEdit, { day_of_week: Number(weeklyForm.day_of_week), ...weeklyForm.periods[0] })
        setWeeklyEdit(null)
      } else await scheduleApi.createWeekly(companyId, { ...weeklyForm, day_of_week: Number(weeklyForm.day_of_week) })
      setWeeklyForm({ day_of_week: 0, periods: [period()] }); successReload('Weekly schedule saved.')
    } catch (err) { fail(err) }
  }
  const editWeekly = (item) => { setWeeklyEdit(item.id); setWeeklyForm({ day_of_week: item.day_of_week, periods: [{ start_time: item.start_time.slice(0, 5), end_time: item.end_time.slice(0, 5) }] }) }
  const submitOverride = async (event) => {
    event.preventDefault()
    if (!overrideForm.is_closed && !validPeriods(overrideForm.periods)) return setError('Every override period must start before it ends.')
    try {
      await scheduleApi.saveOverride(companyId, { ...overrideForm, reason: overrideForm.reason || null, periods: overrideForm.is_closed ? [] : overrideForm.periods })
      setOverrideForm({ date: '', is_closed: false, reason: '', periods: [period()] }); successReload('Override saved or replaced.')
    } catch (err) { fail(err) }
  }
  const editOverride = (item) => setOverrideForm({ date: item.date, is_closed: item.is_closed, reason: item.reason || '', periods: item.periods?.length ? item.periods.map((p) => ({ start_time: p.start_time.slice(0, 5), end_time: p.end_time.slice(0, 5) })) : [period()] })
  const submitBreak = async (event) => {
    event.preventDefault()
    if (breakForm.start_time >= breakForm.end_time) return setError('Break start time must be before end time.')
    try {
      const payload = { ...breakForm, reason: breakForm.reason || null }
      if (breakEdit) await scheduleApi.updateBreak(companyId, breakEdit, payload)
      else await scheduleApi.createBreak(companyId, payload)
      setBreakEdit(null); setBreakForm({ date: '', start_time: '12:00', end_time: '13:00', break_type: 'lunch', reason: '' }); successReload('Break saved.')
    } catch (err) { fail(err) }
  }
  const editBreak = (item) => { setBreakEdit(item.id); setBreakForm({ date: item.date, start_time: item.start_time.slice(0, 5), end_time: item.end_time.slice(0, 5), break_type: item.break_type, reason: item.reason || '' }) }
  const remove = async (action, message) => { try { await action(); successReload(message) } catch (err) { fail(err) } }
  const setPeriodValue = (form, setForm, index, key, value) => setForm({ ...form, periods: form.periods.map((item, itemIndex) => itemIndex === index ? { ...item, [key]: value } : item) })

  return <><div className="admin-heading"><span className="eyebrow">Availability rules</span><h1>Schedule</h1><p>Manage regular hours, date overrides, and breaks.</p></div><ErrorAlert message={error} /><SuccessAlert message={success} />
    {loading ? <Loading /> : <div className="schedule-sections">
      <section className="admin-card"><div className="card-heading"><div><h2>Weekly schedule</h2><p>Add one or several periods for a weekday.</p></div></div>
        <form className="schedule-form" onSubmit={submitWeekly}><Field label="Day"><select value={weeklyForm.day_of_week} onChange={(e) => setWeeklyForm({ ...weeklyForm, day_of_week: Number(e.target.value) })}>{DAY_NAMES.map((day, index) => <option value={index} key={day}>{day}</option>)}</select></Field>
          {weeklyForm.periods.map((item, index) => <div className="period-row" key={index}><Field label="Starts"><input type="time" value={item.start_time} onChange={(e) => setPeriodValue(weeklyForm, setWeeklyForm, index, 'start_time', e.target.value)} /></Field><Field label="Ends"><input type="time" value={item.end_time} onChange={(e) => setPeriodValue(weeklyForm, setWeeklyForm, index, 'end_time', e.target.value)} /></Field>{weeklyForm.periods.length > 1 && <button type="button" className="icon-button danger" onClick={() => setWeeklyForm({ ...weeklyForm, periods: weeklyForm.periods.filter((_, i) => i !== index) })}><Trash2 size={16} /></button>}</div>)}
          {!weeklyEdit && <button type="button" className="button-link" onClick={() => setWeeklyForm({ ...weeklyForm, periods: [...weeklyForm.periods, period()] })}><Plus size={15} /> Add another period</button>}<button className="button button-primary small">{weeklyEdit ? 'Update period' : 'Add schedule'}</button>
        </form>
        {weekly.length ? <div className="simple-list schedule-list">{weekly.map((item) => <div key={item.id}><span><strong>{DAY_NAMES[item.day_of_week]}</strong>{formatTime(item.start_time)} – {formatTime(item.end_time)}</span><span className="row-actions"><button className="icon-button" onClick={() => editWeekly(item)}><Edit3 size={15} /></button><button className="icon-button danger" onClick={() => remove(() => scheduleApi.deleteWeekly(companyId, item.id), 'Weekly period deleted.')}><Trash2 size={15} /></button></span></div>)}</div> : <EmptyState title="No weekly hours" />}</section>

      <section className="admin-card"><div className="card-heading"><div><h2>Date overrides</h2><p>Posting an existing date replaces its override.</p></div></div>
        <form className="schedule-form" onSubmit={submitOverride}><div className="form-grid"><Field label="Date"><input required type="date" value={overrideForm.date} onChange={(e) => setOverrideForm({ ...overrideForm, date: e.target.value })} /></Field><Field label="Reason"><input value={overrideForm.reason} onChange={(e) => setOverrideForm({ ...overrideForm, reason: e.target.value })} /></Field></div><label className="check-field"><input type="checkbox" checked={overrideForm.is_closed} onChange={(e) => setOverrideForm({ ...overrideForm, is_closed: e.target.checked })} /> Closed all day</label>
          {!overrideForm.is_closed && overrideForm.periods.map((item, index) => <div className="period-row" key={index}><Field label="Starts"><input type="time" value={item.start_time} onChange={(e) => setPeriodValue(overrideForm, setOverrideForm, index, 'start_time', e.target.value)} /></Field><Field label="Ends"><input type="time" value={item.end_time} onChange={(e) => setPeriodValue(overrideForm, setOverrideForm, index, 'end_time', e.target.value)} /></Field><button type="button" className="icon-button danger" onClick={() => setOverrideForm({ ...overrideForm, periods: overrideForm.periods.filter((_, i) => i !== index) })}><Trash2 size={16} /></button></div>)}
          {!overrideForm.is_closed && <button type="button" className="button-link" onClick={() => setOverrideForm({ ...overrideForm, periods: [...overrideForm.periods, period()] })}><Plus size={15} /> Add period</button>}<button className="button button-primary small">Save override</button>
        </form>
        {overrides.length ? <div className="simple-list schedule-list">{overrides.map((item) => <div key={item.id}><span><strong>{formatDate(item.date)}</strong>{item.is_closed ? 'Closed' : item.periods?.map((p) => `${formatTime(p.start_time)}–${formatTime(p.end_time)}`).join(', ') || 'No hours'}</span><span className="row-actions"><button className="icon-button" onClick={() => editOverride(item)}><Edit3 size={15} /></button><button className="icon-button danger" onClick={() => remove(() => scheduleApi.deleteOverride(companyId, item.id), 'Override deleted.')}><Trash2 size={15} /></button></span></div>)}</div> : <EmptyState title="No overrides" />}</section>

      <section className="admin-card"><div className="card-heading"><div><h2>Breaks</h2><p>Block unavailable time on a specific date.</p></div></div>
        <form className="schedule-form" onSubmit={submitBreak}><div className="form-grid"><Field label="Date"><input required type="date" value={breakForm.date} onChange={(e) => setBreakForm({ ...breakForm, date: e.target.value })} /></Field><Field label="Type"><input required value={breakForm.break_type} onChange={(e) => setBreakForm({ ...breakForm, break_type: e.target.value })} /></Field><Field label="Starts"><input required type="time" value={breakForm.start_time} onChange={(e) => setBreakForm({ ...breakForm, start_time: e.target.value })} /></Field><Field label="Ends"><input required type="time" value={breakForm.end_time} onChange={(e) => setBreakForm({ ...breakForm, end_time: e.target.value })} /></Field></div><Field label="Reason"><input value={breakForm.reason} onChange={(e) => setBreakForm({ ...breakForm, reason: e.target.value })} /></Field><button className="button button-primary small">{breakEdit ? 'Update break' : 'Add break'}</button></form>
        {breaks.length ? <div className="simple-list schedule-list">{breaks.map((item) => <div key={item.id}><span><strong>{formatDate(item.date)} · {item.break_type}</strong>{formatTime(item.start_time)} – {formatTime(item.end_time)}</span><span className="row-actions"><button className="icon-button" onClick={() => editBreak(item)}><Edit3 size={15} /></button><button className="icon-button danger" onClick={() => remove(() => scheduleApi.deleteBreak(companyId, item.id), 'Break deleted.')}><Trash2 size={15} /></button></span></div>)}</div> : <EmptyState title="No breaks" />}</section>
    </div>}
  </>
}
