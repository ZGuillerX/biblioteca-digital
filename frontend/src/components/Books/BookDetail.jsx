
// Vista detallada de un libro

import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Container, Card, Button, Badge, Alert, Spinner, Row, Col } from 'react-bootstrap';
import bookService from '../../services/bookService';
import loanService from '../../services/loanService';
import { useAuth } from '../../context/AuthContext';

const BookDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  
  const [book, setBook] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    loadBook();
  }, [id]);

  const loadBook = async () => {
    try {
      setLoading(true);
      setError('');
      const data = await bookService.getById(id);
      setBook(data);
    } catch (err) {
      setError('Libro no encontrado');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleLoanRequest = async () => {
    if (!isAuthenticated) {
      setError('Debes iniciar sesión para solicitar préstamos');
      return;
    }

    try {
      setError('');
      setSuccess('');
      await loanService.create(book.id);
      setSuccess('¡Préstamo solicitado exitosamente!');
      
      // Recargar libro para actualizar disponibilidad
      await loadBook();
    } catch (err) {
      setError(err.detail || 'Error al solicitar préstamo');
      console.error(err);
    }
  };

  if (loading) {
    return (
      <Container className="mt-5 text-center">
        <Spinner animation="border" />
        <p className="mt-3">Cargando libro...</p>
      </Container>
    );
  }

  if (error && !book) {
    return (
      <Container className="mt-5">
        <Alert variant="danger">{error}</Alert>
        <Button variant="secondary" onClick={() => navigate('/books')}>
          Volver al Catálogo
        </Button>
      </Container>
    );
  }

  const isAvailable = book.available_copies > 0;

  return (
    <Container className="mt-4">
      <Button 
        variant="outline-secondary" 
        className="mb-3"
        onClick={() => navigate('/books')}
      >
        ← Volver al Catálogo
      </Button>

      {error && <Alert variant="danger" dismissible onClose={() => setError('')}>{error}</Alert>}
      {success && <Alert variant="success" dismissible onClose={() => setSuccess('')}>{success}</Alert>}

      <Card>
        <Card.Body>
          <Row>
            <Col md={8}>
              <h2>{book.title}</h2>
              <h5 className="text-muted mb-3">{book.author}</h5>

              <div className="mb-3">
                <Badge bg={isAvailable ? 'success' : 'danger'} className="me-2">
                  {isAvailable 
                    ? `${book.available_copies} disponibles` 
                    : 'No disponible'
                  }
                </Badge>
                <Badge bg="secondary">Total: {book.total_copies}</Badge>
              </div>

              <hr />

              <Row className="mb-3">
                <Col sm={6}>
                  <strong>ISBN:</strong> {book.isbn}
                </Col>
                <Col sm={6}>
                  <strong>Categoría:</strong> {book.category || 'Sin categoría'}
                </Col>
                <Col sm={6} className="mt-2">
                  <strong>Año:</strong> {book.publication_year || 'N/A'}
                </Col>
              </Row>

              {book.description && (
                <>
                  <h5>Descripción</h5>
                  <p>{book.description}</p>
                </>
              )}
            </Col>

            <Col md={4}>
              <Card bg="light">
                <Card.Body>
                  <h5 className="mb-3">Acciones</h5>
                  
                  {isAuthenticated ? (
                    isAvailable ? (
                      <Button 
                        variant="primary" 
                        className="w-100"
                        onClick={handleLoanRequest}
                      >
                        Solicitar Préstamo
                      </Button>
                    ) : (
                      <Alert variant="warning" className="mb-0">
                        Este libro no está disponible actualmente
                      </Alert>
                    )
                  ) : (
                    <Alert variant="info" className="mb-0">
                      <small>Inicia sesión para solicitar préstamos</small>
                    </Alert>
                  )}
                </Card.Body>
              </Card>
            </Col>
          </Row>
        </Card.Body>
      </Card>
    </Container>
  );
};

export default BookDetail;
