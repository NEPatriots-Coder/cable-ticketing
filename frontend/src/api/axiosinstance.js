import axios from 'axios';

const axiosInstance = axios.create({
  baseURL: '/api',  // This will be proxied by nginx to backend
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export default axiosInstance;