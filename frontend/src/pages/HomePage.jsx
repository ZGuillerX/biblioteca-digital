
// Página de inicio con información general


import { Container, Row, Col, Card, Button } from 'react-bootstrap';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const HomePage = () => {
  const navigate = useNavigate();
  const { isAuthenticated, user } = useAuth();

  return (
    <Container className="mt-5">
      {/* Hero Section */}
      <div className="text-center mb-5">
        <h1 className="display-4"> Bienvenido a Biblioteca Digital</h1>
        <p className="lead text-muted">
          Tu sistema de gestión de préstamos de libros
        </p>
        
        {isAuthenticated ? (
          <div className="mt-4">
            <h4>¡Hola, {user?.username}! </h4>
            <p className="text-muted">¿Qué te gustaría hacer hoy?</p>
            <div className="d-flex justify-content-center gap-3 mt-3">
              <Button 
                variant="primary" 
                size="lg"
                onClick={() => navigate('/books')}
              >
                Ver Catálogo
              </Button>
              <Button 
                variant="outline-primary" 
                size="lg"
                onClick={() => navigate('/my-loans')}
              >
                Mis Préstamos
              </Button>
            </div>
          </div>
        ) : (
          <div className="mt-4">
            <Button 
              variant="primary" 
              size="lg" 
              className="me-3"
              onClick={() => navigate('/register')}
            >
              Registrarse
            </Button>
            <Button 
              variant="outline-primary" 
              size="lg"
              onClick={() => navigate('/login')}
            >
              Iniciar Sesión
            </Button>
          </div>
        )}
      </div>

      {/* Features */}
      <Row className="mb-5">
        <Col md={4} className="mb-4">
          <Card className="h-100 text-center shadow-sm">
            <Card.Body>
              <div className="display-4 mb-3"></div>
              <Card.Title>Amplio Catálogo</Card.Title>
              <Card.Text>
                Accede a nuestra colección de libros en diferentes categorías
              </Card.Text>
            </Card.Body>
          </Card>
        </Col>

        <Col md={4} className="mb-4">
          <Card className="h-100 text-center shadow-sm">
            <Card.Body>
              <div className="display-4 mb-3"></div>
              <Card.Title>Búsqueda Fácil</Card.Title>
              <Card.Text>
                Encuentra rápidamente el libro que buscas por título o autor
              </Card.Text>
            </Card.Body>
          </Card>
        </Col>

        <Col md={4} className="mb-4">
          <Card className="h-100 text-center shadow-sm">
            <Card.Body>
              <div className="display-4 mb-3"></div>
              <Card.Title>Gestión Simple</Card.Title>
              <Card.Text>
                Administra tus préstamos y devoluciones de manera sencilla
              </Card.Text>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Stats */}
      <Card className="bg-light">
        <Card.Body>
          <h3 className="text-center mb-4">¿Cómo funciona?</h3>
          <Row>
            <Col md={3} className="text-center mb-3">
              <div className="display-6 mb-2">1</div>
              <h5>Regístrate</h5>
              <p className="text-muted">Crea tu cuenta gratis</p>
            </Col>
            
            <Col md={3} className="text-center mb-3">
              <div className="display-6 mb-2">2</div>
              <h5>Explora</h5>
              <p className="text-muted">Busca en nuestro catálogo</p>
            </Col>
            
            <Col md={3} className="text-center mb-3">
              <div className="display-6 mb-2">3</div>
              <h5>Solicita</h5>
              <p className="text-muted">Pide el libro que quieras</p>
            </Col>
            
            <Col md={3} className="text-center mb-3">
              <div className="display-6 mb-2">4</div>
              <h5>Disfruta</h5>
              <p className="text-muted">Lee y devuelve a tiempo</p>
            </Col>
          </Row>
        </Card.Body>
      </Card>

      {/* Info adicional */}
      <div className="mt-5 mb-5 text-center">
        <h4>Información Importante</h4>
        <Row className="mt-4">
          <Col md={4}>
            <p><strong>Duración del préstamo:</strong> 14 días</p>
          </Col>
          <Col md={4}>
            <p><strong>Límite de préstamos:</strong> 3 simultáneos</p>
          </Col>
          <Col md={4}>
            <p><strong>Disponibilidad:</strong> En tiempo real</p>
          </Col>
        </Row>
      </div>
    </Container>
  );
};

export default HomePage;
