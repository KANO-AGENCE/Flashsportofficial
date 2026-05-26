import api from './client'

export const trainingApi = {
  // Dashboard
  dashboard: () => api.get('/training/dashboard'),

  // Ground Truth
  listGroundTruth: (params = {}) => api.get('/training/ground-truth', { params }),
  groundTruthStats: () => api.get('/training/ground-truth/stats'),
  collectGroundTruth: (eventId) => api.post(`/training/ground-truth/collect/${eventId}`),
  collectAll: () => api.post('/training/ground-truth/collect-all'),

  // Review Queue
  listReview: (params = {}) => api.get('/training/review', { params }),
  reviewCounts: () => api.get('/training/review/counts'),
  resolveReview: (id, data) => api.post(`/training/review/${id}/resolve`, data),
  flagEvent: (eventId) => api.post(`/training/review/flag-event/${eventId}`),

  // Datasets
  listDatasets: () => api.get('/training/datasets'),
  createDataset: (data) => api.post('/training/datasets', data),
  getDataset: (id) => api.get(`/training/datasets/${id}`),
  addEntries: (id, data) => api.post(`/training/datasets/${id}/add-entries`, data),
  deleteDataset: (id) => api.delete(`/training/datasets/${id}`),

  // Models
  listModels: (params = {}) => api.get('/training/models', { params }),
  createModel: (data) => api.post('/training/models', data),
  promoteModel: (id, status) => api.put(`/training/models/${id}/promote`, { status }),
  compareModels: (aId, bId) => api.get('/training/models/compare', { params: { model_a_id: aId, model_b_id: bId } }),

  // Training Sessions
  listSessions: () => api.get('/training/sessions'),
  createSession: (data) => api.post('/training/sessions', data),
  getSession: (id) => api.get(`/training/sessions/${id}`),
}
