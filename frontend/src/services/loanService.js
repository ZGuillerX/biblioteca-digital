// Funciones para gestionar préstamos

import apiClient from "./apiClient";

const loanService = {
  /**
   * Crea un nuevo préstamo
   * @param {number} bookId - ID del libro
   * @returns {Promise<Object>} Préstamo creado
   */
  create: async (bookId) => {
    try {
      const response = await apiClient.post("/api/loans", { book_id: bookId });
      return response.data?.data || response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  /**
   * Obtiene mis préstamos
   * @param {string||null} status - Filtro por estado
   * @returns {Promise<Array>} Lista de préstamos
   */
  getMyLoans: async (status = null) => {
    try {
      let url = "/api/loans/my-loans";
      if (status) url += `?status_filter=${encodeURIComponent(status)}`;
      const response = await apiClient.get(url);
      return response.data?.data || response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  /**
   * Devuelve un libro
   * @param {number} loanId - ID del préstamo
   * @returns {Promise<Object>} Mensaje de confirmación
   */
  returnBook: async (loanId) => {
    try {
      const response = await apiClient.put(`/api/loans/${loanId}/return`);
      return response.data?.data || response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  /**
   * Obtiene todos los préstamos (admin)
   * @param {number} skip - Offset
   * @param {number} limit - Límite
   * @param {string||null} status - Filtro por estado
   * @returns {Promise<Array>} Lista de préstamos
   */
  getAll: async (skip = 0, limit = 50, status = null) => {
    try {
      let url = `/api/loans?skip=${skip}&limit=${limit}`;
      if (status) url += `&status_filter=${encodeURIComponent(status)}`;

      const response = await apiClient.get(url);

      return response.data?.data || response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },

  /**
   * Obtiene un préstamo por ID
   * @param {number} id - ID del préstamo
   * @returns {Promise} Datos del préstamo
   */
  getById: async (id) => {
    try {
      const response = await apiClient.get(`/api/loans/${id}`);
      return response.data?.data || response.data;
    } catch (error) {
      throw error.response?.data || error.message;
    }
  },
};

export default loanService;
