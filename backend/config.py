import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# Rutas base
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.getenv("DATA_DIR", str(BASE_DIR / "data")))

# Configuración de entorno
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
IS_PRODUCTION = ENVIRONMENT == "production"

# ========================================
# CONFIGURACIÓN DE BASE DE DATOS
# ========================================
DB_TYPE = os.getenv("DB_TYPE", "sqlite")  # sqlite o postgresql

# PostgreSQL
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", 5432))
POSTGRES_USER = os.getenv("POSTGRES_USER", "logistica_user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "logistica_password_2026")
POSTGRES_DB = os.getenv("POSTGRES_DB", "logistica_hesego")

# SQLite (fallback para desarrollo)
DB_PATH = Path(os.getenv("SQLITE_PATH", str(BASE_DIR / "backend" / "logistica.db")))

# Construir URL de conexión
if DB_TYPE == "postgresql":
    DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
else:
    DATABASE_URL = f"sqlite:///{DB_PATH}"

# ========================================
# CONFIGURACIÓN DE REDIS/CACHÉ
# ========================================
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
CACHE_TTL = int(os.getenv("CACHE_TTL", 300))

# ========================================
# CONFIGURACIÓN DEL SERVIDOR
# ========================================
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", 8000))

# CORS
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

# ========================================
# CONFIGURACIÓN DE LOGGING
# ========================================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = os.getenv("LOG_FORMAT", "json")  # json o text

# ========================================
# CONFIGURACIÓN DE ARCHIVOS EXCEL
# ========================================
EXCEL_FILES = {
    "costos_mensuales": {
        "path": DATA_DIR / "TRANSPORTE" / "Costos mensuales - Vehiculos.xlsx",
        "sheet": "Cto Vehiculos"
    },
    "operatividad_vehiculos": {
        "path": DATA_DIR / "TRANSPORTE" / "Operatividad diaria Transporte.xlsx",
        "sheet": "08  Operatividad Vehiculos x Se"
    },
    "compras": {
        "path": DATA_DIR / "COMPRAS" / "BASE INFORME COMPRAS.xlsx",
        "sheets": {
            "traza_req_oc": "TRAZA REQ OC",
            "oc_descuentos": "OC DESCUENTOS",
            "base_oc_generadas": "BASE OC GENERADAS"
        }
    },
    "indicadores_almacenes": {
        "path": DATA_DIR / "ALMACENES" / "INDICADORES 2025.xlsx",
        "sheets": {
            "oymm": "OYMM",
            "fiscal_ru": "FISCAL-RU",
            "brigadas": "BRIGADAS ",
            "errores": "ERRORES ",
            "programados": "PRO VS EJECU",
            "gestion": "GESTION "
        }
    }
}

# Validar configuración al cargar
def validate_config():
    """Validar que la configuración sea correcta"""
    errors = []
    
    # Validar que DATA_DIR existe o advertir
    if not DATA_DIR.exists():
        errors.append(f"⚠️ Directorio de datos no encontrado: {DATA_DIR}")
    
    # Validar configuración de base de datos
    if DB_TYPE not in ["sqlite", "postgresql"]:
        errors.append(f"❌ DB_TYPE inválido: {DB_TYPE}. Debe ser 'sqlite' o 'postgresql'")
    
    if DB_TYPE == "postgresql":
        if not all([POSTGRES_HOST, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB]):
            errors.append("❌ Configuración de PostgreSQL incompleta")
    
    return errors

# Ejecutar validación
config_errors = validate_config()
if config_errors:
    print("\n".join(config_errors))
