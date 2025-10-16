// Funciones para registro, login y gestión de sesión

import apiClient from "./apiClient";

const authService = {
  /**
   * Registra un nuevo usuario
   * @param {Object} userData - Datos del usuario
   * @returns {Promise} Promesa con respuesta del servidor
   */
  register: async (userData) => {
    try {
      const response = await apiClient.post("/api/auth/register", userData);
      return response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  /**
   * Inicia sesión
   * @param {string} username - Nombre de usuario
   * @param {string} password - Contraseña
   * @returns {Promise} Promesa con token y datos
   */
  login: async (username, password) => {
    try {
      const response = await apiClient.post("/api/auth/login", {
        username,
        password,
      });

      const token = response.data?.data?.access_token;
      if (!token) throw new Error("Token no recibido");

      // Guardar token
      localStorage.setItem("token", token);

      // Obtener información del usuario
      const userInfo = await authService.getCurrentUser();
      localStorage.setItem("user", JSON.stringify(userInfo));

      return { token, user: userInfo };
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  /**
   * Cierra sesión
   */
  logout: () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    window.location.href = "/login";
  },

  /**
   * Obtiene información del usuario actual
   * @returns {Promise} Promesa con datos del usuario
   */
  getCurrentUser: async () => {
    try {
      const response = await apiClient.get("/api/auth/me");
      return response.data?.data || response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  // Verifica si hay token
  isAuthenticated: () => !!localStorage.getItem("token"),

  //Devuelve el usuario almacenado en localStorage

  getStoredUser: () => {
    const user = localStorage.getItem("user");
    return user ? JSON.parse(user) : null;
  },

  /**
   * Devuelve el token almacenado
   */
  getToken: () => localStorage.getItem("token"),

  /**
   * Verifica si el usuario es admin
   */
  isAdmin: () => {
    const user = authService.getStoredUser();
    return user?.role === "admin";
  },
};

export default authService;
