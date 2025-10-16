// Panel de administración con estadísticas y gestión
import { useState, useEffect } from "react";
import {
  Container,
  Row,
  Col,
  Card,
  Table,
  Alert,
  Spinner,
  Button,
  Tabs,
  Tab,
  Modal,
  Form,
} from "react-bootstrap";
import bookService from "../services/bookService";
import loanService from "../services/loanService";
import BulkUploadPage from "../components/Books/BulkUploadPage";
import GoogleBooksSearch from "../components/Books/GoogleBooksSearch";

const AdminPage = () => {
  const [stats, setStats] = useState({
    totalBooks: 0,
    totalLoans: 0,
    activeLoans: 0,
    overdueLoans: 0,
  });
  const [books, setBooks] = useState([]);
  const [loans, setLoans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Modal para crear libro
  const [showModal, setShowModal] = useState(false);
  const [newBook, setNewBook] = useState({
    title: "",
    author: "",
    isbn: "",
    description: "",
    category: "",
    publication_year: "",
    total_copies: 1,
    available_copies: 1,
  });

  useEffect(() => {
    loadAdminData();
  }, []);

  const loadAdminData = async () => {
    try {
      setLoading(true);
      setError("");

      const booksData = await bookService.getAll();
      const loansData = await loanService.getAll();

      const activeLoans = loansData.filter((l) => l.status === "activo").length;
      const overdueLoans = loansData.filter(
        (l) => l.status === "vencido"
      ).length;

      setStats({
        totalBooks: booksData.length,
        totalLoans: loansData.length,
        activeLoans,
        overdueLoans,
      });

      setBooks(booksData);
      setLoans(loansData.slice(0, 10));
    } catch (err) {
      setError("Error al cargar datos de administración");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateBook = async (e) => {
    e.preventDefault();
    console.log("🚀 handleCreateBook iniciado");
    console.log("📦 Datos del nuevo libro:", newBook);

    try {
      setError("");

      const createdBook = await bookService.create(newBook);

      console.log("✅ Libro creado correctamente:", createdBook);

      setShowModal(false);
      setNewBook({
        title: "",
        author: "",
        isbn: "",
        description: "",
        category: "",
        publication_year: "",
        total_copies: 1,
        available_copies: 1,
      });

      setBooks((prevBooks) => [createdBook, ...prevBooks]);

      alert("Libro creado exitosamente");
    } catch (err) {
      console.error("Error en handleCreateBook:", err);
      setError(err.detail || "Error al crear libro");
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setNewBook({
      ...newBook,
      [name]: value,
    });
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString("es-ES", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  if (loading) {
    return (
      <Container className="mt-5 text-center">
        <Spinner animation="border" />
        <p className="mt-3">Cargando panel de administración...</p>
      </Container>
    );
  }

  return (
    <Container className="mt-4">
      <h2 className="mb-4">Panel de Administración</h2>

      {error && (
        <Alert variant="danger" dismissible onClose={() => setError("")}>
          {error}
        </Alert>
      )}

      <Tabs defaultActiveKey="dashboard" id="admin-tabs" className="mb-4">
        {/* --- DASHBOARD --- */}
        <Tab eventKey="dashboard" title="Estadísticas">
          <Row className="mb-4">
            <Col md={3}>
              <Card className="text-center bg-primary text-white">
                <Card.Body>
                  <h3>{stats.totalBooks}</h3>
                  <p className="mb-0">Libros en Catálogo</p>
                </Card.Body>
              </Card>
            </Col>
            <Col md={3}>
              <Card className="text-center bg-info text-white">
                <Card.Body>
                  <h3>{stats.totalLoans}</h3>
                  <p className="mb-0">Préstamos Totales</p>
                </Card.Body>
              </Card>
            </Col>
            <Col md={3}>
              <Card className="text-center bg-success text-white">
                <Card.Body>
                  <h3>{stats.activeLoans}</h3>
                  <p className="mb-0">Préstamos Activos</p>
                </Card.Body>
              </Card>
            </Col>
            <Col md={3}>
              <Card className="text-center bg-danger text-white">
                <Card.Body>
                  <h3>{stats.overdueLoans}</h3>
                  <p className="mb-0">Préstamos Vencidos</p>
                </Card.Body>
              </Card>
            </Col>
          </Row>

          <Card>
            <Card.Header>
              <h5 className="mb-0">Préstamos Recientes</h5>
            </Card.Header>
            <Card.Body>
              {loans.length === 0 ? (
                <Alert variant="info">No hay préstamos registrados</Alert>
              ) : (
                <Table striped bordered hover responsive>
                  <thead>
                    <tr>
                      <th>ID</th>
                      <th>Usuario</th>
                      <th>Libro</th>
                      <th>Fecha Préstamo</th>
                      <th>Fecha Vencimiento</th>
                      <th>Estado</th>
                    </tr>
                  </thead>
                  <tbody>
                    {loans.map((loan) => (
                      <tr key={loan.id}>
                        <td>{loan.id}</td>
                        <td>{loan.user_username}</td>
                        <td>{loan.book_title}</td>
                        <td>{formatDate(loan.loan_date)}</td>
                        <td>{formatDate(loan.due_date)}</td>
                        <td>
                          <span
                            className={`badge bg-${
                              loan.status === "activo"
                                ? "primary"
                                : loan.status === "devuelto"
                                ? "success"
                                : "danger"
                            }`}
                          >
                            {loan.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </Table>
              )}
            </Card.Body>
          </Card>
        </Tab>

        {/* --- GESTIÓN DE LIBROS --- */}
        <Tab eventKey="books" title="Libros">
          <div className="d-flex justify-content-end mb-3">
            <Button variant="primary" onClick={() => setShowModal(true)}>
              + Agregar Libro
            </Button>
          </div>

          {books.length === 0 ? (
            <Alert variant="info">No hay libros en el catálogo</Alert>
          ) : (
            <Table striped bordered hover responsive>
              <thead>
                <tr>
                  <th>Portada</th>
                  <th>Título</th>
                  <th>Autor</th>
                  <th>ISBN</th>
                  <th>Categoría</th>
                  <th>Año</th>
                  <th>Copias</th>
                </tr>
              </thead>
              <tbody>
                {books.map((book) => (
                  <tr key={book.id}>
                    <td className="text-center">
                      {book.cover_url ? (
                        <img
                          src={book.cover_url}
                          alt={book.title}
                          style={{
                            width: "50px",
                            height: "70px",
                            objectFit: "cover",
                            borderRadius: "4px",
                          }}
                        />
                      ) : (
                        <span className="text-muted">Sin imagen</span>
                      )}
                    </td>
                    <td>{book.title}</td>
                    <td>{book.author}</td>
                    <td>{book.isbn}</td>
                    <td>{book.category || "-"}</td>
                    <td>{book.publication_year || "-"}</td>
                    <td>
                      {book.available_copies}/{book.total_copies}
                    </td>
                  </tr>
                ))}
              </tbody>
            </Table>
          )}
        </Tab>

        {/* --- CARGA MASIVA --- */}
        <Tab eventKey="bulk" title="Carga Masiva">
          <BulkUploadPage />
        </Tab>

        {/* --- GOOGLE BOOKS --- */}
        <Tab eventKey="google" title="Google Books">
          <GoogleBooksSearch />
        </Tab>
      </Tabs>

      {/* MODAL DE CREACIÓN DE LIBRO */}
      <Modal show={showModal} onHide={() => setShowModal(false)} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>Agregar Nuevo Libro</Modal.Title>
        </Modal.Header>

        <Form onSubmit={handleCreateBook}>
          <Modal.Body>
            <Row>
              <Col md={6}>
                <Form.Group className="mb-3">
                  <Form.Label>Título *</Form.Label>
                  <Form.Control
                    type="text"
                    name="title"
                    value={newBook.title}
                    onChange={handleInputChange}
                    required
                  />
                </Form.Group>
              </Col>

              <Col md={6}>
                <Form.Group className="mb-3">
                  <Form.Label>Autor *</Form.Label>
                  <Form.Control
                    type="text"
                    name="author"
                    value={newBook.author}
                    onChange={handleInputChange}
                    required
                  />
                </Form.Group>
              </Col>
            </Row>

            <Row>
              <Col md={6}>
                <Form.Group className="mb-3">
                  <Form.Label>ISBN *</Form.Label>
                  <Form.Control
                    type="text"
                    name="isbn"
                    value={newBook.isbn}
                    onChange={handleInputChange}
                    required
                  />
                </Form.Group>
              </Col>

              <Col md={6}>
                <Form.Group className="mb-3">
                  <Form.Label>Categoría</Form.Label>
                  <Form.Control
                    type="text"
                    name="category"
                    value={newBook.category}
                    onChange={handleInputChange}
                  />
                </Form.Group>
              </Col>
            </Row>

            <Form.Group className="mb-3">
              <Form.Label>Descripción</Form.Label>
              <Form.Control
                as="textarea"
                rows={3}
                name="description"
                value={newBook.description}
                onChange={handleInputChange}
              />
            </Form.Group>

            <Row>
              <Col md={4}>
                <Form.Group className="mb-3">
                  <Form.Label>Año de Publicación</Form.Label>
                  <Form.Control
                    type="number"
                    name="publication_year"
                    value={newBook.publication_year}
                    onChange={handleInputChange}
                    min="1000"
                    max="2100"
                  />
                </Form.Group>
              </Col>

              <Col md={4}>
                <Form.Group className="mb-3">
                  <Form.Label>Total Copias *</Form.Label>
                  <Form.Control
                    type="number"
                    name="total_copies"
                    value={newBook.total_copies}
                    onChange={handleInputChange}
                    min="1"
                    required
                  />
                </Form.Group>
              </Col>

              <Col md={4}>
                <Form.Group className="mb-3">
                  <Form.Label>Copias Disponibles *</Form.Label>
                  <Form.Control
                    type="number"
                    name="available_copies"
                    value={newBook.available_copies}
                    onChange={handleInputChange}
                    min="0"
                    required
                  />
                </Form.Group>
              </Col>
            </Row>
          </Modal.Body>

          <Modal.Footer>
            <Button variant="secondary" onClick={() => setShowModal(false)}>
              Cancelar
            </Button>
            <Button variant="primary" type="submit">
              Crear Libro
            </Button>
          </Modal.Footer>
        </Form>
      </Modal>
    </Container>
  );
};

export default AdminPage;
