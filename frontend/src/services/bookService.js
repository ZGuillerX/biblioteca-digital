// Funciones para gestionar libros

import apiClient from "./apiClient";

const bookService = {
  /**
   * Obtiene todos los libros
   */
  getAll: async (skip = 0, limit = 100, category = null) => {
    try {
      let url = `/api/books/?skip=${skip}&limit=${limit}`;
      if (category) {
        url += `&category=${category}`;
      }

      const response = await apiClient.get(url);

      if (!Array.isArray(response.data)) {
        console.warn(
          "La respuesta no contiene un array de libros:",
          response.data
        );
        return [];
      }

      return response.data;
    } catch (error) {
      console.error("Error al obtener libros:", error);
      throw error.response?.data || { detail: "Error al cargar libros" };
    }
  },

  /**
   * Obtiene un libro por ID
   */
  getById: async (id) => {
    try {
      const response = await apiClient.get(`/api/books/${id}`);
      return response.data;
    } catch (error) {
      console.error("Error al obtener libro:", error);
      throw error.response?.data || { detail: "Error al cargar libro" };
    }
  },

  /**
   * Busca libros
   */
  search: async (query) => {
    try {
      const response = await apiClient.get(
        `/api/books/search/?q=${encodeURIComponent(query)}`
      );

      if (!Array.isArray(response.data)) {
        console.warn(
          "La respuesta de búsqueda no contiene un array de libros:",
          response.data
        );
        return [];
      }

      return response.data;
    } catch (error) {
      console.error("Error en búsqueda:", error);
      throw error.response?.data || { detail: "Error en búsqueda" };
    }
  },

  /**
   * Crea un nuevo libro (admin)
   */
  create: async (bookData) => {
    try {
      const response = await apiClient.post("/api/books", bookData);
      return response.data;
    } catch (error) {
      console.error("Error al crear libro:", error);
      throw error.response?.data || { detail: "Error al crear libro" };
    }
  },

  /**
   * Actualiza un libro (admin)
   */
  update: async (id, bookData) => {
    try {
      const response = await apiClient.put(`/api/books/${id}`, bookData);
      return response.data;
    } catch (error) {
      console.error("Error al actualizar libro:", error);
      throw error.response?.data || { detail: "Error al actualizar libro" };
    }
  },

  /**
   * Elimina un libro (admin)
   */
  delete: async (id) => {
    try {
      const response = await apiClient.delete(`/api/books/${id}`);
      return response.data;
    } catch (error) {
      console.error("Error al eliminar libro:", error);
      throw error.response?.data || { detail: "Error al eliminar libro" };
    }
  },
};

export default bookService;
