// Barra de búsqueda y filtros para libros

import React,{ useState } from 'react';
import { Form, Row, Col, Button, InputGroup } from 'react-bootstrap';
import bookService from '../../services/bookService';

const BookSearch = ({ books, onSearch }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [category, setCategory] = useState('');
  const [searching, setSearching] = useState(false);

  // Obtener categorías únicas - con validación
  const categories = React.useMemo(() => {
    if (!Array.isArray(books)) return [];
    
    const uniqueCategories = [...new Set(
      books
        .map(book => book.category)
        .filter(cat => cat && cat.trim() !== '')
    )];
    
    return uniqueCategories.sort();
  }, [books]);

  const handleSearch = async (e) => {
    e.preventDefault();
    
    if (!searchTerm.trim()) {
      // Si no hay término de búsqueda, filtrar solo por categoría
      filterByCategory();
      return;
    }

    try {
      setSearching(true);
      const results = await bookService.search(searchTerm);
      
      // Asegurar que results es un array
      const resultsArray = Array.isArray(results) ? results : [];

      
      // Si hay filtro de categoría, aplicarlo también
      if (category) {
        const filtered = resultsArray.filter(book => book.category === category);
        onSearch(filtered);
      } else {
        onSearch(resultsArray);
      }
    } catch (err) {
      console.error('Error en búsqueda:', err);
      onSearch([]);
    } finally {
      setSearching(false);
    }
  };

  const filterByCategory = () => {
    if (!Array.isArray(books)) {
      onSearch([]);
      return;
    }

    if (category) {
      const filtered = books.filter(book => book.category === category);
      onSearch(filtered);
    } else {
      onSearch(books);
    }
  };

 const handleCategoryChange = async (e) => {
  const newCategory = e.target.value;
  setCategory(newCategory);
  setSearchTerm(''); 

  try {
    setSearching(true);

    // llamada al backend con el filtro de categoría
    const results = await bookService.getAll(0, 100, newCategory);
    const booksArray = Array.isArray(results) ? results : [];


    onSearch(booksArray);
  } catch (err) {
    console.error("Error al filtrar por categoría:", err);
    onSearch([]);
  } finally {
    setSearching(false);
  }
};


  const handleClear = () => {
    setSearchTerm('');
    setCategory('');
    onSearch(Array.isArray(books) ? books : []);
  };

  return (
    <Form onSubmit={handleSearch} className="mb-4">
      <Row className="g-3">
        <Col md={6}>
          <InputGroup>
            <Form.Control
              type="text"
              placeholder="Buscar por título o autor..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
            <Button 
              variant="primary" 
              type="submit"
              disabled={searching}
            >
              {searching ? 'Buscando...' : 'Buscar'}
            </Button>
          </InputGroup>
        </Col>

        <Col md={4}>
          <Form.Select 
            value={category}
            onChange={handleCategoryChange}
          >
            <option value="">Todas las categorías</option>
            {categories.map((cat, idx) => (
              <option key={idx} value={cat}>{cat}</option>
            ))}
          </Form.Select>
        </Col>

        <Col md={2}>
          <Button 
            variant="outline-secondary" 
            onClick={handleClear}
            className="w-100"
          >
            Limpiar
          </Button>
        </Col>
      </Row>
    </Form>
  );
};

export default BookSearch;