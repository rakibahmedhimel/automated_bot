import axios from 'axios'

const apiBaseUrl = (
  import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
).replace(/\/+$/, '')

const client = axios.create({
  baseURL: apiBaseUrl,
  headers: { 'Content-Type': 'application/json' },
  timeout: 30000,
})

client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (import.meta.env.DEV) {
      const method = error.config?.method?.toUpperCase() || 'REQUEST'
      const baseUrl = error.config?.baseURL || ''
      const requestUrl = error.config?.url || ''
      console.error('[Slotely API]', method, `${baseUrl}${requestUrl}`, {
        params: error.config?.params,
        status: error.response?.status,
        response: error.response?.data,
        message: error.message,
      })
    }
    return Promise.reject(error)
  },
)

export function getApiError(error) {
  const detail = error?.response?.data?.detail
  if (Array.isArray(detail)) {
    return detail.map((item) => item.msg).join(', ')
  }
  if (typeof detail === 'string') return detail
  if (error?.code === 'ECONNABORTED') return 'The request timed out. Please try again.'
  if (!error?.response) {
    return `Cannot connect to the Slotely API at ${client.defaults.baseURL}. Check that the API is running and reachable.`
  }
  if (error.response.status >= 500) {
    return 'The Slotely API encountered a server error while processing this request.'
  }
  return `Request failed (${error.response.status}). Please try again.`
}

export function getAvailabilityError(error) {
  const detail = error?.response?.data?.detail
  if (typeof detail === 'string') {
    const normalized = detail.toLowerCase()
    if (normalized.includes('past')) return 'That date is in the past. Choose today or a future date.'
    if (normalized.includes('company') || normalized.includes('service')) {
      return 'This company or service is no longer available.'
    }
    return detail
  }
  if (error?.response?.status === 422) {
    return `Availability request validation failed: ${getApiError(error)}`
  }
  if (error?.response?.status >= 500) {
    return 'The API could not calculate availability because of a server error. The company and service were found successfully.'
  }
  return getApiError(error)
}

export default client
