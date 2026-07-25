import { Component } from 'react'
import { AlertTriangle } from 'lucide-react'

export default class AdminErrorBoundary extends Component {
  state = { error: null }

  static getDerivedStateFromError(error) {
    return { error }
  }

  componentDidCatch(error, info) {
    if (import.meta.env.DEV) {
      console.error('[Slotely Admin]', error, info)
    }
  }

  render() {
    if (!this.state.error) return this.props.children
    return <section className="admin-route-error">
      <AlertTriangle size={28} />
      <h1>This admin page could not render</h1>
      <p>{this.state.error.message}</p>
      <button className="button button-primary" onClick={() => window.location.reload()}>Reload page</button>
    </section>
  }
}
