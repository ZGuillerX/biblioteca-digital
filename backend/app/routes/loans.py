"""
Rutas de Préstamos
==================
Endpoints para gestión de préstamos y devoluciones de libros.
"""

from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from datetime import datetime, timedelta
import logging

from models import LoanCreate, LoanResponse, LoanWithDetails, MessageResponse
from database import execute_query, get_db_connection
from routes.auth import get_current_user, require_admin
from mysql.connector import Error
from utils import create_response

# Configurar logging
logger = logging.getLogger(__name__)

# Crear router
router = APIRouter()

# Constantes
MAX_LOANS_PER_USER = 3  # Máximo de préstamos simultáneos
LOAN_DURATION_DAYS = 14  # Duración del préstamo en días


# ==================== FUNCIONES AUXILIARES ====================

# Obtiene el ID de un usuario por su username.
def get_user_id_by_username(username: str) -> Optional[int]:
    
    try:
        result = execute_query(
            "SELECT id FROM users WHERE username = %s",
            (username,)
        )
        return result[0]["id"] if result else None
    except Exception as e:
        logger.error(f"Error al obtener ID de usuario: {e}")
        return None

# Verifica si un libro tiene copias disponibles.
def check_book_availability(book_id: int) -> bool:
    
    try:
        result = execute_query(
            "SELECT available_copies FROM books WHERE id = %s",
            (book_id,)
        )
        
        if not result:
            return False
        
        return result[0]["available_copies"] > 0
        
    except Exception as e:
        logger.error(f"Error al verificar disponibilidad: {e}")
        return False

# Cuenta los préstamos activos de un usuario
def count_active_loans(user_id: int) -> int:
    
    try:
        result = execute_query(
            "SELECT COUNT(*) as count FROM loans WHERE user_id = %s AND status = 'activo'",
            (user_id,)
        )
        return result[0]["count"] if result else 0
        
    except Exception as e:
        logger.error(f"Error al contar préstamos activos: {e}")
        return 0

# Actualiza la disponibilidad de un libro.
def update_book_availability(book_id: int, increment: bool = False) -> bool:

    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        
        if increment:
            # Incrementar copias disponibles (devolución)
            query = """
                UPDATE books 
                SET available_copies = available_copies + 1 
                WHERE id = %s AND available_copies < total_copies
            """
        else:
            # Decrementar copias disponibles (préstamo)
            query = """
                UPDATE books 
                SET available_copies = available_copies - 1 
                WHERE id = %s AND available_copies > 0
            """
        
        cursor.execute(query, (book_id,))
        connection.commit()
        
        success = cursor.rowcount > 0
        
        if success:
            logger.debug(f"Disponibilidad actualizada para libro ID {book_id}")
        else:
            logger.warning(f"No se pudo actualizar disponibilidad para libro ID {book_id}")
        
        return success
        
    except Error as e:
        logger.error(f"Error al actualizar disponibilidad: {e}")
        if connection:
            connection.rollback()
        return False
        
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()

# Actualiza el estado de préstamos vencidos.
def update_overdue_loans() -> int:
    
    try:
        result = execute_query(
            """
            UPDATE loans 
            SET status = 'vencido' 
            WHERE status = 'activo' 
            AND due_date < NOW() 
            AND return_date IS NULL
            """,
            fetch=False
        )
        
        logger.info("Estados de préstamos vencidos actualizados")
        # Número de préstamos actualizados
        return 0  # rowcount no está disponible en execute_query
        
    except Exception as e:
        logger.error(f"Error al actualizar préstamos vencidos: {e}")
        return 0


# ==================== ENDPOINTS DE USUARIOS ====================

# Crea un nuevo préstamo de libro.
# Requiere autenticación.
@router.post("/", response_model=LoanResponse, status_code=status.HTTP_201_CREATED)
async def create_loan(
    loan: LoanCreate,
    current_user: dict = Depends(get_current_user)
):

    connection = None
    cursor = None
    
    try:
        # Obtener ID del usuario
        user_id = get_user_id_by_username(current_user["username"])
        
        if not user_id:
            logger.error(f"No se pudo obtener ID para usuario: {current_user['username']}")
            return create_response(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Usuario no encontrado"
            )
        
        # Verificar que el libro existe
        book = execute_query(
            "SELECT id, title, available_copies FROM books WHERE id = %s",
            (loan.book_id,)
        )
        
        if not book:
            logger.warning(f"Intento de préstamo de libro inexistente: ID {loan.book_id}")
            return create_response(
                status_code=status.HTTP_404_NOT_FOUND,
                message=f"Libro con ID {loan.book_id} no encontrado"
            )
        
        # Verificar disponibilidad
        if not check_book_availability(loan.book_id):
            logger.warning(f"Intento de préstamo sin disponibilidad: {book[0]['title']}")
            return create_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="No hay copias disponibles de este libro"
            )
        
        # Verificar límite de préstamos activos
        active_loans = count_active_loans(user_id)
        
        if active_loans >= MAX_LOANS_PER_USER:
            logger.warning(f"Usuario {current_user['username']} alcanzó límite de préstamos")
            return create_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                message=f"Has alcanzado el límite de {MAX_LOANS_PER_USER} préstamos simultáneos"
            )
        
        # Verificar que no tenga el mismo libro prestado
        existing_loan = execute_query(
            """
            SELECT id FROM loans 
            WHERE user_id = %s AND book_id = %s AND status = 'activo'
            """,
            (user_id, loan.book_id)
        )
        
        if existing_loan:
            logger.warning(f"Usuario {current_user['username']} ya tiene libro {loan.book_id} prestado")
            return create_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Ya tienes este libro en préstamo"
            )
        
        # Calcular fecha de vencimiento
        due_date = datetime.now() + timedelta(days=LOAN_DURATION_DAYS)
        
        # Iniciar transacción
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        # Crear préstamo
        cursor.execute(
            """
            INSERT INTO loans (user_id, book_id, due_date)
            VALUES (%s, %s, %s)
            """,
            (user_id, loan.book_id, due_date)
        )
        
        loan_id = cursor.lastrowid
        
        # Actualizar disponibilidad del libro
        cursor.execute(
            """
            UPDATE books 
            SET available_copies = available_copies - 1 
            WHERE id = %s AND available_copies > 0
            """,
            (loan.book_id,)
        )
        
        if cursor.rowcount == 0:
            connection.rollback()
            logger.error(f"Error al actualizar disponibilidad del libro {loan.book_id}")
            return create_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Error al actualizar disponibilidad del libro"
            )
        
        # Confirmar transacción
        connection.commit()
        
        # Obtener préstamo creado
        cursor.execute(
            """
            SELECT id, user_id, book_id, loan_date, due_date, 
                   return_date, status, created_at
            FROM loans 
            WHERE id = %s
            """,
            (loan_id,)
        )
        
        new_loan = cursor.fetchone()
        
        logger.info(f"Préstamo creado: Usuario {current_user['username']}, Libro ID {loan.book_id}")
        return create_response(
            status_code=status.HTTP_201_CREATED,
            message="Préstamo creado exitosamente",
            data=new_loan
        )
        
    except Error as e:
        logger.error(f"Error de base de datos al crear préstamo: {e}")
        if connection:
            connection.rollback()
        return create_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Error al crear préstamo",
            detail="Error de base de datos"
        )
    except Exception as e:
        logger.error(f"Error al crear préstamo: {e}")
        if connection:
            connection.rollback()
        return create_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Error al crear préstamo",
            detail=str(e)
        )
        
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


# Obtiene los préstamos del usuario actual.
# Requiere autenticación.
@router.get("/my-loans", response_model=List[LoanWithDetails])
async def get_my_loans(
    status_filter: Optional[str] = Query(None, description="Filtrar por estado: activo, devuelto, vencido"),
    current_user: dict = Depends(get_current_user)
):
    
    try:
        # Actualizar préstamos vencidos
        update_overdue_loans()
        
        # Obtener ID del usuario
        user_id = get_user_id_by_username(current_user["username"])
        
        if not user_id:
            logger.error(f"No se pudo obtener ID para usuario: {current_user['username']}")
            return create_response(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Usuario no encontrado"
            )
        
        # Construir query
        if status_filter:
            query = """
                SELECT 
                    l.id, l.user_id, l.book_id, l.loan_date, l.due_date, 
                    l.return_date, l.status, l.created_at,
                    b.title as book_title, b.author as book_author,
                    u.username as user_username
                FROM loans l
                INNER JOIN books b ON l.book_id = b.id
                INNER JOIN users u ON l.user_id = u.id
                WHERE l.user_id = %s AND l.status = %s
                ORDER BY l.loan_date DESC
            """
            params = (user_id, status_filter)
        else:
            query = """
                SELECT 
                    l.id, l.user_id, l.book_id, l.loan_date, l.due_date, 
                    l.return_date, l.status, l.created_at,
                    b.title as book_title, b.author as book_author,
                    u.username as user_username
                FROM loans l
                INNER JOIN books b ON l.book_id = b.id
                INNER JOIN users u ON l.user_id = u.id
                WHERE l.user_id = %s
                ORDER BY l.loan_date DESC
            """
            params = (user_id,)
        
        loans = execute_query(query, params)
        
        logger.info(f"Préstamos obtenidos para usuario {current_user['username']}: {len(loans) if loans else 0}")
        return create_response(
            status_code=status.HTTP_200_OK,
            message="Préstamos obtenidos correctamente",
            data=loans if loans else []
        )
        
    except Error as e:
        logger.error(f"Error de base de datos al obtener préstamos: {e}")
        return create_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Error al obtener préstamos",
            detail="Error de base de datos"
        )
    except Exception as e:
        logger.error(f"Error al obtener préstamos: {e}")
        return create_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Error al obtener préstamos",
            detail=str(e)
        )

# Devuelve un libro prestado.
# Requiere autenticación.
@router.put("/{loan_id}/return", response_model=MessageResponse)
async def return_book(
    loan_id: int,
    current_user: dict = Depends(get_current_user)
):

    connection = None
    cursor = None
    
    try:
        # Obtener ID del usuario
        user_id = get_user_id_by_username(current_user["username"])
        
        if not user_id:
            logger.error(f"No se pudo obtener ID para usuario: {current_user['username']}")
            return create_response(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Usuario no encontrado"
            )
        
        # Obtener préstamo
        loan = execute_query(
            """
            SELECT l.id, l.user_id, l.book_id, l.status, b.title
            FROM loans l
            INNER JOIN books b ON l.book_id = b.id
            WHERE l.id = %s
            """,
            (loan_id,)
        )
        
        if not loan:
            logger.warning(f"Intento de devolver préstamo inexistente: ID {loan_id}")
            return create_response(
                status_code=status.HTTP_404_NOT_FOUND,
                message=f"Préstamo con ID {loan_id} no encontrado"
            )
        
        loan_data = loan[0]
        
        # Verificar que el préstamo pertenezca al usuario (usuarios normales)
        # Los admin pueden devolver cualquier préstamo
        if current_user["role"] != "admin" and loan_data["user_id"] != user_id:
            logger.warning(f"Usuario {current_user['username']} intentó devolver préstamo ajeno")
            return create_response(
                status_code=status.HTTP_403_FORBIDDEN,
                message="No tienes permiso para devolver este préstamo"
            )
        
        # Verificar que el préstamo esté activo o vencido
        if loan_data["status"] == "devuelto":
            logger.warning(f"Intento de devolver libro ya devuelto: ID {loan_id}")
            return create_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="Este libro ya fue devuelto"
            )
        
        # Iniciar transacción
        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Actualizar préstamo
        cursor.execute(
            """
            UPDATE loans 
            SET return_date = NOW(), status = 'devuelto'
            WHERE id = %s
            """,
            (loan_id,)
        )
        
        # Incrementar disponibilidad del libro
        cursor.execute(
            """
            UPDATE books 
            SET available_copies = available_copies + 1 
            WHERE id = %s AND available_copies < total_copies
            """,
            (loan_data["book_id"],)
        )
        
        if cursor.rowcount == 0:
            connection.rollback()
            logger.error(f"Error al actualizar disponibilidad del libro {loan_data['book_id']}")
            return create_response(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="Error al actualizar disponibilidad del libro"
            )
        
        # Confirmar transacción
        connection.commit()
        
        logger.info(f"Libro devuelto: {loan_data['title']} por {current_user['username']}")
        return create_response(
            status_code=status.HTTP_200_OK,
            message="Libro devuelto exitosamente",
            detail=f"Has devuelto el libro: {loan_data['title']}"
        )
        
    except Error as e:
        logger.error(f"Error de base de datos al devolver libro: {e}")
        if connection:
            connection.rollback()
        return create_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Error al devolver libro",
            detail="Error de base de datos"
        )
    except Exception as e:
        logger.error(f"Error al devolver libro: {e}")
        if connection:
            connection.rollback()
        return create_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Error al devolver libro",
            detail=str(e)
        )
        
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()


# ==================== ENDPOINTS ADMIN ====================

# Obtiene todos los préstamos del sistema.
# Requiere permisos de administrador.
@router.get("/", response_model=List[LoanWithDetails])
async def get_all_loans(
    skip: int = Query(0, ge=0, description="Número de registros a saltar"),
    limit: int = Query(50, ge=1, le=100, description="Límite de registros"),
    status_filter: Optional[str] = Query(None, description="Filtrar por estado"),
    current_user: dict = Depends(require_admin)
):
    
    try:
        # Actualizar préstamos vencidos
        update_overdue_loans()
        
        if status_filter:
            query = """
                SELECT 
                    l.id, l.user_id, l.book_id, l.loan_date, l.due_date, 
                    l.return_date, l.status, l.created_at,
                    b.title as book_title, b.author as book_author,
                    u.username as user_username
                FROM loans l
                INNER JOIN books b ON l.book_id = b.id
                INNER JOIN users u ON l.user_id = u.id
                WHERE l.status = %s
                ORDER BY l.loan_date DESC
                LIMIT %s OFFSET %s
            """
            params = (status_filter, limit, skip)
        else:
            query = """
                SELECT 
                    l.id, l.user_id, l.book_id, l.loan_date, l.due_date, 
                    l.return_date, l.status, l.created_at,
                    b.title as book_title, b.author as book_author,
                    u.username as user_username
                FROM loans l
                INNER JOIN books b ON l.book_id = b.id
                INNER JOIN users u ON l.user_id = u.id
                ORDER BY l.loan_date DESC
                LIMIT %s OFFSET %s
            """
            params = (limit, skip)
        
        loans = execute_query(query, params)
        
        logger.info(f"Admin {current_user['username']} obtuvo {len(loans) if loans else 0} préstamos")
        return create_response(
            status_code=status.HTTP_200_OK,
            message="Préstamos obtenidos correctamente",
            data=loans if loans else []
        )
        
    except Error as e:
        logger.error(f"Error de base de datos al obtener préstamos: {e}")
        return create_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Error al obtener préstamos",
            detail="Error de base de datos"
        )
    except Exception as e:
        logger.error(f"Error al obtener préstamos: {e}")
        return create_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Error al obtener préstamos",
            detail=str(e)
        )


# Obtiene un préstamo específico por ID.
# Usuarios pueden ver solo sus préstamos, admin puede ver todos.
@router.get("/{loan_id}", response_model=LoanWithDetails)
async def get_loan_by_id(
    loan_id: int,
    current_user: dict = Depends(get_current_user)
):
    
    try:
        loan = execute_query(
            """
            SELECT 
                l.id, l.user_id, l.book_id, l.loan_date, l.due_date, 
                l.return_date, l.status, l.created_at,
                b.title as book_title, b.author as book_author,
                u.username as user_username
            FROM loans l
            INNER JOIN books b ON l.book_id = b.id
            INNER JOIN users u ON l.user_id = u.id
            WHERE l.id = %s
            """,
            (loan_id,)
        )
        
        if not loan:
            logger.warning(f"Préstamo no encontrado: ID {loan_id}")
            return create_response(
                status_code=status.HTTP_404_NOT_FOUND,
                message=f"Préstamo con ID {loan_id} no encontrado"
            )
        
        loan_data = loan[0]
        
        # Verificar permisos (usuarios solo ven sus préstamos)
        if current_user["role"] != "admin" and loan_data["user_username"] != current_user["username"]:
            logger.warning(f"Usuario {current_user['username']} intentó ver préstamo ajeno: ID {loan_id}")
            return create_response(
                status_code=status.HTTP_403_FORBIDDEN,
                message="No tienes permiso para ver este préstamo"
            )
        
        logger.info(f"Préstamo obtenido: ID {loan_id} por {current_user['username']}")
        return create_response(
            status_code=status.HTTP_200_OK,
            message="Préstamo obtenido correctamente",
            data=loan_data
        )
        
    except Error as e:
        logger.error(f"Error de base de datos al obtener préstamo: {e}")
        return create_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Error al obtener préstamo",
            detail="Error de base de datos"
        )
    except Exception as e:
        logger.error(f"Error al obtener préstamo: {e}")
        return create_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Error al obtener préstamo",
            detail=str(e)
        )