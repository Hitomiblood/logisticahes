"""
Rutas API para Operatividad de Vehículos
"""
from fastapi import APIRouter, Query
from typing import Optional
from ..database import get_db
from ..cache import cache_get, cache_set, generate_cache_key, invalidate_operatividad_cache

router = APIRouter(prefix="/api/operatividad", tags=["Operatividad Vehículos"])

# TTL de caché en segundos (5 minutos)
CACHE_TTL = 300


def build_where_clause(fecha_inicio, fecha_fin, sedes, estados, placas):
    """Construir cláusula WHERE y parámetros"""
    where_clause = "WHERE 1=1"
    params = []
    
    if fecha_inicio:
        where_clause += " AND fecha_ejecucion >= ?"
        params.append(fecha_inicio)
    if fecha_fin:
        where_clause += " AND fecha_ejecucion <= ?"
        params.append(fecha_fin)
    if sedes:
        sede_list = sedes.split(",")
        placeholders = ",".join(["?" for _ in sede_list])
        where_clause += f" AND sede IN ({placeholders})"
        params.extend(sede_list)
    if estados:
        estado_list = estados.split(",")
        placeholders = ",".join(["?" for _ in estado_list])
        where_clause += f" AND estado_vehiculo IN ({placeholders})"
        params.extend(estado_list)
    if placas:
        placa_list = placas.split(",")
        placeholders = ",".join(["?" for _ in placa_list])
        where_clause += f" AND placa IN ({placeholders})"
        params.extend(placa_list)
    
    return where_clause, params


@router.get("/datos")
async def get_datos(
    fecha_inicio: Optional[str] = None,
    fecha_fin: Optional[str] = None,
    sedes: Optional[str] = None,
    estados: Optional[str] = None,
    placas: Optional[str] = None,
    limit: int = Query(default=100, le=150000),
    offset: int = Query(default=0, ge=0)
):
    """Obtener datos de operatividad con filtros y paginación"""
    with get_db() as conn:
        cursor = conn.cursor()
        where_clause, params = build_where_clause(fecha_inicio, fecha_fin, sedes, estados, placas)
        
        # Contar total de registros
        count_query = f"SELECT COUNT(*) FROM operatividad_vehiculos {where_clause}"
        cursor.execute(count_query, params)
        total = cursor.fetchone()[0]
        
        # Obtener registros paginados
        query = f"SELECT * FROM operatividad_vehiculos {where_clause} ORDER BY fecha_ejecucion DESC LIMIT {limit} OFFSET {offset}"
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return {"data": [dict(row) for row in rows], "total": total}


@router.get("/filters")
async def get_filters():
    """Obtener opciones disponibles para filtros (alias de /filtros)"""
    return await get_filtros()


@router.get("/filtros")
async def get_filtros():
    """Obtener opciones disponibles para filtros"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT sede FROM operatividad_vehiculos WHERE sede IS NOT NULL ORDER BY sede")
        sedes = [row[0] for row in cursor.fetchall()]
        cursor.execute("SELECT DISTINCT estado_vehiculo FROM operatividad_vehiculos WHERE estado_vehiculo IS NOT NULL ORDER BY estado_vehiculo")
        estados = [row[0] for row in cursor.fetchall()]
        cursor.execute("SELECT DISTINCT placa FROM operatividad_vehiculos WHERE placa IS NOT NULL ORDER BY placa")
        placas = [row[0] for row in cursor.fetchall()]
        cursor.execute("SELECT MIN(fecha_ejecucion), MAX(fecha_ejecucion) FROM operatividad_vehiculos")
        fecha_min, fecha_max = cursor.fetchone()
        return {"sedes": sedes, "estados": estados, "placas": placas, "fecha_min": fecha_min, "fecha_max": fecha_max}


@router.get("/kpis")
async def get_kpis(
    fecha_inicio: Optional[str] = None, fecha_fin: Optional[str] = None,
    sedes: Optional[str] = None, estados: Optional[str] = None, placas: Optional[str] = None
):
    """Obtener KPIs de operatividad (con caché)"""
    # Verificar caché
    cache_key = generate_cache_key("operatividad:kpis", 
        fecha_inicio=fecha_inicio, fecha_fin=fecha_fin, 
        sedes=sedes, estados=estados, placas=placas)
    cached = cache_get(cache_key)
    if cached:
        return cached
    
    with get_db() as conn:
        cursor = conn.cursor()
        where_clause, params = build_where_clause(fecha_inicio, fecha_fin, sedes, estados, placas)
        
        cursor.execute(f'''
            SELECT SUM(vehiculos_programados), SUM(vehiculos_operativos), SUM(dias_en_taller),
                   COUNT(DISTINCT placa), COUNT(DISTINCT estado_vehiculo),
                   MIN(fecha_ejecucion), MAX(fecha_ejecucion)
            FROM operatividad_vehiculos {where_clause}
        ''', params)
        row = cursor.fetchone()
        programados = row[0] or 0
        operativos = row[1] or 0
        pct_operacion = (operativos / programados * 100) if programados > 0 else 0
        
        result = {
            "pct_operacion": round(pct_operacion, 1),
            "vehiculos_programados": programados,
            "vehiculos_operativos": operativos,
            "dias_taller": row[2] or 0,
            "placas_unicas": row[3] or 0,
            "estados": row[4] or 0,
            "fecha_min": row[5],
            "fecha_max": row[6]
        }
        
        cache_set(cache_key, result, CACHE_TTL)
        return result


@router.get("/grafico/diario")
async def get_diaria(
    fecha_inicio: Optional[str] = None, fecha_fin: Optional[str] = None,
    sedes: Optional[str] = None, estados: Optional[str] = None, placas: Optional[str] = None
):
    """Datos para gráfico de operación diaria (con caché)"""
    cache_key = generate_cache_key("operatividad:diario", 
        fecha_inicio=fecha_inicio, fecha_fin=fecha_fin, 
        sedes=sedes, estados=estados, placas=placas)
    cached = cache_get(cache_key)
    if cached:
        return cached
    
    with get_db() as conn:
        cursor = conn.cursor()
        where_clause, params = build_where_clause(fecha_inicio, fecha_fin, sedes, estados, placas)
        cursor.execute(f'''
            SELECT fecha_ejecucion, SUM(vehiculos_programados), SUM(vehiculos_operativos)
            FROM operatividad_vehiculos {where_clause}
            GROUP BY fecha_ejecucion ORDER BY fecha_ejecucion
        ''', params)
        results = []
        for row in cursor.fetchall():
            programados, operativos = row[1] or 0, row[2] or 0
            pct = (operativos / programados * 100) if programados > 0 else 0
            results.append({"fecha": row[0], "programados": programados, "operativos": operativos, "pct_operacion": round(pct, 1)})
        
        cache_set(cache_key, results, CACHE_TTL)
        return results


@router.get("/grafico/sede")
async def get_por_sede(
    fecha_inicio: Optional[str] = None, fecha_fin: Optional[str] = None,
    sedes: Optional[str] = None, estados: Optional[str] = None, placas: Optional[str] = None
):
    """Datos para gráfico por sede (con caché)"""
    cache_key = generate_cache_key("operatividad:sede", 
        fecha_inicio=fecha_inicio, fecha_fin=fecha_fin, 
        sedes=sedes, estados=estados, placas=placas)
    cached = cache_get(cache_key)
    if cached:
        return cached
    
    with get_db() as conn:
        cursor = conn.cursor()
        where_clause, params = build_where_clause(fecha_inicio, fecha_fin, sedes, estados, placas)
        cursor.execute(f'''
            SELECT sede, SUM(vehiculos_programados), SUM(vehiculos_operativos)
            FROM operatividad_vehiculos {where_clause}
            GROUP BY sede ORDER BY SUM(vehiculos_operativos) DESC
        ''', params)
        results = []
        for row in cursor.fetchall():
            programados, operativos = row[1] or 0, row[2] or 0
            pct = (operativos / programados * 100) if programados > 0 else 0
            results.append({"sede": row[0], "programados": programados, "operativos": operativos, "pct_operacion": round(pct, 1)})
        
        cache_set(cache_key, results, CACHE_TTL)
        return results


@router.get("/grafico/estado")
async def get_por_estado(
    fecha_inicio: Optional[str] = None, fecha_fin: Optional[str] = None,
    sedes: Optional[str] = None, estados: Optional[str] = None, placas: Optional[str] = None
):
    """Datos para gráfico por estado (con caché)"""
    cache_key = generate_cache_key("operatividad:estado", 
        fecha_inicio=fecha_inicio, fecha_fin=fecha_fin, 
        sedes=sedes, estados=estados, placas=placas)
    cached = cache_get(cache_key)
    if cached:
        return cached
    
    with get_db() as conn:
        cursor = conn.cursor()
        where_clause, params = build_where_clause(fecha_inicio, fecha_fin, sedes, estados, placas)
        cursor.execute(f"SELECT estado_vehiculo, COUNT(*) FROM operatividad_vehiculos {where_clause} GROUP BY estado_vehiculo ORDER BY COUNT(*) DESC", params)
        results = [{"estado": row[0], "cantidad": row[1]} for row in cursor.fetchall()]
        
        cache_set(cache_key, results, CACHE_TTL)
        return results


@router.get("/grafico/taller")
async def get_top_dias_taller(
    fecha_inicio: Optional[str] = None, fecha_fin: Optional[str] = None,
    sedes: Optional[str] = None, estados: Optional[str] = None, placas: Optional[str] = None,
    limit: int = 10
):
    """Top placas por días en taller (con caché)"""
    cache_key = generate_cache_key("operatividad:taller", 
        fecha_inicio=fecha_inicio, fecha_fin=fecha_fin, 
        sedes=sedes, estados=estados, placas=placas, limit=limit)
    cached = cache_get(cache_key)
    if cached:
        return cached
    
    with get_db() as conn:
        cursor = conn.cursor()
        where_clause, params = build_where_clause(fecha_inicio, fecha_fin, sedes, estados, placas)
        cursor.execute(f'''
            SELECT placa, SUM(dias_en_taller) as total_dias
            FROM operatividad_vehiculos {where_clause}
            GROUP BY placa HAVING total_dias > 0
            ORDER BY total_dias DESC LIMIT {limit}
        ''', params)
        results = [{"placa": row[0], "dias": row[1]} for row in cursor.fetchall()]
        
        cache_set(cache_key, results, CACHE_TTL)
        return results
