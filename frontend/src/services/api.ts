import axios from 'axios';

// В dev используем относительный путь — Vite проксирует /api на бэкенд (см. vite.config.ts)
const API_BASE_URL =
  import.meta.env.DEV ? '/api/v1' : (import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1');

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor для добавления JWT токена в заголовки
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Interceptor для обработки ошибок авторизации
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Токен недействителен — очищаем и редиректим на логин
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;
