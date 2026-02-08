"""
API FastAPI para Logística HESEGO
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.exceptions import RequestValidationError

from .database import get_db, init_db
from .config import BASE_DIR, CORS_ORIGINS, IS_PRODUCTION
from .cache import get_cache_stats, invalidate_all_cache
from .logging_middleware import (
    LoggingMiddleware, 
    global_exception_handler, 
    validation_exception_handler,
    get_logger
)

# Logger
logger = get_logger("api")

# Importar routers
from .routes import costos, operatividad, compras, indicadores, fiscal_ru, brigadas, errores, programados, gestion, upload

# Rutas de carpetas
FRONTEND_DIR = BASE_DIR / "frontend"
IMG_DIR = BASE_DIR / "img"
DATA_DIR = BASE_DIR / "data"

app = FastAPI(
    title="Logística HESEGO API",
    description="API para dashboards de logística",
    version="2.0.0",
    docs_url="/api/docs" if not IS_PRODUCTION else None,  # Deshabilitar docs en producción
    redoc_url="/api/redoc" if not IS_PRODUCTION else None
)

# Middleware de logging
app.add_middleware(LoggingMiddleware)

# CORS para permitir requests desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Manejadores de excepciones globales
app.add_exception_handler(Exception, global_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

# Servir archivos estáticos (solo si existen los directorios)
if IMG_DIR.exists():
    app.mount("/img", StaticFiles(directory=str(IMG_DIR)), name="img")
if DATA_DIR.exists():
    app.mount("/data", StaticFiles(directory=str(DATA_DIR)), name="data")

# Incluir routers de API
app.include_router(costos.router)
app.include_router(operatividad.router)
app.include_router(compras.router)
app.include_router(indicadores.router)
app.include_router(fiscal_ru.router)
app.include_router(brigadas.router)
app.include_router(errores.router)
app.include_router(programados.router)
app.include_router(gestion.router)
app.include_router(upload.router)


@app.on_event("startup")
async def startup():
    """Inicializar BD al arrancar"""
    logger.info("🚀 Iniciando aplicación Logística HESEGO")
    try:
        init_db()
        logger.info("✅ Base de datos inicializada")
    except Exception as e:
        logger.error(f"❌ Error inicializando base de datos: {e}", exc_info=True)
        raise


@app.on_event("shutdown")
async def shutdown():
    """Cleanup al cerrar"""
    logger.info("👋 Cerrando aplicación Logística HESEGO")


# ============== ENDPOINTS DE ADMINISTRACIÓN ==============

@app.get("/api/admin/cache/stats")
async def cache_stats():
    """Obtener estadísticas del caché Redis"""
    return get_cache_stats()


@app.post("/api/admin/cache/clear")
async def cache_clear():
    """Limpiar todo el caché"""
    deleted = invalidate_all_cache()
    return {"message": "Caché limpiado", "keys_deleted": deleted}


# ============== ENDPOINTS PARA ARCHIVOS HTML ==============

@app.get("/")
async def root():
    return FileResponse(str(FRONTEND_DIR / "index.html"))


@app.get("/index.html")
async def index():
    return FileResponse(str(FRONTEND_DIR / "index.html"))


@app.get("/costos_mensuales.html")
async def costos_mensuales_page():
    return FileResponse(str(FRONTEND_DIR / "costos_mensuales.html"))


@app.get("/operatividad_vehiculos.html")
async def operatividad_vehiculos_page():
    return FileResponse(str(FRONTEND_DIR / "operatividad_vehiculos.html"))


@app.get("/compras.html")
async def compras_page():
    return FileResponse(str(FRONTEND_DIR / "compras.html"))


@app.get("/indicadores.html")
async def indicadores_page():
    return FileResponse(str(FRONTEND_DIR / "indicadores.html"))


@app.get("/dashboard_operativo.html")
async def dashboard_operativo_page():
    return FileResponse(str(FRONTEND_DIR / "dashboard_operativo.html"))


# ============== ENDPOINTS DE ADMINISTRACIÓN ==============

@app.get("/api/admin/stats")
async def get_admin_stats():
    """Estadísticas generales de la base de datos"""
    with get_db() as conn:
        cursor = conn.cursor()
        stats = {}
        
        # Contar registros de cada tabla
        tables = ["costos_mensuales", "operatividad_vehiculos", "traza_req_oc", "oc_descuentos", "base_oc_generadas"]
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                stats[table] = cursor.fetchone()[0]
            except:
                stats[table] = 0
        
        return stats


@app.get("/api/health")
async def health_check():
    """Verificar que la API está funcionando"""
    return {"status": "ok", "message": "API Logística HESEGO funcionando"}
