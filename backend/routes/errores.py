"""
Rutas para el módulo de Errores Movimientos
"""
from fastapi import APIRouter, Query
from typing import Optional
from backend.database import get_db

router = APIRouter(prefix="/api/errores", tags=["errores"])

# Mapeo de meses en español a números
MESES_MAP = {
    "ENERO": 1, "FEBRERO": 2, "MARZO": 3, "ABRIL": 4,
    "MAYO": 5, "JUNIO": 6, "JULIO": 7, "AGOSTO": 8,
    "SEPTIEMBRE": 9, "OCTUBRE": 10, "NOVIEMBRE": 11, "DICIEMBRE": 12
}

def build_where_clause(fecha_inicio: Optional[str], fecha_fin: Optional[str], sedes: Optional[str], errores: Optional[str]):
    """Construir cláusula WHERE dinámica"""
    conditions = []
    params = []
    
    # Filtro de tiempo por fecha YYYY-MM
    if fecha_inicio and fecha_fin:
        try:
            # Convertir YYYY-MM a rango de meses
            year_inicio, mes_inicio = map(int, fecha_inicio.split('-'))
            year_fin, mes_fin = map(int, fecha_fin.split('-'))
            
            # Obtener meses incluidos
            meses_incluidos = []
            for mes_num in range(mes_inicio, mes_fin + 1):
                for mes_nombre, num in MESES_MAP.items():
                    if num == mes_num:
                        meses_incluidos.append(mes_nombre)
            
            if meses_incluidos:
                placeholders = ','.join('?' * len(meses_incluidos))
                conditions.append(f"mes IN ({placeholders})")
                params.extend(meses_incluidos)
        except:
            pass
    
    # Filtro de sedes
    if sedes:
        sedes_list = [s.strip() for s in sedes.split(',')]
        placeholders = ','.join('?' * len(sedes_list))
        conditions.append(f"sede IN ({placeholders})")
        params.extend(sedes_list)
    
    # Filtro de errores
    if errores:
        errores_list = [e.strip() for e in errores.split(',')]
        placeholders = ','.join('?' * len(errores_list))
        conditions.append(f"error IN ({placeholders})")
        params.extend(errores_list)
    
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    return where_clause, params


@router.get("/filtros")
def get_filtros():
    """Obtener valores únicos para filtros"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Sedes
        cursor.execute("SELECT DISTINCT sede FROM errores WHERE sede IS NOT NULL ORDER BY sede")
        sedes = [row[0] for row in cursor.fetchall()]
        
        # Tipos de error
        cursor.execute("SELECT DISTINCT error FROM errores WHERE error IS NOT NULL ORDER BY error")
        tipos_error = [row[0] for row in cursor.fetchall()]
        
        return {
            "sedes": sedes,
            "tipos_error": tipos_error
        }


@router.get("/kpis")
def get_kpis(
    fecha_inicio: Optional[str] = Query(None),
    fecha_fin: Optional[str] = Query(None),
    sedes: Optional[str] = Query(None),
    errores: Optional[str] = Query(None)
):
    """Obtener KPIs de Errores"""
    where_clause, params = build_where_clause(fecha_inicio, fecha_fin, sedes, errores)
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        query = f'''
            SELECT 
                COUNT(*) as total_registros,
                SUM(CASE WHEN error = 'Si' THEN 1 ELSE 0 END) as total_errores_si,
                SUM(CASE WHEN error = 'Revisar' THEN 1 ELSE 0 END) as total_revisar,
                SUM(CASE WHEN error = 'No' THEN 1 ELSE 0 END) as total_sin_error,
                COALESCE(SUM(total), 0) as valor_total
            FROM errores
            WHERE {where_clause}
        '''
        
        cursor.execute(query, params)
        row = cursor.fetchone()
        
        return {
            "total_registros": row[0],
            "total_errores_si": row[1],
            "total_revisar": row[2],
            "total_sin_error": row[3],
            "valor_total": row[4]
        }


@router.get("/grafico/por-error")
def get_por_error(
    fecha_inicio: Optional[str] = Query(None),
    fecha_fin: Optional[str] = Query(None),
    sedes: Optional[str] = Query(None),
    errores: Optional[str] = Query(None)
):
    """Obtener datos agrupados por tipo de error para gráfico"""
    where_clause, params = build_where_clause(fecha_inicio, fecha_fin, sedes, errores)
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        query = f'''
            SELECT 
                error,
                COUNT(*) as cantidad
            FROM errores
            WHERE {where_clause}
            GROUP BY error
            ORDER BY cantidad DESC
        '''
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        return {
            "labels": [row[0] for row in rows],
            "valores": [row[1] for row in rows]
        }


@router.get("/grafico/por-sede")
def get_por_sede(
    fecha_inicio: Optional[str] = Query(None),
    fecha_fin: Optional[str] = Query(None),
    sedes: Optional[str] = Query(None),
    errores: Optional[str] = Query(None)
):
    """Obtener datos agrupados por sede para gráfico"""
    where_clause, params = build_where_clause(fecha_inicio, fecha_fin, sedes, errores)
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        query = f'''
            SELECT 
                sede,
                SUM(CASE WHEN error = 'No' THEN 1 ELSE 0 END) as sin_error,
                SUM(CASE WHEN error = 'Revisar' THEN 1 ELSE 0 END) as revisar,
                SUM(CASE WHEN error = 'Si' THEN 1 ELSE 0 END) as con_error
            FROM errores
            WHERE {where_clause}
            GROUP BY sede
            ORDER BY sede
        '''
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        return {
            "sedes": [row[0] for row in rows],
            "sin_error": [row[1] for row in rows],
            "revisar": [row[2] for row in rows],
            "con_error": [row[3] for row in rows]
        }
