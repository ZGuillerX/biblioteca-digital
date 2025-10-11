"""
Rutas de Autenticación
======================
Endpoints para registro, login y gestión de usuarios.
"""

from fastapi import APIRouter, HTTPException, status, Depends, Header
from typing import Optional
import logging
from datetime import timedelta

from models import UserCreate, UserLogin, UserResponse, Token, MessageResponse
from security import hash_password, verify_password, create_access_token, decode_access_token
from database import execute_query
from mysql.connector import Error

# Configurar logging
logger = logging.getLogger(__name__)

# Crear router
router = APIRouter()


# ==================== DEPENDENCIAS ====================

def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    """
    Dependencia para obtener el usuario actual desde el token JWT.
    
    Args:
        authorization (str): Header de autorización con formato "Bearer <token>"
        
    Returns:
        dict: Datos del usuario actual
        
    Raises:
        HTTPException: Si el token es inválido o no se proporciona
        
    Example:
        @app.get("/protected")
        def protected_route(current_user: dict = Depends(get_current_user)):
            return {"user": current_user["username"]}
    """
    if not authorization:
        logger.warning("⚠️ Intento de acceso sin token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autorización no proporcionado",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    try:
        # Extraer token del header "Bearer <token>"
        scheme, token = authorization.split()
        
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Esquema de autorización inválido"
            )
        
        # Decodificar token
        payload = decode_access_token(token)
        
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido o expirado"
            )
        
        username = payload.get("sub")
        role = payload.get("role")
        
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido"
            )
        
        logger.debug(f"✅ Usuario autenticado: {username}")
        return {"username": username, "role": role}
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Formato de token inválido"
        )
    except Exception as e:
        logger.error(f"❌ Error en autenticación: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Error de autenticación"
        )


def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Dependencia que verifica que el usuario actual sea admin.
    
    Args:
        current_user (dict): Usuario actual obtenido del token
        
    Returns:
        dict: Datos del usuario admin
        
    Raises:
        HTTPException: Si el usuario no es admin
    """
    if current_user.get("role") != "admin":
        logger.warning(f"⚠️ Usuario {current_user['username']} intentó acceso admin")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos de administrador"
        )
    return current_user


# ==================== ENDPOINTS ====================

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user: UserCreate):
    """
    Registra un nuevo usuario en el sistema.
    
    Args:
        user (UserCreate): Datos del usuario a crear
        
    Returns:
        UserResponse: Datos del usuario creado
        
    Raises:
        HTTPException 400: Si el username o email ya existe
        HTTPException 500: Si hay error en la base de datos
    """
    try:
        # Verificar si el username ya existe
        existing_user = execute_query(
            "SELECT id FROM users WHERE username = %s OR email = %s",
            (user.username, user.email)
        )
        
        if existing_user:
            logger.warning(f"⚠️ Intento de registro con username/email existente: {user.username}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El username o email ya está registrado"
            )
        
        # Encriptar contraseña
        hashed_password = hash_password(user.password)
        
        # Insertar usuario
        execute_query(
            """
            INSERT INTO users (username, email, password_hash, full_name, role)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (user.username, user.email, hashed_password, user.full_name, user.role),
            fetch=False
        )
        
        # Obtener usuario recién creado
        new_user = execute_query(
            "SELECT id, username, email, full_name, role, is_active, created_at FROM users WHERE username = %s",
            (user.username,)
        )
        
        logger.info(f"✅ Usuario registrado: {user.username}")
        return new_user[0]
        
    except HTTPException:
        raise
    except Error as e:
        logger.error(f"❌ Error de base de datos al registrar usuario: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al registrar usuario"
        )
    except Exception as e:
        logger.error(f"❌ Error inesperado al registrar usuario: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin):
    """
    Inicia sesión y genera un token JWT.
    
    Args:
        credentials (UserLogin): Username y contraseña
        
    Returns:
        Token: Token JWT de acceso
        
    Raises:
        HTTPException 401: Si las credenciales son incorrectas
        HTTPException 403: Si el usuario está inactivo
    """
    try:
        # Buscar usuario
        user = execute_query(
            "SELECT id, username, password_hash, role, is_active FROM users WHERE username = %s",
            (credentials.username,)
        )
        
        if not user:
            logger.warning(f"⚠️ Intento de login con username inexistente: {credentials.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales incorrectas"
            )
        
        user_data = user[0]
        
        # Verificar que el usuario esté activo
        if not user_data["is_active"]:
            logger.warning(f"⚠️ Intento de login con usuario inactivo: {credentials.username}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuario inactivo"
            )
        
        # Verificar contraseña
        if not verify_password(credentials.password, user_data["password_hash"]):
            logger.warning(f"⚠️ Contraseña incorrecta para usuario: {credentials.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales incorrectas"
            )
        
        # Crear token JWT
        access_token = create_access_token(
            data={"sub": user_data["username"], "role": user_data["role"]},
            expires_delta=timedelta(minutes=30)
        )
        
        logger.info(f"✅ Login exitoso: {credentials.username}")
        return {"access_token": access_token, "token_type": "bearer"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error en login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """
    Obtiene información del usuario actual.
    Requiere autenticación.
    
    Args:
        current_user (dict): Usuario obtenido del token (inyectado por dependencia)
        
    Returns:
        UserResponse: Datos del usuario actual
    """
    try:
        user = execute_query(
            "SELECT id, username, email, full_name, role, is_active, created_at FROM users WHERE username = %s",
            (current_user["username"],)
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        return user[0]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error al obtener usuario: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al obtener información del usuario"
        )
