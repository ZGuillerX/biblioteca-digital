"""
Módulo de Conexión a Base de Datos
===================================
Maneja todas las conexiones a MySQL con manejo adecuado de errores.
Incluye pool de conexiones y cierre automático.
"""


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


# Clase para manejar conexiones a MySQL con pool de conexiones.
class DatabaseConnection:
   
    _connection_pool = None
    
    @classmethod
    # Inicializa el pool de conexiones a MySQL.
    # Se ejecuta una sola vez al iniciar la aplicación.
    def initialize_pool(cls) -> None:
      
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
            logger.info("Pool de conexiones MySQL inicializado correctamente")
        except Error as e:
            logger.error(f"Error al inicializar pool de conexiones: {e}")
            raise
    
    @classmethod
    # Obtiene una conexión del pool.
    def get_connection(cls):
       
        try:
            if cls._connection_pool is None:
                cls.initialize_pool()
            
            connection = cls._connection_pool.get_connection()
            logger.debug("Conexión obtenida del pool")
            return connection
            
        except Error as e:
            logger.error(f"Error al obtener conexión: {e}")
            raise

# Función auxiliar para obtener conexión a la base de datos.
# Utilizada en los servicios y rutas
def get_db_connection():
   
    return DatabaseConnection.get_connection()

# Ejecuta una query en la base de datos con manejo automático de conexiones.
def execute_query(query: str, params: tuple = None, fetch: bool = True) -> Optional[list]: # type: ignore
   
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
            logger.debug(f"Query ejecutada: {len(results)} registros obtenidos")
            return results
        else:
            # Si es INSERT/UPDATE/DELETE, hacer commit
            connection.commit()
            logger.debug(f"Query ejecutada: {cursor.rowcount} filas afectadas")
            return None
            
    except Error as e:
        logger.error(f"Error ejecutando query: {e}")
        if connection:
            connection.rollback()
        raise
        
    finally:
        # Cerrar cursor y conexión
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()
            logger.debug("Conexión cerrada correctamente")


# Prueba la conexión a la base de datos. bool: True si la conexión es exitosa, False en caso contrario
def test_connection() -> bool: # type: ignore
    
    connection = None
    try:
        connection = get_db_connection()
        if connection.is_connected():
            db_info = connection.get_server_info()
            logger.info(f"Conexión exitosa a MySQL Server versión {db_info}")
            return True
    except Error as e:
        logger.error(f"Error en conexión: {e}")
        return False
    finally:
        if connection and connection.is_connected():
            connection.close()
