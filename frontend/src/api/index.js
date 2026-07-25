import client from './client'

export const companiesApi = {
  list: (includeInactive = false) =>
    client.get('/companies/', { params: { include_inactive: includeInactive } }),
  get: (companyId) => client.get(`/companies/${companyId}`),
}

export const servicesApi = {
  list: (companyId) => client.get(`/companies/${companyId}/services/`),
  create: (companyId, data) => client.post(`/companies/${companyId}/services/`, data),
  update: (companyId, serviceId, data) =>
    client.patch(`/companies/${companyId}/services/${serviceId}`, data),
}

export const appointmentsApi = {
  availability: (companyId, serviceId, requestedDate) =>
    client.get(`/companies/${companyId}/availability/`, {
      params: { service_id: serviceId, requested_date: requestedDate },
    }),
  create: (companyId, data) => client.post(`/companies/${companyId}/appointments/`, data),
  mine: (companyId, externalUserId) =>
    client.get(`/companies/${companyId}/appointments/my`, {
      params: { external_user_id: externalUserId },
    }),
  lookup: (companyId, customerEmail) =>
    client.get(`/companies/${companyId}/appointments/lookup`, {
      params: { customer_email: customerEmail },
    }),
  list: (companyId, params) =>
    client.get(`/companies/${companyId}/appointments/`, { params }),
  cancel: (companyId, appointmentId, cancellationReason) =>
    client.post(`/companies/${companyId}/appointments/${appointmentId}/cancel`, {
      cancellation_reason: cancellationReason || null,
    }),
  status: (companyId, appointmentId, status) =>
    client.patch(`/companies/${companyId}/appointments/${appointmentId}/status`, { status }),
}

export const chatApi = {
  sessions: (companyId, externalUserId) =>
    client.get(`/companies/${companyId}/chat/sessions`, {
      params: externalUserId ? { external_user_id: externalUserId } : {},
    }),
  createSession: (companyId, data) =>
    client.post(`/companies/${companyId}/chat/sessions`, data),
  messages: (companyId, sessionId) =>
    client.get(`/companies/${companyId}/chat/sessions/${sessionId}/messages`),
  send: (companyId, sessionId, data) =>
    client.post(`/companies/${companyId}/chat/sessions/${sessionId}/messages`, data),
  archive: (companyId, sessionId) =>
    client.delete(`/companies/${companyId}/chat/sessions/${sessionId}`),
  rename: (companyId, sessionId, title) =>
    client.patch(`/companies/${companyId}/chat/sessions/${sessionId}`, { title }),
}

export const conversationsApi = {
  mine: (companyId, params) =>
    client.get(`/companies/${companyId}/customer-conversations`, { params }),
  create: (companyId, data) =>
    client.post(`/companies/${companyId}/customer-conversations`, data),
  messages: (companyId, conversationId, params) =>
    client.get(`/companies/${companyId}/customer-conversations/${conversationId}/messages`, { params }),
  send: (companyId, conversationId, data) =>
    client.post(`/companies/${companyId}/customer-conversations/${conversationId}/messages`, data),
  adminList: (companyId, params = {}) =>
    client.get(`/admin/companies/${companyId}/customer-conversations`, { params }),
  adminMessages: (companyId, conversationId) =>
    client.get(`/admin/companies/${companyId}/customer-conversations/${conversationId}/messages`),
  adminSend: (companyId, conversationId, content) =>
    client.post(`/admin/companies/${companyId}/customer-conversations/${conversationId}/messages`, { content }),
  adminStatus: (companyId, conversationId, status) =>
    client.patch(`/admin/companies/${companyId}/customer-conversations/${conversationId}`, { status }),
}

export const scheduleApi = {
  weekly: (companyId) => client.get(`/companies/${companyId}/admin/schedule/weekly`),
  createWeekly: (companyId, data) =>
    client.post(`/companies/${companyId}/admin/schedule/weekly`, data),
  updateWeekly: (companyId, id, data) =>
    client.patch(`/companies/${companyId}/admin/schedule/weekly/${id}`, data),
  deleteWeekly: (companyId, id) =>
    client.delete(`/companies/${companyId}/admin/schedule/weekly/${id}`),
  overrides: (companyId) => client.get(`/companies/${companyId}/admin/schedule/override`),
  saveOverride: (companyId, data) =>
    client.post(`/companies/${companyId}/admin/schedule/override`, data),
  deleteOverride: (companyId, id) =>
    client.delete(`/companies/${companyId}/admin/schedule/override/${id}`),
  breaks: (companyId) => client.get(`/companies/${companyId}/admin/schedule/break`),
  createBreak: (companyId, data) =>
    client.post(`/companies/${companyId}/admin/schedule/break`, data),
  updateBreak: (companyId, id, data) =>
    client.patch(`/companies/${companyId}/admin/schedule/break/${id}`, data),
  deleteBreak: (companyId, id) =>
    client.delete(`/companies/${companyId}/admin/schedule/break/${id}`),
}

export const requestsApi = {
  create: (companyId, data) =>
    client.post(`/companies/${companyId}/schedule-requests/`, data),
  list: (companyId) => client.get(`/companies/${companyId}/schedule-requests/`),
  mine: (companyId, externalUserId) =>
    client.get(`/companies/${companyId}/schedule-requests/my`, {
      params: { external_user_id: externalUserId },
    }),
  status: (companyId, id, data) =>
    client.patch(`/companies/${companyId}/schedule-requests/${id}/status`, data),
}

export const dashboardApi = {
  get: (companyId) => client.get(`/admin/companies/${companyId}/dashboard/`),
}

export const superadminApi = {
  getOpenAI: (secret) =>
    client.get('/superadmin/settings/openai', {
      headers: { 'X-Slotely-Superadmin-Key': secret },
    }),
  updateOpenAI: (secret, apiKey) =>
    client.put('/superadmin/settings/openai', { api_key: apiKey }, {
      headers: { 'X-Slotely-Superadmin-Key': secret },
    }),
  deleteOpenAI: (secret) =>
    client.delete('/superadmin/settings/openai', {
      headers: { 'X-Slotely-Superadmin-Key': secret },
    }),
}
