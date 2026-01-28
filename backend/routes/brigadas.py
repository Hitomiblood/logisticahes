"""
Rutas para el módulo de Brigadas
"""
from fastapi import APIRouter, Query
from typing import Optional
from ..database import get_db

router = APIRouter(prefix="/api/brigadas", tags=["brigadas"])

# Mapeo de meses en español a números
MESES_MAP = {
    "ENERO": 1, "FEBRERO": 2, "MARZO": 3, "ABRIL": 4,
    "MAYO": 5, "JUNIO": 6, "JULIO": 7, "AGOSTO": 8,
    "SEPTIEMBRE": 9, "OCTUBRE": 10, "NOVIEMBRE": 11, "DICIEMBRE": 12
}

def build_where_clause(anios: Optional[str] = None, meses: Optional[str] = None, sedes: Optional[str] = None):
    """Construir cláusula WHERE dinámica"""
    conditions = []
    params = []
    
    # Filtro por meses (nombres)
    if meses:
        meses_list = [m.strip() for m in meses.split(',')]
        placeholders = ','.join('?' * len(meses_list))
        conditions.append(f"TRIM(mes) IN ({placeholders})")
        params.extend(meses_list)
    
    # Filtro de sedes
    if sedes:
        sedes_list = [s.strip() for s in sedes.split(',')]
        placeholders = ','.join('?' * len(sedes_list))
        conditions.append(f"sede IN ({placeholders})")
        params.extend(sedes_list)
    
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    return where_clause, params


@router.get("/filtros")
def get_filtros():
    """Obtener valores únicos para filtros"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Sedes
        cursor.execute("SELECT DISTINCT sede FROM brigadas WHERE sede IS NOT NULL ORDER BY sede")
        sedes = [row[0] for row in cursor.fetchall()]
        
        # Estados
        cursor.execute("SELECT DISTINCT estado FROM brigadas WHERE estado IS NOT NULL ORDER BY estado")
        estados = [row[0] for row in cursor.fetchall()]
        
        return {
            "sedes": sedes,
            "estados": estados
        }


@router.get("/kpis")
def get_kpis(
    anios: Optional[str] = Query(None),
    meses: Optional[str] = Query(None),
    sedes: Optional[str] = Query(None)
):
    """Obtener KPIs de Brigadas"""
    where_clause, params = build_where_clause(anios, meses, sedes)
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Costo Total
        query = f'''
            SELECT 
                COALESCE(SUM(costo_total), 0) as costo_total,
                COALESCE(SUM(costo_diferencia), 0) as costo_diferencia,
                COALESCE(AVG(diferencia), 0) as diferencia_promedio,
                COUNT(DISTINCT item_codigo) as items_unicos,
                COUNT(*) as total_registros
            FROM brigadas
            WHERE {where_clause}
        '''
        
        cursor.execute(query, params)
        row = cursor.fetchone()
        
        return {
            "costo_total": row[0],
            "costo_diferencia": row[1],
            "diferencia_promedio": row[2],
            "items_unicos": row[3],
            "total_registros": row[4]
        }


@router.get("/grafico/por-sede")
def get_por_sede(
    anios: Optional[str] = Query(None),
    meses: Optional[str] = Query(None),
    sedes: Optional[str] = Query(None)
):
    """Obtener datos agrupados por sede para gráfico"""
    where_clause, params = build_where_clause(anios, meses, sedes)
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        query = f'''
            SELECT 
                sede,
                COALESCE(SUM(costo_total), 0) as costo_total,
                COALESCE(SUM(costo_diferencia), 0) as costo_diferencia,
                COALESCE(AVG(diferencia), 0) as diferencia
            FROM brigadas
            WHERE {where_clause}
            GROUP BY sede
            ORDER BY sede
        '''
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        return {
            "sedes": [row[0] for row in rows],
            "costo_total": [row[1] for row in rows],
            "costo_diferencia": [row[2] for row in rows],
            "desviacion": [row[3] for row in rows]  # Cambiar 'diferencia' a 'desviacion'
        }
