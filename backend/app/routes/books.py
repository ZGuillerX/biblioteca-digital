"""
Rutas de Libros
===============
Endpoints para gestión del catálogo de libros.
"""

from fastapi import APIRouter,status, Depends, Query
from typing import List, Optional
import logging

from models import BookCreate, BookUpdate, BookResponse, MessageResponse
from database import execute_query
from routes.auth import require_admin
from mysql.connector import Error
from utils import create_response

# Configurar logging
logger = logging.getLogger(__name__)

# Crear router
router = APIRouter()


# ==================== ENDPOINTS PÚBLICOS ====================

# Obtiene lista de todos los libros.
# Soporta paginación y filtrado por categoría.
@router.get("/", response_model=List[BookResponse])
async def get_all_books(
    skip: int = Query(0, ge=0, description="Número de registros a saltar"),
    limit: int = Query(100, ge=1, le=100, description="Límite de registros"),
    category: Optional[str] = Query(None, description="Filtrar por categoría")
):
    
    try:
        logger.info(f"🛠️ Parámetros recibidos - skip: {skip}, limit: {limit}, category: {category}")


        if category:
            query = """
                SELECT id, title, author, isbn, description, category, 
                       publication_year, total_copies, available_copies, created_at
                FROM books 
                WHERE category = %s
                ORDER BY title
                LIMIT %s OFFSET %s
            """
            params = (category, limit, skip)
        else:
            query = """
                SELECT id, title, author, isbn, description, category, 
                       publication_year, total_copies, available_copies, created_at
                FROM books 
                ORDER BY title
                LIMIT %s OFFSET %s
            """
            params = (limit, skip)
        
        books = execute_query(query, params)
        logger.info(f"Se obtuvieron {len(books) if books else 0} libros")
      

        return books if books else []
        
    except Error as e:
        logger.error(f"Error de base de datos al obtener libros: {e}")
        return create_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Error al obtener libros",
            detail="Error de base de datos"
        )
    except Exception as e:
        logger.error(f"Error al obtener libros: {e}")
        return create_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Error al obtener libros",
            detail=str(e)
        )


# Obtiene un libro específico por su ID.
@router.get("/{book_id}", response_model=BookResponse)
async def get_book_by_id(book_id: int):
    
    try:
        book = execute_query(
            """
            SELECT id, title, author, isbn, description, category, 
                   publication_year, total_copies, available_copies, created_at
            FROM books 
            WHERE id = %s
            """,
            (book_id,)
        )
        
        if not book:
            logger.warning(f"Libro no encontrado: ID {book_id}")
            return create_response(
                status_code=status.HTTP_404_NOT_FOUND,
                message=f"Libro con ID {book_id} no encontrado"
            )
        
        logger.info(f"Libro obtenido: {book[0]['title']}")
        return book[0]
        
    except Error as e:
        logger.error(f"Error de base de datos al obtener libro: {e}")
        return create_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Error al obtener libro",
            detail="Error de base de datos"
        )
    except Exception as e:
        logger.error(f"Error al obtener libro: {e}")
        return create_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Error al obtener libro",
            detail=str(e)
        )


# Busca libros por título o autor.
@router.get("/search/", response_model=List[BookResponse])
async def search_books(
    q: str = Query(..., min_length=1, description="Término de búsqueda"),
    limit: int = Query(20, ge=1, le=100, description="Límite de resultados")
):
    
    try:
        search_term = f"%{q}%"
        books = execute_query(
            """
            SELECT id, title, author, isbn, description, category, 
                   publication_year, total_copies, available_copies, created_at
            FROM books 
            WHERE title LIKE %s OR author LIKE %s
            ORDER BY title
            LIMIT %s
            """,
            (search_term, search_term, limit)
            
        )

        logger.debug(f"Libros encontrados: {books}")

        
        
        logger.info(f"Búsqueda '{q}': {len(books) if books else 0} resultados")
        
        return books if books else []
        
        
    except Error as e:
        logger.error(f"Error de base de datos en búsqueda: {e}")
        return create_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Error al buscar libros",
            detail="Error de base de datos"
        )
    except Exception as e:
        logger.error(f"Error en búsqueda: {e}")
        return create_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Error al buscar libros",
            detail=str(e)
        )


# ==================== ENDPOINTS ADMIN ====================

# Crea un nuevo libro en el catálogo.
# Requiere permisos de administrador.
@router.post("/", response_model=BookResponse)
async def create_book(
    book: BookCreate,
    current_user: dict = Depends(require_admin)
):
    
    try:
        # Verificar si el ISBN ya existe
        existing_book = execute_query(
            "SELECT id FROM books WHERE isbn = %s",
            (book.isbn,)
        )
        
        if existing_book:
            logger.warning(f"Intento de crear libro con ISBN existente: {book.isbn}")
            return create_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Ya existe un libro con ese ISBN"
            )
        
        # Insertar libro
        execute_query(
            """
            INSERT INTO books (title, author, isbn, description, category, 
                             publication_year, total_copies, available_copies)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                book.title, book.author, book.isbn, book.description,
                book.category, book.publication_year,
                book.total_copies, book.available_copies
            ),
            fetch=False
        )
        
        # Obtener libro creado
        new_book = execute_query(
            """
            SELECT id, title, author, isbn, description, category, 
                   publication_year, total_copies, available_copies, created_at
            FROM books 
            WHERE isbn = %s
            """,
            (book.isbn,)
        )
        
        logger.info(f"Libro creado por {current_user['username']}: {book.title}")
        return create_response(
            status_code=status.HTTP_201_CREATED,
            message="Libro creado exitosamente",
            data=new_book[0] if new_book else None
        )
        
    except Error as e:
        logger.error(f"Error de base de datos al crear libro: {e}")
        return create_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Error al crear libro",
            detail="Error de base de datos"
        )
    except Exception as e:
        logger.error(f"Error al crear libro: {e}")
        return create_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Error al crear libro",
            detail=str(e)
        )


# Actualiza un libro existente.
# Requiere permisos de administrador.
@router.put("/{book_id}", response_model=BookResponse)
async def update_book(
    book_id: int,
    book_update: BookUpdate,
    current_user: dict = Depends(require_admin)
):
    
    try:
        # Verificar que el libro existe
        existing_book = execute_query(
            "SELECT id FROM books WHERE id = %s",
            (book_id,)
        )
        
        if not existing_book:
            logger.warning(f"Intento de actualizar libro inexistente: ID {book_id}")
            return create_response(
                status_code=status.HTTP_404_NOT_FOUND,
                message=f"Libro con ID {book_id} no encontrado"
            )
        
        # Construir query de actualización dinámicamente
        update_fields = []
        params = []
        
        if book_update.title is not None:
            update_fields.append("title = %s")
            params.append(book_update.title)
        if book_update.author is not None:
            update_fields.append("author = %s")
            params.append(book_update.author)
        if book_update.description is not None:
            update_fields.append("description = %s")
            params.append(book_update.description)
        if book_update.category is not None:
            update_fields.append("category = %s")
            params.append(book_update.category)
        if book_update.publication_year is not None:
            update_fields.append("publication_year = %s")
            params.append(book_update.publication_year)
        if book_update.total_copies is not None:
            update_fields.append("total_copies = %s")
            params.append(book_update.total_copies)
        if book_update.available_copies is not None:
            update_fields.append("available_copies = %s")
            params.append(book_update.available_copies)
        
        if not update_fields:
            logger.warning(f"Intento de actualizar libro sin campos: ID {book_id}")
            return create_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="No se proporcionaron campos para actualizar"
            )
        
        params.append(book_id)
        query = f"UPDATE books SET {', '.join(update_fields)} WHERE id = %s"
        
        execute_query(query, tuple(params), fetch=False)
        
        # Obtener libro actualizado
        updated_book = execute_query(
            """
            SELECT id, title, author, isbn, description, category, 
                   publication_year, total_copies, available_copies, created_at
            FROM books 
            WHERE id = %s
            """,
            (book_id,)
        )
        
        logger.info(f"Libro actualizado por {current_user['username']}: ID {book_id}")
        return create_response(
            status_code=status.HTTP_200_OK,
            message="Libro actualizado exitosamente",
            data=updated_book[0] if updated_book else None
        )
        
    except Error as e:
        logger.error(f"Error de base de datos al actualizar libro: {e}")
        return create_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Error al actualizar libro",
            detail="Error de base de datos"
        )
    except Exception as e:
        logger.error(f"Error al actualizar libro: {e}")
        return create_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Error al actualizar libro",
            detail=str(e)
        )


# Elimina un libro del catálogo.
# Requiere permisos de administrador.
@router.delete("/{book_id}", response_model=MessageResponse)
async def delete_book(
    book_id: int,
    current_user: dict = Depends(require_admin)
):
    
    try:
        # Verificar que el libro existe
        book = execute_query(
            "SELECT title FROM books WHERE id = %s",
            (book_id,)
        )
        
        if not book:
            logger.warning(f"Intento de eliminar libro inexistente: ID {book_id}")
            return create_response(
                status_code=status.HTTP_404_NOT_FOUND,
                message=f"Libro con ID {book_id} no encontrado"
            )
        
        # Verificar que no tenga préstamos activos
        active_loans = execute_query(
            "SELECT COUNT(*) as count FROM loans WHERE book_id = %s AND status = 'activo'",
            (book_id,)
        )
        
        if active_loans and active_loans[0]["count"] > 0:
            logger.warning(f"Intento de eliminar libro con préstamos activos: ID {book_id}")
            return create_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="No se puede eliminar un libro con préstamos activos"
            )
        
        # Eliminar libro
        execute_query(
            "DELETE FROM books WHERE id = %s",
            (book_id,),
            fetch=False
        )
        
        logger.info(f"Libro eliminado por {current_user['username']}: {book[0]['title']}")
        return create_response(
            status_code=status.HTTP_200_OK,
            message="Libro eliminado exitosamente",
            detail=f"Se eliminó el libro: {book[0]['title']}"
        )
        
    except Error as e:
        logger.error(f"Error de base de datos al eliminar libro: {e}")
        return create_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Error al eliminar libro",
            detail="Error de base de datos"
        )
    except Exception as e:
        logger.error(f"Error al eliminar libro: {e}")
        return create_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Error al eliminar libro",
            detail=str(e)
        )