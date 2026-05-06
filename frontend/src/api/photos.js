import api from './client'

export const photosApi = {
  list(eventId, params = {}) {
    return api.get(`/events/${eventId}/photos`, { params })
  },
  get(photoId) {
    return api.get(`/photos/${photoId}`)
  },
  rotate(photoId) {
    return api.post(`/photos/${photoId}/rotate`)
  },
  upload(eventId, files, cardId = null) {
    const form = new FormData()
    files.forEach(f => form.append('files', f))
    const params = cardId ? `?card_id=${cardId}` : ''
    return api.post(`/events/${eventId}/photos${params}`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  importFolder(eventId, folderPath, cardName = null) {
    const body = { folder_path: folderPath }
    if (cardName) body.card_name = cardName
    return api.post(`/events/${eventId}/import-folder`, body)
  },
  listBibs(eventId) {
    return api.get(`/events/${eventId}/bibs`)
  },
  validateDetection(detectionId, data) {
    return api.put(`/detections/${detectionId}/validate`, data)
  },
  process(eventId) {
    return api.post(`/events/${eventId}/process`)
  },
  processCard(eventId, cardId) {
    return api.post(`/events/${eventId}/process-card/${cardId}`)
  },
  processStatus(eventId, cardId = null) {
    const params = cardId ? { card_id: cardId } : {}
    return api.get(`/events/${eventId}/process/status`, { params })
  },
  stop(eventId) {
    return api.post(`/events/${eventId}/stop`)
  },
  reset(eventId) {
    return api.post(`/events/${eventId}/reset`)
  },
  createCard(eventId, name) {
    return api.post(`/events/${eventId}/cards`, { name })
  },
  deleteCard(cardId) {
    return api.delete(`/cards/${cardId}`)
  },
  publishToWeb(eventId) {
    return api.post('/web/publish', { event_id: eventId })
  },
}
