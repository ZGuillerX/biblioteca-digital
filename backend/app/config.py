"""
Módulo de Configuración
=======================
Este módulo maneja todas las variables de entorno y configuraciones del sistema.
Utiliza pydantic-settings para validar las variables de entorno.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # 
    # Clase de configuración que carga variables de entorno.
    
    # Atributos:
    #     APP_NAME (str): Nombre de la aplicación
    #     APP_VERSION (str): Versión de la aplicación
    #     DEBUG (bool): Modo debug
        
    #     MYSQL_HOST (str): Host de MySQL
    #     MYSQL_PORT (int): Puerto de MySQL
    #     MYSQL_USER (str): Usuario de MySQL
    #     MYSQL_PASSWORD (str): Contraseña de MySQL
    #     MYSQL_DATABASE (str): Nombre de la base de datos
        
    #     SECRET_KEY (str): Clave secreta para JWT
    #     ALGORITHM (str): Algoritmo de encriptación
    #     ACCESS_TOKEN_EXPIRE_MINUTES (int): Tiempo de expiración del token
    # 
    
    # Configuración de la aplicación
    APP_NAME: str = "Biblioteca Digital"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Configuración de MySQL
    MYSQL_HOST: str
    MYSQL_PORT: int = 3306
    MYSQL_USER: str
    MYSQL_PASSWORD: str
    MYSQL_DATABASE: str
    
    # Configuración de seguridad
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    class Config:
        
    # Configuración de pydantic para cargar el archivo .env
        env_file = ".env"
        case_sensitive = True


@lru_cache()

# Función que retorna la configuración de la aplicación.
# Utiliza caché para evitar leer el archivo .env múltiples veces.
def get_settings() -> Settings:
    
    # Instancia de configuración con todas las variables
    return Settings() # type: ignore


# Instancia global de configuración
settings = get_settings()
