//  Lista de libros con búsqueda y filtros

import { useState, useEffect } from "react";
import { Container, Row, Col, Alert, Spinner } from "react-bootstrap";
import BookCard from "./BookCard";
import BookSearch from "./BookSearch";
import bookService from "../../services/bookService";
import loanService from "../../services/loanService";
import { useAuth } from "../../context/AuthContext";

const BookList = () => {
  const [books, setBooks] = useState([]);
  const [filteredBooks, setFilteredBooks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const { isAuthenticated } = useAuth();

  useEffect(() => {
    loadBooks();
  }, []);

  const loadBooks = async () => {
    try {
      setLoading(true);
      setError("");

      const data = await bookService.getAll();

      // Ahora data ya es directamente un array de libros
      const booksArray = Array.isArray(data) ? data : [];

      setBooks(booksArray);
      setFilteredBooks(booksArray);
    } catch (err) {
      setError("Error al cargar libros");
      console.error("Error en loadBooks:", err);
      setBooks([]);
      setFilteredBooks([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (results) => {
    const resultsArray = Array.isArray(results) ? results : [];
    setFilteredBooks(resultsArray);
  };

  const handleLoanRequest = async (bookId) => {
    if (!isAuthenticated) {
      setError("Debes iniciar sesión para solicitar préstamos");
      return;
    }

    try {
      setError("");
      setSuccess("");
      await loanService.create(bookId);
      setSuccess("¡Préstamo solicitado exitosamente!");

      // Recargar libros para actualizar disponibilidad
      await loadBooks();

      // Limpiar mensaje después de 3 segundos
      setTimeout(() => setSuccess(""), 3000);
    } catch (err) {
      const errorMessage =
        err.detail || err.message || "Error al solicitar préstamo";
      setError(errorMessage);
      console.error("Error en handleLoanRequest:", err);

      // Limpiar mensaje de error después de 5 segundos
      setTimeout(() => setError(""), 5000);
    }
  };

  if (loading) {
    return (
      <Container className="mt-5 text-center">
        <Spinner animation="border" role="status">
          <span className="visually-hidden">Cargando...</span>
        </Spinner>
        <p className="mt-3">Cargando catálogo...</p>
      </Container>
    );
  }

  return (
    <Container className="mt-4">
      <h2 className="mb-4">Catálogo de Libros</h2>

      {error && (
        <Alert variant="danger" dismissible onClose={() => setError("")}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert variant="success" dismissible onClose={() => setSuccess("")}>
          {success}
        </Alert>
      )}

      <BookSearch books={books} onSearch={handleSearch} />

      {!Array.isArray(filteredBooks) || filteredBooks.length === 0 ? (
        <Alert variant="info" className="mt-4">
          {books.length === 0
            ? "No hay libros en el catálogo"
            : "No se encontraron libros con los criterios de búsqueda"}
        </Alert>
      ) : (
        <>
          <p className="text-muted mb-3">
            Mostrando {filteredBooks.length} libro(s)
          </p>

          <Row xs={1} md={2} lg={3} xl={4} className="g-4">
            {filteredBooks.map((book) => (
              <Col key={book.id}>
                <BookCard
                  book={book}
                  onLoanRequest={handleLoanRequest}
                  showLoanButton={isAuthenticated}
                />
              </Col>
            ))}
          </Row>
        </>
      )}
    </Container>
  );
};

export default BookList;
