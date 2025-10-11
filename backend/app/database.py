"""
Módulo de Conexión a Base de Datos
===================================
Maneja todas las conexiones a MySQL con manejo adecuado de errores.
Incluye pool de conexiones y cierre automático.
"""

import mysql.connector
from mysql.connector import Error, pooling
from typing import Optional
import logging
from config import settings

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseConnection:
    """
    Clase para manejar conexiones a MySQL con pool de conexiones.
    """
    
    _connection_pool = None
    
    @classmethod
    def initialize_pool(cls) -> None:
        """
        Inicializa el pool de conexiones a MySQL.
        Se ejecuta una sola vez al iniciar la aplicación.
        
        Raises:
            Error: Si no se puede crear el pool de conexiones
        """
        try:
            cls._connection_pool = pooling.MySQLConnectionPool(
                pool_name="biblioteca_pool",
                pool_size=5,
                pool_reset_session=True,
                host=settings.MYSQL_HOST,
                port=settings.MYSQL_PORT,
                database=settings.MYSQL_DATABASE,
                user=settings.MYSQL_USER,
                password=settings.MYSQL_PASSWORD,
                charset='utf8mb4',
                collation='utf8mb4_unicode_ci'
            )
            logger.info("✅ Pool de conexiones MySQL inicializado correctamente")
        except Error as e:
            logger.error(f"❌ Error al inicializar pool de conexiones: {e}")
            raise
    
    @classmethod
    def get_connection(cls):
        """
        Obtiene una conexión del pool.
        
        Returns:
            MySQLConnection: Conexión activa a la base de datos
            
        Raises:
            Error: Si no se puede obtener la conexión
            
        Example:
            >>> conn = DatabaseConnection.get_connection()
            >>> cursor = conn.cursor(dictionary=True)
            >>> cursor.execute("SELECT * FROM users")
        """
        try:
            if cls._connection_pool is None:
                cls.initialize_pool()
            
            connection = cls._connection_pool.get_connection()
            logger.debug("✅ Conexión obtenida del pool")
            return connection
            
        except Error as e:
            logger.error(f"❌ Error al obtener conexión: {e}")
            raise


def get_db_connection():
    """
    Función auxiliar para obtener conexión a la base de datos.
    Utilizada en los servicios y rutas.
    
    Returns:
        MySQLConnection: Conexión activa a MySQL
        
    Example:
        >>> connection = get_db_connection()
        >>> try:
        >>>     cursor = connection.cursor(dictionary=True)
        >>>     cursor.execute("SELECT * FROM books")
        >>>     results = cursor.fetchall()
        >>> finally:
        >>>     if connection.is_connected():
        >>>         cursor.close()
        >>>         connection.close()
    """
    return DatabaseConnection.get_connection()


def execute_query(query: str, params: tuple = None, fetch: bool = True) -> Optional[list]:
    """
    Ejecuta una query en la base de datos con manejo automático de conexiones.
    
    Args:
        query (str): Query SQL a ejecutar
        params (tuple, optional): Parámetros para la query preparada
        fetch (bool): Si True, retorna resultados (SELECT). Si False, no retorna (INSERT/UPDATE/DELETE)
    
    Returns:
        list | None: Lista de resultados si fetch=True, None si fetch=False
        
    Raises:
        Error: Si hay error en la ejecución de la query
        
    Example:
        >>> # SELECT
        >>> users = execute_query("SELECT * FROM users WHERE role = %s", ("admin",))
        >>> 
        >>> # INSERT
        >>> execute_query(
        >>>     "INSERT INTO books (title, author) VALUES (%s, %s)",
        >>>     ("1984", "George Orwell"),
        >>>     fetch=False
        >>> )
    """
    connection = None
    cursor = None
    
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        
        # Ejecutar query
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        # Si es SELECT, obtener resultados
        if fetch:
            results = cursor.fetchall()
            logger.debug(f"✅ Query ejecutada: {len(results)} registros obtenidos")
            return results
        else:
            # Si es INSERT/UPDATE/DELETE, hacer commit
            connection.commit()
            logger.debug(f"✅ Query ejecutada: {cursor.rowcount} filas afectadas")
            return None
            
    except Error as e:
        logger.error(f"❌ Error ejecutando query: {e}")
        if connection:
            connection.rollback()
        raise
        
    finally:
        # Cerrar cursor y conexión
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()
            logger.debug("🔒 Conexión cerrada correctamente")


def test_connection() -> bool:
    """
    Prueba la conexión a la base de datos.
    
    Returns:
        bool: True si la conexión es exitosa, False en caso contrario
        
    Example:
        >>> if test_connection():
        >>>     print("Conexión exitosa")
    """
    connection = None
    try:
        connection = get_db_connection()
        if connection.is_connected():
            db_info = connection.get_server_info()
            logger.info(f"✅ Conexión exitosa a MySQL Server versión {db_info}")
            return True
    except Error as e:
        logger.error(f"❌ Error en conexión: {e}")
        return False
    finally:
        if connection and connection.is_connected():
            connection.close()
