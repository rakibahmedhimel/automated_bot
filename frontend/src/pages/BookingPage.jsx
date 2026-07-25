import { ArrowLeft, ArrowRight, CalendarCheck2, CheckCircle2 } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { appointmentsApi, companiesApi, requestsApi, scheduleApi, servicesApi } from '../api'
import { getApiError, getAvailabilityError } from '../api/client'
import { BookingStepper, TimeSlotGrid } from '../components/Booking'
import TimeSelector from '../components/TimeSelector'
import { ServiceCard } from '../components/Cards'
import { ErrorAlert, Field, Loading, Modal, SuccessAlert } from '../components/UI'
import { useTestCustomer } from '../hooks/useTestCustomer'
import { formatDate, formatTime, todayInput } from '../utils/format'

export default function BookingPage() {
  const { companyId } = useParams()
  const [company, setCompany] = useState(null)
  const [services, setServices] = useState([])
  const [serviceId, setServiceId] = useState('')
  const [date, setDate] = useState('')
  const [slots, setSlots] = useState([])
  const [slot, setSlot] = useState(null)
  const [step, setStep] = useState(1)
  const [profile] = useTestCustomer()
  const [details, setDetails] = useState(() => ({
    external_user_id: profile.external_user_id,
    customer_name: profile.customer_name,
    customer_email: profile.customer_email,
    customer_phone: profile.customer_phone,
  }))
  const [loading, setLoading] = useState(true)
  const [slotsLoading, setSlotsLoading] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [availabilityMessage, setAvailabilityMessage] = useState('')
  const [booking, setBooking] = useState(null)
  const [requestOpen, setRequestOpen] = useState(false)
  const [requestSuccess, setRequestSuccess] = useState('')
  const [requestForm, setRequestForm] = useState({
    preferred_start_time: '',
    preferred_end_time: '',
    message: '',
  })
  const service = useMemo(() => services.find((item) => item.id === serviceId), [services, serviceId])

  useEffect(() => {
    localStorage.setItem('slotely_company_id', companyId)
    Promise.all([companiesApi.get(companyId), servicesApi.list(companyId)])
      .then(([companyResponse, servicesResponse]) => {
        setCompany(companyResponse.data)
        setServices(servicesResponse.data)
      }).catch((err) => setError(getApiError(err))).finally(() => setLoading(false))
  }, [companyId])

  const chooseService = (selected) => {
    setServiceId(selected.id); setDate(''); setSlot(null); setSlots([]); setError(''); setAvailabilityMessage(''); setStep(2)
  }

  const loadAvailability = async (nextDate) => {
    setDate(nextDate); setSlot(null); setSlots([]); setError(''); setAvailabilityMessage('')
    if (!nextDate || !serviceId) return
    setSlotsLoading(true)
    try {
      const { data } = await appointmentsApi.availability(companyId, serviceId, nextDate)
      setSlots(data.slots)
      if (!data.slots.length) {
        let message = 'No available slots remain on this date.'
        try {
          const [weeklyResponse, overrideResponse] = await Promise.all([
            scheduleApi.weekly(companyId),
            scheduleApi.overrides(companyId),
          ])
          const override = overrideResponse.data.find((item) => item.date === nextDate)
          const dayOfWeek = (new Date(`${nextDate}T00:00:00`).getDay() + 6) % 7
          const weeklyPeriods = weeklyResponse.data.filter(
            (item) => item.day_of_week === dayOfWeek && item.is_active,
          )
          if (override?.is_closed) message = 'The company is closed on this date.'
          else if (override && !override.periods?.length) message = 'No schedule is configured for this override date.'
          else if (!override && !weeklyPeriods.length) message = 'No weekly schedule is configured for this day.'
        } catch {
          // The availability response is still authoritative if diagnostics fail.
        }
        setAvailabilityMessage(message)
      }
    } catch (err) {
      setError(getAvailabilityError(err))
    } finally {
      setSlotsLoading(false)
    }
  }

  const submit = async () => {
    if (!serviceId || !date || !slot) return setError('Choose a service, date, and time before booking.')
    setSubmitting(true); setError('')
    try {
      const payload = {
        service_id: serviceId,
        appointment_date: date,
        start_time: slot.start_time,
        external_user_id: details.external_user_id || null,
        customer_name: details.customer_name || null,
        customer_email: details.customer_email || null,
        customer_phone: details.customer_phone || null,
      }
      const { data } = await appointmentsApi.create(companyId, payload)
      setBooking(data); setStep(4)
    } catch (err) {
      setError(getApiError(err))
    } finally {
      setSubmitting(false)
    }
  }
  const submitScheduleRequest = async (event) => {
    event.preventDefault()
    if (
      requestForm.preferred_start_time
      && requestForm.preferred_end_time
      && requestForm.preferred_start_time >= requestForm.preferred_end_time
    ) {
      return setError('Preferred start time must be before preferred end time.')
    }
    setSubmitting(true)
    setError('')
    try {
      await requestsApi.create(companyId, {
        service_id: serviceId,
        requested_date: date,
        preferred_start_time: requestForm.preferred_start_time || null,
        preferred_end_time: requestForm.preferred_end_time || null,
        message: requestForm.message || null,
        external_user_id: details.external_user_id || null,
        customer_name: details.customer_name || null,
        customer_email: details.customer_email || null,
        customer_phone: details.customer_phone || null,
      })
      setRequestSuccess('Schedule request sent. The business can review it from the admin dashboard.')
    } catch (err) {
      setError(getApiError(err))
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) return <div className="page-container"><Loading label="Preparing your booking" /></div>
  if (!company) return <div className="page-container"><ErrorAlert message={error || 'Company not found'} /></div>
  if (booking) return <section className="confirmation-page">
    <div className="confirmation-icon"><CheckCircle2 size={38} /></div><span className="eyebrow">Booking confirmed</span>
    <h1>You’re all set.</h1><p>Your appointment with {company.name} is confirmed.</p>
    <div className="confirmation-ticket"><div><small>Service</small><strong>{service?.name}</strong></div><div><small>Date</small><strong>{formatDate(booking.appointment_date)}</strong></div><div><small>Time</small><strong>{formatTime(booking.start_time)} – {formatTime(booking.end_time)}</strong></div><div><small>Confirmation</small><strong className="mono">{booking.id}</strong></div></div>
    <div className="button-row"><Link className="button button-primary" to={`/companies/${companyId}/appointments`}>View my appointments</Link><button className="button button-secondary" onClick={() => { setBooking(null); setStep(1); setServiceId(''); setDate(''); setSlot(null) }}>Book another</button></div>
  </section>

  return <section className="booking-page">
    <div className="booking-intro"><Link to="/" className="back-link"><ArrowLeft size={16} /> All businesses</Link><span className="eyebrow">Book with confidence</span><h1>{company.name}</h1><p>{company.description || `Select a service and a time that works for you.`}</p><Link className="button button-secondary" to={`/companies/${companyId}/schedule-request`}>Request a custom time</Link></div>
    <div className="booking-card"><BookingStepper current={step} /><ErrorAlert message={error} />
      {step === 1 && <div className="booking-panel"><div className="panel-heading"><span>01</span><div><h2>What can we help with?</h2><p>Choose the service you’d like to book.</p></div></div>
        <div className="service-grid">{services.map((item) => <ServiceCard key={item.id} service={item} selected={item.id === serviceId} onClick={() => chooseService(item)} />)}</div>
      </div>}
      {step === 2 && <div className="booking-panel"><div className="panel-heading"><span>02</span><div><h2>Pick your date and time</h2><p>{service?.name} · {service?.duration_minutes} minutes</p></div></div>
        <Field label="Appointment date"><input type="date" min={todayInput()} value={date} onChange={(event) => loadAvailability(event.target.value)} /></Field>
        {slotsLoading ? <Loading label="Checking availability" /> : date && (slots.length ? <><h3 className="subheading">Available times</h3><TimeSlotGrid slots={slots} selected={slot} onSelect={setSlot} /></> : availabilityMessage && <div className="inline-empty">{availabilityMessage}<button className="button-link" type="button" onClick={() => setRequestOpen(true)}>Request a different time</button></div>)}
        <div className="button-row split"><button className="button button-secondary" onClick={() => setStep(1)}><ArrowLeft size={16} /> Back</button><button className="button button-primary" disabled={!slot} onClick={() => setStep(3)}>Continue <ArrowRight size={16} /></button></div>
      </div>}
      {step === 3 && <div className="booking-panel"><div className="panel-heading"><span>03</span><div><h2>Tell us about you</h2><p>These details help the business recognize your booking.</p></div></div>
        <div className="form-grid">
          <Field label="External user ID" hint="Prefilled from your test customer profile."><input value={details.external_user_id} onChange={(event) => setDetails({ ...details, external_user_id: event.target.value })} placeholder="e.g. test-user-123" /></Field>
          <Field label="Your name"><input value={details.customer_name} onChange={(event) => setDetails({ ...details, customer_name: event.target.value })} placeholder="Your full name" /></Field>
          <Field label="Email"><input type="email" value={details.customer_email} onChange={(event) => setDetails({ ...details, customer_email: event.target.value })} placeholder="you@example.com" /></Field>
          <Field label="Phone"><input type="tel" value={details.customer_phone} onChange={(event) => setDetails({ ...details, customer_phone: event.target.value })} placeholder="+880..." /></Field>
        </div>
        <div className="booking-summary"><CalendarCheck2 /><div><strong>{service?.name}</strong><span>{formatDate(date)} at {formatTime(slot?.start_time)}</span></div></div>
        <div className="button-row split"><button className="button button-secondary" onClick={() => setStep(2)}><ArrowLeft size={16} /> Back</button><button className="button button-primary" disabled={submitting} onClick={submit}>{submitting ? 'Confirming…' : 'Confirm booking'} <CheckCircle2 size={17} /></button></div>
      </div>}
    </div>
    <Modal open={requestOpen} title="Request a time" onClose={() => setRequestOpen(false)}>
      <p>Send a request for {service?.name} on {formatDate(date)}. Your test profile will be included automatically.</p>
      <SuccessAlert message={requestSuccess} />
      <form className="stack-form" onSubmit={submitScheduleRequest}>
        <div className="form-grid"><TimeSelector label="Preferred start" value={requestForm.preferred_start_time} onChange={(value) => setRequestForm({ ...requestForm, preferred_start_time: value })} /><TimeSelector label="Preferred end" value={requestForm.preferred_end_time} onChange={(value) => setRequestForm({ ...requestForm, preferred_end_time: value })} /></div>
        <Field label="Message"><textarea rows="3" value={requestForm.message} onChange={(event) => setRequestForm({ ...requestForm, message: event.target.value })} placeholder="Anything the business should know?" /></Field>
        <div className="button-row"><button type="button" className="button button-secondary" onClick={() => setRequestOpen(false)}>Close</button><button className="button button-primary" disabled={submitting || Boolean(requestSuccess)}>Send request</button></div>
      </form>
    </Modal>
  </section>
}
