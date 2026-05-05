import api from './client'

export const eventsApi = {
  list() {
    return api.get('/events')
  },
  get(id) {
    return api.get(`/events/${id}`)
  },
  create(data) {
    return api.post('/events', data)
  },
  updateConfig(id, config) {
    return api.put(`/events/${id}/config`, config)
  },
  delete(id) {
    return api.delete(`/events/${id}`)
  },
  uploadSampleBib(id, file) {
    const form = new FormData()
    form.append('file', file)
    return api.post(`/events/${id}/sample-bib`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
}

export const webApi = {
  stats: () => api.get('/web/admin/stats'),
  listWebEvents: () => api.get('/web/admin/events'),
  updateWebEvent: (id, data) => api.put(`/web/admin/events/${id}`, data),
  publish: (eventId) => api.post('/web/publish', { event_id: eventId }),
  uploadCover: (webEventId, file) => {
    const form = new FormData()
    form.append('file', file)
    return api.post(`/web/admin/events/${webEventId}/cover`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  // Products
  listProducts: () => api.get('/web/admin/products'),
  createProduct: (data) => api.post('/web/admin/products', data),
  updateProduct: (id, data) => api.put(`/web/admin/products/${id}`, data),
  deleteProduct: (id) => api.delete(`/web/admin/products/${id}`),
  // Event products
  listEventProducts: (webEventId) => api.get(`/web/admin/events/${webEventId}/products`),
  addEventProduct: (webEventId, data) => api.post(`/web/admin/events/${webEventId}/products`, data),
  updateEventProduct: (wepId, data) => api.put(`/web/admin/event-products/${wepId}`, data),
  deleteEventProduct: (wepId) => api.delete(`/web/admin/event-products/${wepId}`),
}

export const mailingApi = {
  stats: () => api.get('/mailing/stats'),
  listEvents: () => api.get('/mailing/events'),
  list: () => api.get('/mailing'),
  get: (id) => api.get(`/mailing/${id}`),
  create: (data) => api.post('/mailing', data),
  update: (id, data) => api.put(`/mailing/${id}`, data),
  delete: (id) => api.delete(`/mailing/${id}`),
  send: (id) => api.post(`/mailing/${id}/send`),
  previewUrl: (id) => `/api/mailing/${id}/preview`,
}

export const triToolsApi = {
  // Participants
  importParticipants(eventId, file) {
    const form = new FormData()
    form.append('file', file)
    return api.post(`/events/${eventId}/participants/import`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  listParticipants(eventId) {
    return api.get(`/events/${eventId}/participants`)
  },
  rgpdDelete(eventId, bibNumber) {
    return api.delete(`/events/${eventId}/participants/rgpd/${bibNumber}`)
  },
  // Frames
  listFrames(eventId) {
    return api.get(`/events/${eventId}/frames`)
  },
  createFrame(eventId, file, config) {
    const form = new FormData()
    form.append('file', file)
    Object.entries(config).forEach(([k, v]) => form.append(k, v))
    return api.post(`/events/${eventId}/frames`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  updateFrame(eventId, frameId, data) {
    return api.put(`/events/${eventId}/frames/${frameId}`, data)
  },
  deleteFrame(eventId, frameId) {
    return api.delete(`/events/${eventId}/frames/${frameId}`)
  },
  // Exports
  exportPhotosPerBib(eventId) {
    return api.get(`/events/${eventId}/export/photos-per-bib`, { responseType: 'blob' })
  },
  exportPhotoCount(eventId) {
    return api.get(`/events/${eventId}/export/photo-count`, { responseType: 'blob' })
  },
  downloadPack(eventId, bibNumber) {
    return api.get(`/events/${eventId}/export/pack/${bibNumber}`, { responseType: 'blob' })
  },
  generateFramedPack(eventId, frameId, bibNumber) {
    return api.post(`/events/${eventId}/frames/${frameId}/generate-pack/${bibNumber}`, null, { responseType: 'blob' })
  },
}

export const triOverviewApi = {
  overview: () => api.get('/tri/overview'),
  lockCard: (cardId) => api.post(`/tri/cards/${cardId}/lock`),
  unlockCard: (cardId) => api.post(`/tri/cards/${cardId}/unlock`),
  processAll: (eventId) => api.post(`/tri/events/${eventId}/process-all`),
  stopEvent: (eventId) => api.post(`/tri/events/${eventId}/stop`),
}
