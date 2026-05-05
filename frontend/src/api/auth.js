import api from './client'

export const authApi = {
  login(email, password) {
    return api.post('/auth/login', { email, password })
  },
  me() {
    return api.get('/auth/me')
  },
}
