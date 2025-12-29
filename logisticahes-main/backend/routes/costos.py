"""
Rutas API para Costos Mensuales
"""
from fastapi import APIRouter, Query
from typing import Optional
from ..database import get_db

router = APIRouter(prefix="/api/costos", tags=["Costos Mensuales"])


def build_where_clause(fecha_inicio, fecha_fin, catalogos, ciudades, terceros):
    """Construir cláusula WHERE y parámetros"""
    where_clause = "WHERE 1=1"
    params = []
    
    if fecha_inicio:
        where_clause += " AND fecha >= ?"
        params.append(fecha_inicio)
    if fecha_fin:
        where_clause += " AND fecha <= ?"
        params.append(fecha_fin)
    if catalogos:
        catalogo_list = catalogos.split(",")
        placeholders = ",".join(["?" for _ in catalogo_list])
        where_clause += f" AND catalogo IN ({placeholders})"
        params.extend(catalogo_list)
    if ciudades:
        ciudad_list = ciudades.split(",")
        placeholders = ",".join(["?" for _ in ciudad_list])
        where_clause += f" AND ciudad IN ({placeholders})"
        params.extend(ciudad_list)
    if terceros:
        tercero_list = terceros.split(",")
        placeholders = ",".join(["?" for _ in tercero_list])
        where_clause += f" AND tercero IN ({placeholders})"
        params.extend(tercero_list)
    
    return where_clause, params


@router.get("/datos")
async def get_datos(
    fecha_inicio: Optional[str] = None,
    fecha_fin: Optional[str] = None,
    catalogos: Optional[str] = None,
    ciudades: Optional[str] = None,
    terceros: Optional[str] = None,
    limit: int = Query(default=50000, le=150000)
):
    """Obtener datos de costos mensuales con filtros"""
    with get_db() as conn:
        cursor = conn.cursor()
        where_clause, params = build_where_clause(fecha_inicio, fecha_fin, catalogos, ciudades, terceros)
        query = f"SELECT * FROM costos_mensuales {where_clause} ORDER BY fecha DESC LIMIT {limit}"
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return {"data": [dict(row) for row in rows], "total": len(rows)}


@router.get("/filtros")
async def get_filtros():
    """Obtener opciones disponibles para filtros"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT catalogo FROM costos_mensuales WHERE catalogo IS NOT NULL ORDER BY catalogo")
        catalogos = [row[0] for row in cursor.fetchall()]
        cursor.execute("SELECT DISTINCT ciudad FROM costos_mensuales WHERE ciudad IS NOT NULL ORDER BY ciudad")
        ciudades = [row[0] for row in cursor.fetchall()]
        cursor.execute("SELECT DISTINCT tercero FROM costos_mensuales WHERE tercero IS NOT NULL ORDER BY tercero")
        terceros = [row[0] for row in cursor.fetchall()]
        cursor.execute("SELECT MIN(fecha), MAX(fecha) FROM costos_mensuales")
        fecha_min, fecha_max = cursor.fetchone()
        return {"catalogos": catalogos, "ciudades": ciudades, "terceros": terceros, "fecha_min": fecha_min, "fecha_max": fecha_max}


@router.get("/kpis")
async def get_kpis(
    fecha_inicio: Optional[str] = None,
    fecha_fin: Optional[str] = None,
    catalogos: Optional[str] = None,
    ciudades: Optional[str] = None,
    terceros: Optional[str] = None
):
    """Obtener KPIs de costos mensuales"""
    with get_db() as conn:
        cursor = conn.cursor()
        where_clause, params = build_where_clause(fecha_inicio, fecha_fin, catalogos, ciudades, terceros)
        
        cursor.execute(f"SELECT SUM(neto), COUNT(*) FROM costos_mensuales {where_clause}", params)
        costo_total, registros = cursor.fetchone()
        cursor.execute(f"SELECT COUNT(DISTINCT tercero) FROM costos_mensuales {where_clause}", params)
        terceros_unicos = cursor.fetchone()[0]
        cursor.execute(f"SELECT COUNT(DISTINCT catalogo) FROM costos_mensuales {where_clause}", params)
        catalogos_unicos = cursor.fetchone()[0]
        cursor.execute(f"SELECT COUNT(DISTINCT strftime('%Y-%m', fecha)) FROM costos_mensuales {where_clause}", params)
        meses = cursor.fetchone()[0] or 1
        
        return {
            "costo_total": costo_total or 0,
            "registros": registros or 0,
            "terceros_unicos": terceros_unicos or 0,
            "catalogos_unicos": catalogos_unicos or 0,
            "promedio_mensual": (costo_total or 0) / meses
        }


@router.get("/grafico/mensual")
async def get_mensual(
    fecha_inicio: Optional[str] = None, fecha_fin: Optional[str] = None,
    catalogos: Optional[str] = None, ciudades: Optional[str] = None, terceros: Optional[str] = None
):
    """Datos para gráfico de costos mensuales"""
    with get_db() as conn:
        cursor = conn.cursor()
        where_clause, params = build_where_clause(fecha_inicio, fecha_fin, catalogos, ciudades, terceros)
        cursor.execute(f"SELECT strftime('%Y-%m', fecha) as mes, SUM(neto) as total FROM costos_mensuales {where_clause} GROUP BY mes ORDER BY mes", params)
        return [{"mes": row[0], "total": row[1]} for row in cursor.fetchall()]


@router.get("/grafico/catalogo")
async def get_por_catalogo(
    fecha_inicio: Optional[str] = None, fecha_fin: Optional[str] = None,
    catalogos: Optional[str] = None, ciudades: Optional[str] = None, terceros: Optional[str] = None
):
    """Datos para gráfico por catálogo"""
    with get_db() as conn:
        cursor = conn.cursor()
        where_clause, params = build_where_clause(fecha_inicio, fecha_fin, catalogos, ciudades, terceros)
        cursor.execute(f"SELECT catalogo, SUM(neto) as total FROM costos_mensuales {where_clause} GROUP BY catalogo ORDER BY total DESC", params)
        return [{"catalogo": row[0], "total": row[1]} for row in cursor.fetchall()]


@router.get("/grafico/ciudad")
async def get_por_ciudad(
    fecha_inicio: Optional[str] = None, fecha_fin: Optional[str] = None,
    catalogos: Optional[str] = None, ciudades: Optional[str] = None, terceros: Optional[str] = None,
    limit: int = 10
):
    """Datos para gráfico por ciudad (Top N)"""
    with get_db() as conn:
        cursor = conn.cursor()
        where_clause, params = build_where_clause(fecha_inicio, fecha_fin, catalogos, ciudades, terceros)
        cursor.execute(f"SELECT ciudad, SUM(neto) as total FROM costos_mensuales {where_clause} GROUP BY ciudad ORDER BY total DESC LIMIT {limit}", params)
        return [{"ciudad": row[0], "total": row[1]} for row in cursor.fetchall()]


@router.get("/grafico/tercero")
async def get_por_tercero(
    fecha_inicio: Optional[str] = None, fecha_fin: Optional[str] = None,
    catalogos: Optional[str] = None, ciudades: Optional[str] = None, terceros: Optional[str] = None,
    limit: int = 10
):
    """Datos para gráfico por tercero (Top N)"""
    with get_db() as conn:
        cursor = conn.cursor()
        where_clause, params = build_where_clause(fecha_inicio, fecha_fin, catalogos, ciudades, terceros)
        cursor.execute(f"SELECT tercero, SUM(neto) as total FROM costos_mensuales {where_clause} GROUP BY tercero ORDER BY total DESC LIMIT {limit}", params)
        return [{"tercero": row[0], "total": row[1]} for row in cursor.fetchall()]
