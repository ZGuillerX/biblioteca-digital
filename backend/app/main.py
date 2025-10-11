"""
Aplicación Principal FastAPI
=============================
Punto de entrada de la aplicación. Configura FastAPI, middlewares y rutas.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import time
from config import settings
from database import DatabaseConnection, test_connection

# Importacion de rutas
from routes import auth, books, loans

# Configurar logging
logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# instancia de FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    description="API REST para sistema de gestión de biblioteca digital",
    version=settings.APP_VERSION,
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc"  # ReDoc
)


# ==================== MIDDLEWARES ====================

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción especificar dominios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Middleware para logging de requests.
    Registra método, ruta y tiempo de respuesta.
    
    Args:
        request (Request): Request HTTP entrante
        call_next: Función para continuar con el request
        
    Returns:
        Response: Respuesta HTTP
    """
    start_time = time.time()
    
    # Procesar request
    response = await call_next(request)
    
    # Calcular tiempo de procesamiento
    process_time = time.time() - start_time
    
    # Log del request
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.3f}s"
    )
    
    return response


# ==================== EVENTOS ====================

@app.on_event("startup")
async def startup_event():
    """
    Evento que se ejecuta al iniciar la aplicación.
    Inicializa pool de conexiones y verifica conectividad.
    """
    logger.info("=" * 50)
    logger.info(f"🚀 Iniciando {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info("=" * 50)
    
    try:
        # Inicializar pool de conexiones
        DatabaseConnection.initialize_pool()
        logger.info("✅ Pool de conexiones inicializado")
        
        # Probar conexión
        if test_connection():
            logger.info("✅ Conexión a MySQL exitosa")
        else:
            logger.error("❌ Error al conectar con MySQL")
            
    except Exception as e:
        logger.error(f"❌ Error en startup: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """
    Evento que se ejecuta al cerrar la aplicación.
    Cierra conexiones y limpia recursos.
    """
    logger.info("🛑 Cerrando aplicación...")
    logger.info("✅ Aplicación cerrada correctamente")


# ==================== RUTAS PRINCIPALES ====================

@app.get("/", tags=["Root"])
async def root():
    """
    Endpoint raíz de la API.
    
    Returns:
        dict: Información básica de la API
    """
    return {
        "message": f"Bienvenido a {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Endpoint de health check.
    Verifica que la API y la base de datos estén funcionando.
    
    Returns:
        dict: Estado de salud del sistema
    """
    db_status = test_connection()
    
    return {
        "status": "healthy" if db_status else "unhealthy",
        "database": "connected" if db_status else "disconnected",
        "version": settings.APP_VERSION
    }


# ==================== INCLUIR ROUTERS ====================

# Incluir rutas de autenticación
app.include_router(
    auth.router,
    prefix="/api/auth",
    tags=["Autenticación"]
)

# Incluir rutas de libros
app.include_router(
    books.router,
    prefix="/api/books",
    tags=["Libros"]
)

# Incluir rutas de préstamos
app.include_router(
    loans.router,
    prefix="/api/loans",
    tags=["Préstamos"]
)


# ==================== MANEJADOR DE ERRORES GLOBAL ====================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Manejador global de excepciones.
    Captura errores no manejados y retorna respuesta JSON.
    
    Args:
        request (Request): Request que generó el error
        exc (Exception): Excepción capturada
        
    Returns:
        JSONResponse: Respuesta de error en formato JSON
    """
    logger.error(f"❌ Error no manejado: {exc}")
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "Ha ocurrido un error interno en el servidor",
            "detail": str(exc) if settings.DEBUG else None
        }
    )


# ==================== PUNTO DE ENTRADA ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
