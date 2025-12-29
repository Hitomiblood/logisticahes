"""
Rutas para el módulo de Programados vs Ejecutados
"""
from fastapi import APIRouter, Query
from typing import Optional
from backend.database import get_db

router = APIRouter(prefix="/api/programados", tags=["programados"])

# Mapeo de meses en español a números
MESES_MAP = {
    "ENERO": 1, "FEBRERO": 2, "MARZO": 3, "ABRIL": 4,
    "MAYO": 5, "JUNIO": 6, "JULIO": 7, "AGOSTO": 8,
    "SEPTIEMBRE": 9, "OCTUBRE": 10, "NOVIEMBRE": 11, "DICIEMBRE": 12
}

def build_where_clause(fecha_inicio: Optional[str], fecha_fin: Optional[str], sedes: Optional[str], tipos_inventario: Optional[str]):
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
    
    # Filtro de tipos de inventario
    if tipos_inventario:
        tipos_list = [t.strip() for t in tipos_inventario.split(',')]
        placeholders = ','.join('?' * len(tipos_list))
        conditions.append(f"tipo_inventario IN ({placeholders})")
        params.extend(tipos_list)
    
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    return where_clause, params


@router.get("/filtros")
def get_filtros():
    """Obtener valores únicos para filtros"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Sedes
        cursor.execute("SELECT DISTINCT sede FROM programados_ejecutados WHERE sede IS NOT NULL ORDER BY sede")
        sedes = [row[0] for row in cursor.fetchall()]
        
        # Tipos de inventario
        cursor.execute("SELECT DISTINCT tipo_inventario FROM programados_ejecutados WHERE tipo_inventario IS NOT NULL ORDER BY tipo_inventario")
        tipos_inventario = [row[0] for row in cursor.fetchall()]
        
        return {
            "sedes": sedes,
            "tipos_inventario": tipos_inventario
        }


@router.get("/kpis")
def get_kpis(
    fecha_inicio: Optional[str] = Query(None),
    fecha_fin: Optional[str] = Query(None),
    sedes: Optional[str] = Query(None),
    tipos_inventario: Optional[str] = Query(None)
):
    """Obtener KPIs de Programados vs Ejecutados"""
    where_clause, params = build_where_clause(fecha_inicio, fecha_fin, sedes, tipos_inventario)
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        query = f'''
            SELECT 
                COUNT(*) as total_registros,
                COALESCE(SUM(programados), 0) as total_programados,
                COALESCE(SUM(ejecutados), 0) as total_ejecutados,
                COALESCE(AVG(indicador_programacion), 0) as promedio_indicador
            FROM programados_ejecutados
            WHERE {where_clause}
        '''
        
        cursor.execute(query, params)
        row = cursor.fetchone()
        
        return {
            "total_registros": row[0],
            "total_programados": row[1],
            "total_ejecutados": row[2],
            "promedio_indicador": round(row[3] * 100, 2) if row[3] else 0
        }


@router.get("/grafico/por-sede")
def get_por_sede(
    fecha_inicio: Optional[str] = Query(None),
    fecha_fin: Optional[str] = Query(None),
    sedes: Optional[str] = Query(None),
    tipos_inventario: Optional[str] = Query(None)
):
    """Obtener datos agrupados por sede para gráfico"""
    where_clause, params = build_where_clause(fecha_inicio, fecha_fin, sedes, tipos_inventario)
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        query = f'''
            SELECT 
                sede,
                COALESCE(SUM(programados), 0) as programados,
                COALESCE(SUM(ejecutados), 0) as ejecutados,
                COALESCE(AVG(indicador_programacion), 0) as indicador
            FROM programados_ejecutados
            WHERE {where_clause}
            GROUP BY sede
            ORDER BY sede
        '''
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        return {
            "sedes": [row[0] for row in rows],
            "programados": [row[1] for row in rows],
            "ejecutados": [row[2] for row in rows],
            "indicador": [round(row[3] * 100, 2) for row in rows]
        }


@router.get("/grafico/por-tipo")
def get_por_tipo(
    fecha_inicio: Optional[str] = Query(None),
    fecha_fin: Optional[str] = Query(None),
    sedes: Optional[str] = Query(None),
    tipos_inventario: Optional[str] = Query(None)
):
    """Obtener datos agrupados por tipo de inventario"""
    where_clause, params = build_where_clause(fecha_inicio, fecha_fin, sedes, tipos_inventario)
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        query = f'''
            SELECT 
                tipo_inventario,
                COALESCE(SUM(programados), 0) as programados,
                COALESCE(SUM(ejecutados), 0) as ejecutados,
                COALESCE(AVG(indicador_programacion), 0) as indicador
            FROM programados_ejecutados
            WHERE {where_clause}
            GROUP BY tipo_inventario
            ORDER BY tipo_inventario
        '''
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        return {
            "tipos": [row[0] for row in rows],
            "programados": [row[1] for row in rows],
            "ejecutados": [row[2] for row in rows],
            "indicador": [round(row[3] * 100, 2) for row in rows]
        }
