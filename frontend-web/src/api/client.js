import axios from 'axios'

const api = axios.create({
  baseURL: '/api/web',
})

export default api
