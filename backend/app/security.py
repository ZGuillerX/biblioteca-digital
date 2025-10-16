"""
Módulo de Seguridad
===================
Maneja autenticación, encriptación de contraseñas y generación de tokens JWT.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict
from jose import JWTError, jwt
from passlib.context import CryptContext
import logging
from config import settings

# Configurar logging
logger = logging.getLogger(__name__)

# Contexto de encriptación para contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Encripta una contraseña usando bcrypt
def hash_password(password: str) -> str:
  
    try:
        hashed = pwd_context.hash(password)
        logger.debug("Contraseña encriptada exitosamente")
        return hashed
    except Exception as e:
        logger.error(f" Error al encriptar contraseña: {e}")
        raise


# Verifica si una contraseña coincide con su hash. 
# plain_password (str): Contraseña en texto plano
# hashed_password (str): Hash de la contraseña almacenada
def verify_password(plain_password: str, hashed_password: str) -> bool:
    
    try:
        is_valid = pwd_context.verify(plain_password, hashed_password)
        if is_valid:
            logger.debug("Contraseña verificada correctamente")
        else:
            logger.debug("ontraseña incorrecta")
        return is_valid
    except Exception as e:
        logger.error(f"Error al verificar contraseña: {e}")
        return False



# Crea un token JWT con los datos proporcionados.
# data (dict): Datos a incluir en el token (ej: {"sub": "username", "role": "admin"})
# expires_delta (timedelta, optional): Tiempo de expiración personalizado
def create_access_token(data: Dict[str, any], expires_delta: Optional[timedelta] = None) -> str:

    try:
        to_encode = data.copy()
        
        # Calcular tiempo de expiración
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        # Agregar tiempo de expiración al payload
        to_encode.update({"exp": expire})
        
        # Generar token
        encoded_jwt = jwt.encode(
            to_encode,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        
        logger.debug(f"Token JWT creado, expira en {settings.ACCESS_TOKEN_EXPIRE_MINUTES} minutos")
        return encoded_jwt
        
    except Exception as e:
        logger.error(f"Error al crear token: {e}")
        raise

# Decodifica y valida un token JWT.
def decode_access_token(token: str) -> Optional[Dict[str, any]]:

    try:
        # Decodificar token
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        logger.debug("Token decodificado exitosamente")
        return payload
        
    except JWTError as e:
        logger.warning(f"Token inválido o expirado: {e}")
        return None
    except Exception as e:
        logger.error(f"Error al decodificar token: {e}")
        return None

# Valida si un token JWT es válido.
def validate_token(token: str) -> bool:
 
    payload = decode_access_token(token)
    return payload is not None
