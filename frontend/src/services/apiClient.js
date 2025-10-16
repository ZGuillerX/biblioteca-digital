// Configuración de Axios para comunicación con el backend

import axios from 'axios';

// URL base del API
const API_URL = import.meta.env.REACT_APP_API_URL || 'http://localhost:8000';

console.log('🔗 API URL configurada:', API_URL);

// Crear instancia de axios
const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000, // 10 segundos
});


// Interceptor de requests para agregar token

apiClient.interceptors.request.use(
  (config) => {

    const token = localStorage.getItem('token');
    
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    console.log('Request:', config.method?.toUpperCase(), config.url);
    
    return config;
  },
  (error) => {
    console.error('Error en request:', error);
    return Promise.reject(error);
  }
);


// Interceptor de responses para manejar errores

apiClient.interceptors.response.use(
  (response) => {
    console.log('Response:', response.status, response.config.url);
    return response;
  },
  (error) => {
    console.error('Error en response:', error.response?.status, error.message);
    
    // Si es error 401, el token expiró
    if (error.response && error.response.status === 401) {
      console.warn('Token expirado o inválido, redirigiendo a login...');
      
      // Limpiar token y redirigir a login
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      
      // Solo redirigir si no estamos ya en login
      if (!window.location.pathname.includes('/login')) {
        window.location.href = '/login';
      }
    }
    
    return Promise.reject(error);
  }
);

export default apiClient;