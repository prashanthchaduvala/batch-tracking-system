import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      try {
        const refreshToken = localStorage.getItem('refresh_token');
        const response = await axios.post(`${API_BASE_URL}/token/refresh/`, {
          refresh: refreshToken,
        });
        localStorage.setItem('access_token', response.data.access);
        originalRequest.headers.Authorization = `Bearer ${response.data.access}`;
        return api(originalRequest);
      } catch (refreshError) {
        // Redirect to login or show error
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }
    return Promise.reject(error);
  }
);

export const batchService = {
  // Get batches with filters and pagination
  getBatches: (filters = {}, page = 1) => {
    const params = { page, ...filters };
    return api.get('/batches/', { params });
  },
  
  // Create a batch
  createBatch: (data) => {
    return api.post('/batches/', data);
  },
  
  // Get batch detail
  getBatch: (id) => {
    return api.get(`/batches/${id}/`);
  },
  
  // Update status
  updateStatus: (id, status) => {
    return api.patch(`/batches/${id}/status/`, { status });
  },
  
  // Notify partner
  notifyPartner: (id) => {
    return api.post(`/batches/${id}/notify/`);
  },
};

export default api;