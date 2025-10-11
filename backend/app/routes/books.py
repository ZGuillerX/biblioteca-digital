"""
Rutas de Libros
===============
Endpoints para gestión del catálogo de libros.

"""

from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
import logging

from models import BookCreate, BookUpdate, BookResponse, MessageResponse
from database import execute_query
from routes.auth import get_current_user, require_admin
from mysql.connector import Error

# Configurar logging
logger = logging.getLogger(__name__)

# Crear router
router = APIRouter()


# ==================== ENDPOINTS PÚBLICOS ====================

@router.get("/", response_model=List[BookResponse])
async def get_all_books(
    skip: int = Query(0, ge=0, description="Número de registros a saltar"),
    limit: int = Query(100, ge=1, le=100, description="Límite de registros"),
    category: Optional[str] = Query(None, description="Filtrar por categoría")
):
    """
    Obtiene lista de todos los libros.
    Soporta paginación y filtrado por categoría.
    
    Args:
        skip (int): Offset para paginación
        limit (int): Límite de resultados
        category (str, optional): Categoría para filtrar
        
    Returns:
        List[BookResponse]: Lista de libros
    """
    try:
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
        
        logger.info(f"✅ Se obtuvieron {len(books)} libros")
        return books if books else []
        
    except Exception as e:
        logger.error(f"❌ Error al obtener libros: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener libros"
        )


@router.get("/{book_id}", response_model=BookResponse)
async def get_book_by_id(book_id: int):
    """
    Obtiene un libro específico por su ID.
    
    Args:
        book_id (int): ID del libro
        
    Returns:
        BookResponse: Datos del libro
        
    Raises:
        HTTPException 404: Si el libro no existe
    """
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
            logger.warning(f"⚠️ Libro no encontrado: ID {book_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Libro con ID {book_id} no encontrado"
            )
        
        logger.info(f"✅ Libro obtenido: {book[0]['title']}")
        return book[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error al obtener libro: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener libro"
        )


@router.get("/search/", response_model=List[BookResponse])
async def search_books(
    q: str = Query(..., min_length=1, description="Término de búsqueda"),
    limit: int = Query(20, ge=1, le=100, description="Límite de resultados")
):
    """
    Busca libros por título o autor.
    
    Args:
        q (str): Término de búsqueda
        limit (int): Límite de resultados
        
    Returns:
        List[BookResponse]: Lista de libros encontrados
    """
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
        
        logger.info(f"✅ Búsqueda '{q}': {len(books)} resultados")
        return books if books else []
        
    except Exception as e:
        logger.error(f"❌ Error en búsqueda: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al buscar libros"
        )


# ==================== ENDPOINTS ADMIN ====================

@router.post("/", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
async def create_book(
    book: BookCreate,
    current_user: dict = Depends(require_admin)
):
    """
    Crea un nuevo libro en el catálogo.
    Requiere permisos de administrador.
    
    Args:
        book (BookCreate): Datos del libro a crear
        current_user (dict): Usuario admin autenticado
        
    Returns:
        BookResponse: Libro creado
        
    Raises:
        HTTPException 400: Si el ISBN ya existe
    """
    try:
        # Verificar si el ISBN ya existe
        existing_book = execute_query(
            "SELECT id FROM books WHERE isbn = %s",
            (book.isbn,)
        )
        
        if existing_book:
            logger.warning(f"⚠️ Intento de crear libro con ISBN existente: {book.isbn}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe un libro con ese ISBN"
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
        
        logger.info(f"✅ Libro creado por {current_user['username']}: {book.title}")
        return new_book[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error al crear libro: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al crear libro"
        )


@router.put("/{book_id}", response_model=BookResponse)
async def update_book(
    book_id: int,
    book_update: BookUpdate,
    current_user: dict = Depends(require_admin)
):
    """
    Actualiza un libro existente.
    Requiere permisos de administrador.
    
    Args:
        book_id (int): ID del libro a actualizar
        book_update (BookUpdate): Datos a actualizar
        current_user (dict): Usuario admin autenticado
        
    Returns:
        BookResponse: Libro actualizado
        
    Raises:
        HTTPException 404: Si el libro no existe
    """
    try:
        # Verificar que el libro existe
        existing_book = execute_query(
            "SELECT id FROM books WHERE id = %s",
            (book_id,)
        )
        
        if not existing_book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Libro con ID {book_id} no encontrado"
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
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se proporcionaron campos para actualizar"
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
        
        logger.info(f"✅ Libro actualizado por {current_user['username']}: ID {book_id}")
        return updated_book[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error al actualizar libro: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al actualizar libro"
        )


@router.delete("/{book_id}", response_model=MessageResponse)
async def delete_book(
    book_id: int,
    current_user: dict = Depends(require_admin)
):
    """
    Elimina un libro del catálogo.
    Requiere permisos de administrador.
    
    Args:
        book_id (int): ID del libro a eliminar
        current_user (dict): Usuario admin autenticado
        
    Returns:
        MessageResponse: Mensaje de confirmación
        
    Raises:
        HTTPException 404: Si el libro no existe
        HTTPException 400: Si el libro tiene préstamos activos
    """
    try:
        # Verificar que el libro existe
        book = execute_query(
            "SELECT title FROM books WHERE id = %s",
            (book_id,)
        )
        
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Libro con ID {book_id} no encontrado"
            )
        
        # Verificar que no tenga préstamos activos
        active_loans = execute_query(
            "SELECT COUNT(*) as count FROM loans WHERE book_id = %s AND status = 'activo'",
            (book_id,)
        )
        
        if active_loans[0]["count"] > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se puede eliminar un libro con préstamos activos"
            )
        
        # Eliminar libro
        execute_query(
            "DELETE FROM books WHERE id = %s",
            (book_id,),
            fetch=False
        )
        
        logger.info(f"✅ Libro eliminado por {current_user['username']}: {book[0]['title']}")
        return {
            "message": "Libro eliminado exitosamente",
            "detail": f"Se eliminó el libro: {book[0]['title']}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error al eliminar libro: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al eliminar libro"
        )
