import axios from 'axios';

const axiosInstance = axios.create({
  // Keep API calls relative so DigitalOcean path routing can send /api to backend.
  baseURL: '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

const clearStoredAuth = () => {
  localStorage.removeItem('user');
  localStorage.removeItem('access_token');
};

const isAuthFailure = (error) => {
  if (error?.response?.status !== 401) return false;
  const message = (error.response?.data?.error || '').toLowerCase();
  return (
    message.includes('token expired') ||
    message.includes('invalid token') ||
    message.includes('authorization bearer token is required')
  );
};

axiosInstance.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

axiosInstance.interceptors.response.use(
  (response) => response,
  (error) => {
    if (isAuthFailure(error)) {
      clearStoredAuth();
      window.dispatchEvent(new CustomEvent('auth:expired'));
    }
    return Promise.reject(error);
  }
);

export default axiosInstance;
