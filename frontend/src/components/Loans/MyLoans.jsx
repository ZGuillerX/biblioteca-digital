// Muestra los préstamos del usuario actual

import React, { useState, useEffect } from "react";
import {
  Container,
  Alert,
  Spinner,
  Card,
  Badge,
  Button,
  Row,
  Col,
  ButtonGroup,
} from "react-bootstrap";
import loanService from "../../services/loanService";

const MyLoans = () => {
  const [loans, setLoans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [filter, setFilter] = useState("all"); // all, activo, devuelto, vencido

  useEffect(() => {
    loadLoans();
  }, [filter]);

  const loadLoans = async () => {
    try {
      setLoading(true);
      setError("");
      const statusFilter = filter === "all" ? null : filter;
      const response = await loanService.getMyLoans(statusFilter);
      const data = Array.isArray(response?.data)
        ? response.data
        : Array.isArray(response)
        ? response
        : [];
      setLoans(data);
    } catch (err) {
      setError("Error al cargar préstamos");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleReturn = async (loanId) => {
    if (!window.confirm("¿Estás seguro de que quieres devolver este libro?")) {
      return;
    }

    try {
      setError("");
      setSuccess("");
      const result = await loanService.returnBook(loanId);
      setSuccess(result?.message || "Libro devuelto correctamente");

      // Recargar préstamos
      await loadLoans();

      // Limpiar mensaje después de 3 segundos
      setTimeout(() => setSuccess(""), 3000);
    } catch (err) {
      setError(err.detail || "Error al devolver libro");
      console.error(err);
    }
  };

  const getStatusBadge = (status) => {
    const variants = {
      activo: "primary",
      devuelto: "success",
      vencido: "danger",
    };

    return <Badge bg={variants[status] || "secondary"}>{status}</Badge>;
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString("es-ES", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  };

  const isOverdue = (dueDate, status) => {
    return status === "activo" && new Date(dueDate) < new Date();
  };

  const getDaysRemaining = (dueDate) => {
    const today = new Date();
    const due = new Date(dueDate);
    const diffTime = due - today;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  };

  if (loading) {
    return (
      <Container className="mt-5 text-center">
        <Spinner animation="border" />
        <p className="mt-3">Cargando préstamos...</p>
      </Container>
    );
  }

  return (
    <Container className="mt-4">
      <h2 className="mb-4">Mis Préstamos</h2>

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

      {/* Filtros */}
      <div className="mb-4">
        <ButtonGroup>
          <Button
            variant={filter === "all" ? "primary" : "outline-primary"}
            onClick={() => setFilter("all")}
          >
            Todos
          </Button>
          <Button
            variant={filter === "activo" ? "primary" : "outline-primary"}
            onClick={() => setFilter("activo")}
          >
            Activos
          </Button>
          <Button
            variant={filter === "devuelto" ? "success" : "outline-success"}
            onClick={() => setFilter("devuelto")}
          >
            Devueltos
          </Button>
          <Button
            variant={filter === "vencido" ? "danger" : "outline-danger"}
            onClick={() => setFilter("vencido")}
          >
            Vencidos
          </Button>
        </ButtonGroup>
      </div>

      {loans.length === 0 ? (
        <Alert variant="info">
          No tienes préstamos {filter !== "all" ? filter + "s" : ""}.
        </Alert>
      ) : (
        <Row xs={1} md={2} lg={3} className="g-4">
          {loans.map((loan) => (
            <Col key={loan.id}>
              <Card
                className={`h-100 ${
                  isOverdue(loan.due_date, loan.status) ? "border-danger" : ""
                }`}
              >
                <Card.Body>
                  <div className="d-flex justify-content-between align-items-start mb-2">
                    <Card.Title className="mb-0">{loan.book_title}</Card.Title>
                    {getStatusBadge(loan.status)}
                  </div>

                  <Card.Subtitle className="mb-3 text-muted">
                    {loan.book_author}
                  </Card.Subtitle>

                  <Card.Text>
                    <small>
                      <strong>Fecha préstamo:</strong>
                      <br />
                      {formatDate(loan.loan_date)}
                    </small>
                  </Card.Text>

                  <Card.Text>
                    <small>
                      <strong>Fecha vencimiento:</strong>
                      <br />
                      {formatDate(loan.due_date)}

                      {loan.status === "activo" && (
                        <>
                          <br />
                          {isOverdue(loan.due_date, loan.status) ? (
                            <Badge bg="danger" className="mt-1">
                              ¡Vencido!
                            </Badge>
                          ) : (
                            <Badge bg="info" className="mt-1">
                              {getDaysRemaining(loan.due_date)} días restantes
                            </Badge>
                          )}
                        </>
                      )}
                    </small>
                  </Card.Text>

                  {loan.return_date && (
                    <Card.Text>
                      <small>
                        <strong>Fecha devolución:</strong>
                        <br />
                        {formatDate(loan.return_date)}
                      </small>
                    </Card.Text>
                  )}

                  {loan.status === "activo" && (
                    <div className="d-grid mt-3">
                      <Button
                        variant={
                          isOverdue(loan.due_date, loan.status)
                            ? "danger"
                            : "success"
                        }
                        onClick={() => handleReturn(loan.id)}
                      >
                        Devolver Libro
                      </Button>
                    </div>
                  )}
                </Card.Body>
              </Card>
            </Col>
          ))}
        </Row>
      )}

      {/* Resumen */}
      <Card className="mt-4 bg-light">
        <Card.Body>
          <h5> Resumen</h5>
          <Row>
            <Col xs={6} md={3}>
              <strong>Total préstamos:</strong> {loans.length}
            </Col>
            <Col xs={6} md={3}>
              <strong>Activos:</strong>{" "}
              {loans.filter((l) => l.status === "activo").length}
            </Col>
            <Col xs={6} md={3}>
              <strong>Devueltos:</strong>{" "}
              {loans.filter((l) => l.status === "devuelto").length}
            </Col>
            <Col xs={6} md={3}>
              <strong>Vencidos:</strong>{" "}
              {loans.filter((l) => l.status === "vencido").length}
            </Col>
          </Row>
        </Card.Body>
      </Card>
    </Container>
  );
};

export default MyLoans;
