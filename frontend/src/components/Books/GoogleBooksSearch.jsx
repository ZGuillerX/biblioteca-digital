import { useState } from "react";
import { BookOpen} from "lucide-react";
import apiClient from "../../services/apiClient";
import bookService from "../../services/bookService";

const GoogleBooksSearch = () => {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [addingBook, setAddingBook] = useState(null);

  const handleSearch = async (e) => {
    e.preventDefault();

    if (!query.trim()) {
      setError("Por favor ingresa un término de búsqueda");
      return;
    }

    try {
      setLoading(true);
      setError("");
      setResults([]);

      const response = await apiClient.get(
        `/api/books/google-books/search?q=${encodeURIComponent(query)}`
      );
      setResults(response.data.books || []);
      setLoading(false);
    } catch (err) {
      setError("Error al buscar en Google Books");
      console.error(err);
      setLoading(false);
    }
  };

  const handleAddBook = async (googleBook) => {
    try {
      setAddingBook(googleBook.isbn);
      setError("");
      setSuccess("");

      const newBook = {
        title: googleBook.title,
        author: googleBook.author || "Autor desconocido",
        isbn: googleBook.isbn,
        description: googleBook.description || "",
        category: googleBook.category || "General",
        publication_year: googleBook.publication_year || null,
        total_copies: 1,
        available_copies: 1,
        cover_url: googleBook.cover_url || null,
      };

      const createdBook = await bookService.create(newBook);

      setSuccess(`Libro "${googleBook.title}" agregado exitosamente`);
      setResults(results.filter((book) => book.isbn !== googleBook.isbn));
    } catch (err) {
      console.error("Error al agregar libro:", err);
      setError(err.detail || "Error al agregar libro");
    } finally {
      setAddingBook(null);
      setTimeout(() => setSuccess(""), 5000);
    }
  };

  return (
    <div>
      <h1>Búsqueda en Google Books</h1>

      {error && (
        <div>
          <p>Error: {error}</p>
          <button onClick={() => setError("")}>Cerrar</button>
        </div>
      )}

      {success && (
        <div>
          <p>{success}</p>
          <button onClick={() => setSuccess("")}>Cerrar</button>
        </div>
      )}

      <form onSubmit={handleSearch}>
        <input
          type="text"
          placeholder="Buscar por título, autor o ISBN..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <button type="submit" disabled={loading}>
          {loading ? "Buscando..." : "Buscar"}
        </button>
      </form>

      {loading && <p>Buscando en Google Books...</p>}

      {!loading && results.length > 0 && (
        <div>
          <h2>
            {results.length} libro{results.length !== 1 ? "s" : ""} encontrado
            {results.length !== 1 ? "s" : ""}
          </h2>

          <ul>
            {results.map((book, index) => (
              <li key={`${book.isbn}-${index}`}>
                {book.cover_url ? (
                  <img
                    src={book.cover_url}
                    alt={book.title}
                    width="100"
                    height="150"
                  />
                ) : (
                  <BookOpen />
                )}

                <h3>{book.title}</h3>
                <p>{book.author || "Autor desconocido"}</p>

                {book.isbn && <p>ISBN: {book.isbn}</p>}
                {book.category && <p>Categoría: {book.category}</p>}
                {book.publication_year && <p>Año: {book.publication_year}</p>}
                {book.description && <p>{book.description}</p>}

                <button
                  onClick={() => handleAddBook(book)}
                  disabled={addingBook === book.isbn}
                >
                  {addingBook === book.isbn
                    ? "Agregando..."
                    : "Agregar al catálogo"}
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}

      {!loading && results.length === 0 && query && (
        <div>
          <BookOpen />
          <h3>No se encontraron resultados</h3>
          <p>Intenta con otros términos de búsqueda</p>
        </div>
      )}
    </div>
  );
};

export default GoogleBooksSearch;
