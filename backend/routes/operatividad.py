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
    offset: int = Query(default=0, ge=0),
    order_by: Optional[str] = Query(default="fecha_ejecucion"),
    order_dir: Optional[str] = Query(default="DESC")
):
    """Obtener datos de operatividad con filtros, paginación y ordenamiento"""
    # Validar columna de ordenamiento para evitar SQL injection
    valid_columns = {
        'fecha_ejecucion', 'sede', 'estado_vehiculo', 'placa', 'tipo_vehiculo',
        'brigada', 'conductor', 'contrato', 'vehiculos_programados', 
        'vehiculos_operativos', 'dias_en_taller', 'motivo_inoperatividad'
    }
    if order_by not in valid_columns:
        order_by = 'fecha_ejecucion'
    
    # Validar dirección de ordenamiento
    order_dir = 'DESC' if order_dir.upper() == 'DESC' else 'ASC'
    
    with get_db() as conn:
        cursor = conn.cursor()
        where_clause, params = build_where_clause(fecha_inicio, fecha_fin, sedes, estados, placas)
        
        # Contar total de registros
        count_query = f"SELECT COUNT(*) FROM operatividad_vehiculos {where_clause}"
        cursor.execute(count_query, params)
        total = cursor.fetchone()[0]
        
        # Obtener registros paginados con ordenamiento
        query = f"SELECT * FROM operatividad_vehiculos {where_clause} ORDER BY {order_by} {order_dir} LIMIT {limit} OFFSET {offset}"
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return {"data": [dict(row) for row in rows], "total": total}


@router.get("/filters")
async def get_filters(
    fecha_inicio: Optional[str] = None,
    fecha_fin: Optional[str] = None,
    sedes: Optional[str] = None,
    estados: Optional[str] = None
):
    """Obtener opciones disponibles para filtros (con filtrado encadenado)"""
    return await get_filtros(fecha_inicio, fecha_fin, sedes, estados)


@router.get("/filtros")
async def get_filtros(
    fecha_inicio: Optional[str] = None,
    fecha_fin: Optional[str] = None,
    sedes: Optional[str] = None,
    estados: Optional[str] = None
):
    """Obtener opciones disponibles para filtros con filtrado encadenado.
    
    - sedes: siempre devuelve todas las sedes disponibles
    - estados: filtrados por sede si se especifica
    - placas: filtradas por sede y estado si se especifican
    """
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Sedes: siempre todas las disponibles (sin filtrar)
        cursor.execute("SELECT DISTINCT sede FROM operatividad_vehiculos WHERE sede IS NOT NULL ORDER BY sede")
        all_sedes = [row[0] for row in cursor.fetchall()]
        
        # Fechas min/max
        cursor.execute("SELECT MIN(fecha_ejecucion), MAX(fecha_ejecucion) FROM operatividad_vehiculos")
        fecha_min, fecha_max = cursor.fetchone()
        
        # Construir filtro base para estados (por sede y fechas)
        where_estados = "WHERE estado_vehiculo IS NOT NULL"
        params_estados = []
        
        if fecha_inicio:
            where_estados += " AND fecha_ejecucion >= ?"
            params_estados.append(fecha_inicio)
        if fecha_fin:
            where_estados += " AND fecha_ejecucion <= ?"
            params_estados.append(fecha_fin)
        if sedes:
            sede_list = sedes.split(",")
            placeholders = ",".join(["?" for _ in sede_list])
            where_estados += f" AND sede IN ({placeholders})"
            params_estados.extend(sede_list)
        
        cursor.execute(f"SELECT DISTINCT estado_vehiculo FROM operatividad_vehiculos {where_estados} ORDER BY estado_vehiculo", params_estados)
        filtered_estados = [row[0] for row in cursor.fetchall()]
        
        # Construir filtro para placas (por sede, estado y fechas)
        where_placas = "WHERE placa IS NOT NULL"
        params_placas = []
        
        if fecha_inicio:
            where_placas += " AND fecha_ejecucion >= ?"
            params_placas.append(fecha_inicio)
        if fecha_fin:
            where_placas += " AND fecha_ejecucion <= ?"
            params_placas.append(fecha_fin)
        if sedes:
            sede_list = sedes.split(",")
            placeholders = ",".join(["?" for _ in sede_list])
            where_placas += f" AND sede IN ({placeholders})"
            params_placas.extend(sede_list)
        if estados:
            estado_list = estados.split(",")
            placeholders = ",".join(["?" for _ in estado_list])
            where_placas += f" AND estado_vehiculo IN ({placeholders})"
            params_placas.extend(estado_list)
        
        cursor.execute(f"SELECT DISTINCT placa FROM operatividad_vehiculos {where_placas} ORDER BY placa", params_placas)
        filtered_placas = [row[0] for row in cursor.fetchall()]
        
        return {
            "sedes": all_sedes, 
            "estados": filtered_estados, 
            "placas": filtered_placas, 
            "fecha_min": fecha_min, 
            "fecha_max": fecha_max
        }


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


@router.get("/resumen/sede")
async def get_resumen_por_sede(
    fecha_inicio: Optional[str] = None, fecha_fin: Optional[str] = None,
    sedes: Optional[str] = None, estados: Optional[str] = None, placas: Optional[str] = None
):
    """Resumen BI: placas únicas y días por estado para cada sede"""
    cache_key = generate_cache_key("operatividad:resumen_sede", 
        fecha_inicio=fecha_inicio, fecha_fin=fecha_fin, 
        sedes=sedes, estados=estados, placas=placas)
    cached = cache_get(cache_key)
    if cached:
        return cached
    
    with get_db() as conn:
        cursor = conn.cursor()
        where_clause, params = build_where_clause(fecha_inicio, fecha_fin, sedes, estados, placas)
        
        # Obtener placas únicas y días por sede y estado
        cursor.execute(f'''
            SELECT sede, estado_vehiculo, 
                   COUNT(DISTINCT placa) as placas,
                   COUNT(*) as dias
            FROM operatividad_vehiculos
            {where_clause}
            GROUP BY sede, estado_vehiculo
            ORDER BY sede, estado_vehiculo
        ''', params)
        rows = cursor.fetchall()
        
        # Organizar datos por sede
        resumen = {}
        estados_set = set()
        for row in rows:
            sede = row['sede'] or 'Sin sede'
            estado = row['estado_vehiculo'] or 'Sin estado'
            placas_count = row['placas']
            dias = row['dias']
            estados_set.add(estado)
            
            if sede not in resumen:
                resumen[sede] = {
                    'sede': sede, 
                    'total_placas': 0, 
                    'total_dias': 0,
                    'dias_operativo': 0,
                    'dias_no_operativo': 0
                }
            
            # Guardar placas y días por estado
            resumen[sede][f'{estado}_placas'] = placas_count
            resumen[sede][f'{estado}_dias'] = dias
            resumen[sede]['total_placas'] += placas_count
            resumen[sede]['total_dias'] += dias
            
            # Sumar días operativos vs no operativos
            if estado == 'Operativo':
                resumen[sede]['dias_operativo'] = dias
            else:
                resumen[sede]['dias_no_operativo'] += dias
        
        # Calcular porcentaje de operatividad
        for sede_data in resumen.values():
            total = sede_data['total_dias']
            if total > 0:
                sede_data['pct_operatividad'] = round((sede_data['dias_operativo'] / total) * 100, 1)
            else:
                sede_data['pct_operatividad'] = 0
        
        # Convertir a lista ordenada
        result = {
            'data': sorted(resumen.values(), key=lambda x: x['sede']),
            'estados': sorted(list(estados_set))
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
        print(f"🔵 CACHE HIT estado: placas={placas}")
        return cached
    
    print(f"🟡 CACHE MISS estado: placas={placas}, estados={estados}")
    
    with get_db() as conn:
        cursor = conn.cursor()
        where_clause, params = build_where_clause(fecha_inicio, fecha_fin, sedes, estados, placas)
        print(f"🟡 WHERE estado: {where_clause}, params: {params}")
        cursor.execute(f"SELECT estado_vehiculo, COUNT(*) FROM operatividad_vehiculos {where_clause} GROUP BY estado_vehiculo ORDER BY COUNT(*) DESC", params)
        results = [{"estado": row[0], "cantidad": row[1]} for row in cursor.fetchall()]
        print(f"🟢 Resultados estado: {results}")
        
        cache_set(cache_key, results, CACHE_TTL)
        return results


@router.get("/grafico/taller")
async def get_top_dias_taller(
    fecha_inicio: Optional[str] = None, fecha_fin: Optional[str] = None,
    sedes: Optional[str] = None, estados: Optional[str] = None, placas: Optional[str] = None,
    limit: int = 10
):
    """Días por estado para cada placa (gráfico de barras apiladas)"""
    cache_key = generate_cache_key("operatividad:taller", 
        fecha_inicio=fecha_inicio, fecha_fin=fecha_fin, 
        sedes=sedes, estados=estados, placas=placas, limit=limit)
    cached = cache_get(cache_key)
    if cached:
        print(f"🔵 CACHE HIT para taller: {cache_key}")
        return cached
    
    print(f"🟡 CACHE MISS para taller: {cache_key}")
    print(f"🟡 Filtros: fecha_inicio={fecha_inicio}, fecha_fin={fecha_fin}, sedes={sedes}, placas={placas[:100] if placas else None}...")
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Construir WHERE para filtrar datos base
        where_parts = ["1=1"]
        params = []
        
        if fecha_inicio:
            where_parts.append("fecha_ejecucion >= ?")
            params.append(fecha_inicio)
        if fecha_fin:
            where_parts.append("fecha_ejecucion <= ?")
            params.append(fecha_fin)
        if sedes:
            sede_list = sedes.split(",")
            placeholders = ",".join(["?" for _ in sede_list])
            where_parts.append(f"sede IN ({placeholders})")
            params.extend(sede_list)
        if placas:
            placa_list = [p.strip() for p in placas.split(",") if p.strip()]
            if placa_list:
                placeholders = ",".join(["?" for _ in placa_list])
                where_parts.append(f"placa IN ({placeholders})")
                params.extend(placa_list)
        
        where_clause = "WHERE " + " AND ".join(where_parts)
        print(f"🟡 WHERE taller: {where_clause}")
        
        # Obtener días por estado para cada placa
        query = f'''
            SELECT placa, estado_vehiculo, COUNT(*) as dias
            FROM operatividad_vehiculos {where_clause}
            GROUP BY placa, estado_vehiculo
            ORDER BY placa, estado_vehiculo
        '''
        print(f"🟡 Query params count: {len(params)}")
        cursor.execute(query, params)
        
        # Organizar datos por placa
        placa_data = {}
        for row in cursor.fetchall():
            placa, estado, dias = row[0], row[1], row[2]
            if placa not in placa_data:
                placa_data[placa] = {"placa": placa, "estados": {}}
            placa_data[placa]["estados"][estado] = dias
        
        print(f"🟡 Placas encontradas: {len(placa_data)}")
        
        # Convertir a lista y ordenar por total de días
        results = []
        for placa, data in placa_data.items():
            total = sum(data["estados"].values())
            results.append({
                "placa": placa,
                "estados": data["estados"],
                "total": total
            })
        
        # Ordenar por total descendente y limitar
        results.sort(key=lambda x: x["total"], reverse=True)
        results = results[:limit]
        
        print(f"🟢 Resultados taller: {len(results)} placas")
        
        cache_set(cache_key, results, CACHE_TTL)
        return results