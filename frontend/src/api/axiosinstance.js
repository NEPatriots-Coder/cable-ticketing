import axios from 'axios';

const axiosInstance = axios.create({
  // Keep API calls relative so DigitalOcean path routing can send /api to backend.
  baseURL: '/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export default axiosInstance;
