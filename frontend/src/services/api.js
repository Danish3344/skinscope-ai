import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000',
  timeout: 5000,
})

export async function getHealth() {
  const response = await api.get('/health')
  return response.data
}

export async function predictImage(file) {
  const formData = new FormData()
  formData.append('image', file)
  const response = await api.post('/predict', formData, { timeout: 30000 })
  return response.data
}

export async function findDermatologists({ latitude, longitude, query }) {
  const params = query ? { query } : { lat: latitude, lng: longitude }
  const response = await api.get('/dermatologists', { params, timeout: 15000 })
  return response.data
}

export default api
