import api from './client.js'

export const webApi = {
  // Public
  listEvents: () => api.get('/events'),
  getEvent: (slug) => api.get(`/events/${slug}`),
  searchBib: (slug, bib) => api.get(`/events/${slug}/search`, { params: { bib } }),
  checkout: (data) => api.post('/checkout', data),

  // Admin
  publish: (eventId) => api.post('/publish', { event_id: eventId }),
  adminListEvents: () => api.get('/admin/events'),
  adminUpdateEvent: (id, data) => api.put(`/admin/events/${id}`, data),
  adminStats: () => api.get('/admin/stats'),
}
