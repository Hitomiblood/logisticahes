import os
from pathlib import Path

# Rutas base
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = BASE_DIR / "backend" / "logistica.db"

# Configuración de archivos Excel
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
    "indicadores": {
        "path": DATA_DIR / "ALMACENES" / "INDICADORES 2025.xlsx",
        "sheet": "OYMM"
    },
    "fiscal_ru": {
        "path": DATA_DIR / "ALMACENES" / "INDICADORES 2025.xlsx",
        "sheet": "FISCAL-RU"
    },
    "brigadas": {
        "path": DATA_DIR / "ALMACENES" / "INDICADORES 2025.xlsx",
        "sheet": "BRIGADAS "
    },
    "errores": {
        "path": DATA_DIR / "ALMACENES" / "INDICADORES 2025.xlsx",
        "sheet": "ERRORES "
    },
    "programados_ejecutados": {
        "path": DATA_DIR / "ALMACENES" / "INDICADORES 2025.xlsx",
        "sheet": "PRO VS EJECU"
    },
    "gestion": {
        "path": DATA_DIR / "ALMACENES" / "INDICADORES 2025.xlsx",
        "sheet": "GESTION "
    }
}

# Configuración del servidor
API_HOST = "0.0.0.0"
API_PORT = 8000
