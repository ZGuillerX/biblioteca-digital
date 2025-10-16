# Servicio para obtener información de libros desde Google Books API
import requests
import logging
from typing import Optional, Dict

logger = logging.getLogger(__name__)

GOOGLE_BOOKS_API = "https://www.googleapis.com/books/v1/volumes"


# Busca un libro en Google Books por ISBN
def search_book_by_isbn(isbn: str) -> Optional[Dict]:
    try:
        # Limpiar ISBN
        isbn_clean = isbn.replace("-", "").replace(" ", "")
        
        # Buscar en Google Books
        params = {
            "q": f"isbn:{isbn_clean}",
            "maxResults": 1
        }
        
        response = requests.get(GOOGLE_BOOKS_API, params=params, timeout=10)
        
        if response.status_code != 200:
            logger.warning(f"Error buscando ISBN {isbn}: {response.status_code}")
            return None
        
        data = response.json()
        
        if data.get("totalItems", 0) == 0:
            logger.info(f"No se encontró información para ISBN {isbn}")
            return None
        
        # Extraer información del primer resultado
        item = data["items"][0]
        volume_info = item.get("volumeInfo", {})
        
        book_data = {
            "title": volume_info.get("title"),
            "author": ", ".join(volume_info.get("authors", [])),
            "description": volume_info.get("description"),
            "category": ", ".join(volume_info.get("categories", [])),
            "publication_year": volume_info.get("publishedDate", "")[:4] if volume_info.get("publishedDate") else None,
            "cover_url": volume_info.get("imageLinks", {}).get("thumbnail"),
            "page_count": volume_info.get("pageCount"),
            "publisher": volume_info.get("publisher"),
            "language": volume_info.get("language")
        }
        
        logger.info(f"Información encontrada para ISBN {isbn}: {book_data.get('title')}")
        return book_data
        
    except Exception as e:
        logger.error(f"Error buscando libro con ISBN {isbn}: {e}")
        return None


# Busca libros por término de búsqueda
import requests
import logging

logger = logging.getLogger(__name__)

GOOGLE_BOOKS_API = "https://www.googleapis.com/books/v1/volumes"

#Busca libros en Google Books y devuelve una lista de diccionarios listos para el frontend
def search_books(query: str, max_results: int = 10) -> list:
    
    try:
        params = {"q": query, "maxResults": max_results}
        response = requests.get(GOOGLE_BOOKS_API, params=params, timeout=10)

        if response.status_code != 200:
            logger.warning(f"Error en búsqueda: {response.status_code}")
            return []

        data = response.json()
        items = data.get("items", [])
        books = []

        for item in items:
            volume_info = item.get("volumeInfo", {})

            # Extraer ISBN
            identifiers = volume_info.get("industryIdentifiers", [])
            isbn = None
            for identifier in identifiers:
                if identifier.get("type") in ["ISBN_13", "ISBN_10"]:
                    isbn = identifier.get("identifier")
                    break

            if not isbn:
                continue

            book_data = {
                "isbn": isbn,
                "title": volume_info.get("title"),
                "author": ", ".join(volume_info.get("authors", [])),
                "description": volume_info.get("description", "Sin descripción"),
                "category": ", ".join(volume_info.get("categories", [])),
                "publication_year": (
                    volume_info.get("publishedDate", "")[:4]
                    if volume_info.get("publishedDate")
                    else None
                ),
                "cover_url": volume_info.get("imageLinks", {}).get("thumbnail"),
            }

            books.append(book_data)

        return books

    except Exception as e:
        logger.error(f"Error en búsqueda de libros: {e}")
        return []
