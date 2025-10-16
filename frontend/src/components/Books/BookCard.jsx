// Tarjeta para mostrar información de un libro
import { Card, Button, Badge } from 'react-bootstrap';
import { useNavigate } from 'react-router-dom';

const BookCard = ({ book, onLoanRequest, showLoanButton = true }) => {
  const navigate = useNavigate();

  const handleLoanClick = () => {
    if (onLoanRequest) {
      onLoanRequest(book.id);
    }
  };

  const isAvailable = book.available_copies > 0;

  return (
    <Card className="h-100 shadow-sm">
      <Card.Body>
        <Card.Title className="text-truncate" title={book.title}>
          {book.title}
        </Card.Title>
        
        <Card.Subtitle className="mb-2 text-muted">
          {book.author}
        </Card.Subtitle>

        <Card.Text>
          <small className="text-muted">
            {book.category || 'Sin categoría'}<br/>
            {book.publication_year || 'N/A'}<br/>
            ISBN: {book.isbn}
          </small>
        </Card.Text>

        {book.description && (
          <Card.Text className="text-muted small">
            {book.description.length > 100 
              ? `${book.description.substring(0, 100)}...` 
              : book.description
            }
          </Card.Text>
        )}

        <div className="d-flex justify-content-between align-items-center mt-3">
          <div>
            <Badge bg={isAvailable ? 'success' : 'danger'}>
              {isAvailable 
                ? `${book.available_copies} disponibles` 
                : 'No disponible'
              }
            </Badge>
            <Badge bg="secondary" className="ms-2">
              Total: {book.total_copies}
            </Badge>
          </div>
        </div>

        <div className="d-grid gap-2 mt-3">
          <Button 
            variant="outline-primary" 
            size="sm"
            onClick={() => navigate(`/books/${book.id}`)}
          >
            Ver Detalles
          </Button>
          
          {showLoanButton && isAvailable && (
            <Button 
              variant="primary" 
              size="sm"
              onClick={handleLoanClick}
            >
              Solicitar Préstamo
            </Button>
          )}
        </div>
      </Card.Body>
    </Card>
  );
};

export default BookCard;
