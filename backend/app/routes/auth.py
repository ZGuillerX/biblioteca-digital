"""
Rutas de Autenticación
======================
Endpoints para registro, login y gestión de usuarios.
"""

from fastapi import APIRouter, HTTPException, status, Depends, Header
from fastapi.responses import JSONResponse
from typing import Optional
import logging
from datetime import timedelta

from models import UserCreate, UserLogin, UserResponse, Token, MessageResponse
from security import hash_password, verify_password, create_access_token, decode_access_token
from database import execute_query
from mysql.connector import Error
from utils import create_response

# Configurar logging
logger = logging.getLogger(__name__)

# Crear router
router = APIRouter()


# ==================== DEPENDENCIAS ====================
# Dependencia para obtener el usuario actual desde el token JWT.
def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    
    try:
        if not authorization:
            logger.warning("Intento de acceso sin token")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token de autorización no proporcionado",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
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
        
        logger.debug(f"Usuario autenticado: {username}")
        return {"username": username, "role": role}
        
    except ValueError:
        logger.error("Formato de token inválido")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Formato de token inválido"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en autenticación: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Error de autenticación"
        )

# Dependencia que verifica que el usuario actual sea admin.
def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    
    try:
        if current_user.get("role") != "admin":
            logger.warning(f"Usuario {current_user['username']} intentó acceso admin")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos de administrador"
            )
        return current_user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verificando permisos admin: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al verificar permisos"
        )


# ==================== ENDPOINTS ====================

# Registra un nuevo usuario en el sistema.
@router.post("/register", response_model=MessageResponse)
async def register_user(user: UserCreate):
    
    try:
        # Verificar si el username ya existe
        existing_user = execute_query(
            "SELECT id FROM users WHERE username = %s OR email = %s",
            (user.username, user.email)
        )
        
        if existing_user:
            logger.warning(f"Intento de registro con username/email existente: {user.username}")
            return create_response(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="El username o email ya está registrado"
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
        
        logger.info(f"Usuario registrado exitosamente: {user.username}")
        return create_response(
            status_code=status.HTTP_201_CREATED,
            message="Usuario creado correctamente",
            data=new_user[0] if new_user else None
        )
        
    except Error as e:
        logger.error(f"Error de base de datos al registrar usuario: {e}")
        return create_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Error al registrar usuario",
            detail="Error de base de datos"
        )
    except Exception as e:
        logger.error(f"Error inesperado al registrar usuario: {e}")
        return create_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Error interno del servidor",
            detail=str(e)
        )


# Inicia sesión y genera un token JWT
@router.post("/login", response_model=Token)
async def login(credentials: UserLogin):
    
    try:
        # Buscar usuario
        user = execute_query(
            "SELECT id, username, password_hash, role, is_active FROM users WHERE username = %s",
            (credentials.username,)
        )
        
        if not user:
            logger.warning(f"Intento de login con usuario inexistente: {credentials.username}")
            return create_response(
                status_code=status.HTTP_401_UNAUTHORIZED,
                message="Credenciales incorrectas"
            )
        
        user_data = user[0]
        
        # Verificar que el usuario esté activo
        if not user_data["is_active"]:
            logger.warning(f"Intento de login con usuario inactivo: {credentials.username}")
            return create_response(
                status_code=status.HTTP_403_FORBIDDEN,
                message="Usuario inactivo"
            )
        
        # Verificar contraseña
        if not verify_password(credentials.password, user_data["password_hash"]):
            logger.warning(f"Intento de login con contraseña incorrecta: {credentials.username}")
            return create_response(
                status_code=status.HTTP_401_UNAUTHORIZED,
                message="Credenciales incorrectas"
            )
        
        # Crear token JWT
        access_token = create_access_token(
            data={"sub": user_data["username"], "role": user_data["role"]},
            expires_delta=timedelta(minutes=30)
        )
        
        logger.info(f"Login exitoso: {credentials.username}")
        return create_response(
            status_code=status.HTTP_200_OK,
            message="Login exitoso",
            data={
                "access_token": access_token,
                "token_type": "bearer"
            }
        )
        
    except Error as e:
        logger.error(f"Error de base de datos en login: {e}")
        return create_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Error interno del servidor",
            detail="Error de base de datos"
        )
    except Exception as e:
        logger.error(f"Error en login: {e}")
        return create_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Error interno del servidor",
            detail=str(e)
        )


# Obtiene información del usuario actual autenticado.
# Requiere autenticación.
@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    
    try:
        user = execute_query(
            "SELECT id, username, email, full_name, role, is_active, created_at FROM users WHERE username = %s",
            (current_user["username"],)
        )
        
        if not user:
            logger.error(f"Usuario autenticado no encontrado en BD: {current_user['username']}")
            return create_response(
                status_code=status.HTTP_404_NOT_FOUND,
                message="Usuario no encontrado"
            )
        
        logger.info(f"Información de usuario obtenida: {current_user['username']}")
        return create_response(
            status_code=status.HTTP_200_OK,
            message="Usuario obtenido correctamente",
            data=user[0]
        )
        
    except Error as e:
        logger.error(f"Error de base de datos al obtener usuario: {e}")
        return create_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Error al obtener información del usuario",
            detail="Error de base de datos"
        )
    except Exception as e:
        logger.error(f"Error al obtener usuario: {e}")
        return create_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Error al obtener información del usuario",
            detail=str(e)
        )