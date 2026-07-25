import { ArrowRight, CalendarCheck2, ShieldCheck, Sparkles, Zap } from 'lucide-react'
import { useEffect, useState } from 'react'
import { companiesApi } from '../api'
import { getApiError } from '../api/client'
import { CompanyCard } from '../components/Cards'
import { EmptyState, ErrorAlert, SkeletonCards } from '../components/UI'

export default function LandingPage() {
  const [companies, setCompanies] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    companiesApi.list().then(({ data }) => setCompanies(data)).catch((err) => setError(getApiError(err))).finally(() => setLoading(false))
  }, [])

  return <>
    <section className="hero-section">
      <div className="hero-copy"><span className="eyebrow"><Sparkles size={15} /> Appointment booking, reimagined</span>
        <h1>Your time deserves a <em>better</em> booking experience.</h1>
        <p>Discover trusted businesses, find the perfect time, and book in moments. No phone calls, no back-and-forth.</p>
        <a href="#companies" className="button button-primary">Find a business <ArrowRight size={17} /></a>
        <div className="trust-row"><span><Zap size={15} /> Instant confirmation</span><span><ShieldCheck size={15} /> Secure details</span><span><CalendarCheck2 size={15} /> Easy management</span></div>
      </div>
      <div className="hero-visual">
        <div className="floating-card card-one"><span>Tomorrow</span><strong>10:30 AM</strong><small>Available</small></div>
        <div className="calendar-art"><div className="calendar-head">July 2026</div><div className="calendar-grid">{['M','T','W','T','F','S','S',20,21,22,23,24,25,26,27,28,29,30,31,1,2].map((day, index) => <span key={index} className={day === 28 ? 'picked' : ''}>{day}</span>)}</div></div>
        <div className="floating-card card-two"><CalendarCheck2 /><div><strong>You're booked!</strong><small>Confirmation sent</small></div></div>
      </div>
    </section>
    <section id="companies" className="section-block">
      <div className="section-heading"><span className="eyebrow">Available now</span><h2>Choose where to book</h2><p>Active businesses accepting appointments through Slotely.</p></div>
      <ErrorAlert message={error} />
      {loading ? <SkeletonCards /> : companies.length ? <div className="company-grid">{companies.map((company) => <CompanyCard key={company.id} company={company} />)}</div> : <EmptyState title="No businesses are accepting bookings" />}
    </section>
  </>
}
