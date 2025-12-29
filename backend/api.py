"""
API FastAPI para Logística HESEGO
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .database import get_db, init_db
from .config import BASE_DIR

# Importar routers
from .routes import costos, operatividad, compras, indicadores, fiscal_ru, brigadas, errores, programados, gestion

# Rutas de carpetas
FRONTEND_DIR = BASE_DIR / "frontend"
IMG_DIR = BASE_DIR / "img"
DATA_DIR = BASE_DIR / "data"

app = FastAPI(
    title="Logística HESEGO API",
    description="API para dashboards de logística",
    version="1.0.0"
)

# CORS para permitir requests desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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


@app.on_event("startup")
async def startup():
    """Inicializar BD al arrancar"""
    init_db()


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
