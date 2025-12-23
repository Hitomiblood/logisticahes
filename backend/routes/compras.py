"""
Rutas API para Compras (3 tablas: traza_req_oc, oc_descuentos, base_oc_generadas)
Columnas reales según la BD:
- traza_req_oc: req_estado, oc_estado, oc_tercero_nombre, req_fecha, oc_fecha, etc.
- oc_descuentos: estado, tercero_nombre, fecha, total_dcto, porcentaje_descuento, etc.
- base_oc_generadas: estado, tercero_nombre, fecha, documento_tipo, total, etc.
"""
from fastapi import APIRouter, Query
from typing import Optional, Dict, Any
from pydantic import BaseModel
from ..database import get_db

router = APIRouter(prefix="/api/compras", tags=["Compras"])


# Modelo para filtros POST
class FilterRequest(BaseModel):
    dateStart: Optional[str] = None
    dateEnd: Optional[str] = None
    processes: Optional[list] = None
    suppliers: Optional[list] = None
    states: Optional[list] = None


# ==================== ENDPOINTS PRINCIPALES ====================
@router.get("/load")
async def load_data():
    """Verificar datos cargados en las 3 tablas de compras"""
    with get_db() as conn:
        cursor = conn.cursor()
        counts = {}
        for table in ["traza_req_oc", "oc_descuentos", "base_oc_generadas"]:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                counts[table] = cursor.fetchone()[0]
            except:
                counts[table] = 0
        return {"success": True, "counts": counts}


@router.get("/filters")
async def get_filters():
    """Obtener todas las opciones de filtros para el dashboard"""
    with get_db() as conn:
        cursor = conn.cursor()
        filters = {}
        
        # Filtros de TRAZA REQ OC
        cursor.execute("SELECT DISTINCT req_estado FROM traza_req_oc WHERE req_estado IS NOT NULL ORDER BY req_estado")
        filters["estados_req"] = [row[0] for row in cursor.fetchall()]
        cursor.execute("SELECT DISTINCT oc_estado FROM traza_req_oc WHERE oc_estado IS NOT NULL ORDER BY oc_estado")
        filters["estados_oc"] = [row[0] for row in cursor.fetchall()]
        cursor.execute("SELECT DISTINCT oc_tercero_nombre FROM traza_req_oc WHERE oc_tercero_nombre IS NOT NULL ORDER BY oc_tercero_nombre LIMIT 500")
        filters["terceros_traza"] = [row[0] for row in cursor.fetchall()]
        
        # Filtros de OC DESCUENTOS
        cursor.execute("SELECT DISTINCT tercero_nombre FROM oc_descuentos WHERE tercero_nombre IS NOT NULL ORDER BY tercero_nombre LIMIT 500")
        filters["terceros_descuentos"] = [row[0] for row in cursor.fetchall()]
        cursor.execute("SELECT DISTINCT estado FROM oc_descuentos WHERE estado IS NOT NULL ORDER BY estado")
        filters["estados_descuentos"] = [row[0] for row in cursor.fetchall()]
        
        # Filtros de BASE OC GENERADAS
        cursor.execute("SELECT DISTINCT tercero_nombre FROM base_oc_generadas WHERE tercero_nombre IS NOT NULL ORDER BY tercero_nombre LIMIT 500")
        filters["terceros_base"] = [row[0] for row in cursor.fetchall()]
        cursor.execute("SELECT DISTINCT documento_tipo FROM base_oc_generadas WHERE documento_tipo IS NOT NULL ORDER BY documento_tipo")
        filters["tipos_doc"] = [row[0] for row in cursor.fetchall()]
        cursor.execute("SELECT DISTINCT estado FROM base_oc_generadas WHERE estado IS NOT NULL ORDER BY estado")
        filters["estados_base"] = [row[0] for row in cursor.fetchall()]
        
        return {"success": True, "filters": filters}


# ==================== TRAZA REQ OC ====================
def build_traza_where(fecha_inicio, fecha_fin, estados_req, estados_oc, terceros):
    where_clause = "WHERE 1=1"
    params = []
    if fecha_inicio:
        where_clause += " AND req_fecha >= ?"
        params.append(fecha_inicio)
    if fecha_fin:
        where_clause += " AND req_fecha <= ?"
        params.append(fecha_fin)
    if estados_req:
        lista = estados_req.split(",")
        where_clause += f" AND req_estado IN ({','.join(['?' for _ in lista])})"
        params.extend(lista)
    if estados_oc:
        lista = estados_oc.split(",")
        where_clause += f" AND oc_estado IN ({','.join(['?' for _ in lista])})"
        params.extend(lista)
    if terceros:
        lista = terceros.split(",")
        where_clause += f" AND oc_tercero_nombre IN ({','.join(['?' for _ in lista])})"
        params.extend(lista)
    return where_clause, params


@router.get("/traza/datos")
async def get_traza_datos(
    fecha_inicio: Optional[str] = None, fecha_fin: Optional[str] = None,
    estados_req: Optional[str] = None, estados_oc: Optional[str] = None, terceros: Optional[str] = None,
    limit: int = Query(default=100000, le=150000)
):
    with get_db() as conn:
        cursor = conn.cursor()
        where_clause, params = build_traza_where(fecha_inicio, fecha_fin, estados_req, estados_oc, terceros)
        cursor.execute(f"SELECT * FROM traza_req_oc {where_clause} LIMIT {limit}", params)
        rows = cursor.fetchall()
        return {"data": [dict(row) for row in rows], "total": len(rows)}


@router.get("/traza/filtros")
async def get_traza_filtros():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT req_estado FROM traza_req_oc WHERE req_estado IS NOT NULL ORDER BY req_estado")
        estados_req = [row[0] for row in cursor.fetchall()]
        cursor.execute("SELECT DISTINCT oc_estado FROM traza_req_oc WHERE oc_estado IS NOT NULL ORDER BY oc_estado")
        estados_oc = [row[0] for row in cursor.fetchall()]
        cursor.execute("SELECT DISTINCT oc_tercero_nombre FROM traza_req_oc WHERE oc_tercero_nombre IS NOT NULL ORDER BY oc_tercero_nombre LIMIT 500")
        terceros = [row[0] for row in cursor.fetchall()]
        cursor.execute("SELECT MIN(req_fecha), MAX(req_fecha) FROM traza_req_oc")
        fecha_min, fecha_max = cursor.fetchone()
        return {"estados_req": estados_req, "estados_oc": estados_oc, "terceros": terceros, "fecha_min": fecha_min, "fecha_max": fecha_max}


@router.get("/traza/kpis")
async def get_traza_kpis(
    fecha_inicio: Optional[str] = None, fecha_fin: Optional[str] = None,
    estados_req: Optional[str] = None, estados_oc: Optional[str] = None, terceros: Optional[str] = None
):
    with get_db() as conn:
        cursor = conn.cursor()
        where_clause, params = build_traza_where(fecha_inicio, fecha_fin, estados_req, estados_oc, terceros)
        cursor.execute(f'''SELECT COUNT(*), COUNT(DISTINCT req_numero), COUNT(DISTINCT oc_numero),
            AVG(dias_aprobar_rq), AVG(dias_generar_oc)
            FROM traza_req_oc {where_clause}''', params)
        row = cursor.fetchone()
        return {
            "total_registros": row[0], 
            "requisiciones": row[1], 
            "ordenes_compra": row[2],
            "dias_promedio_aprobar": round(row[3] or 0, 1),
            "dias_promedio_generar_oc": round(row[4] or 0, 1)
        }


# ==================== OC DESCUENTOS ====================
def build_descuentos_where(fecha_inicio, fecha_fin, terceros, estados):
    where_clause = "WHERE 1=1"
    params = []
    if fecha_inicio:
        where_clause += " AND fecha >= ?"
        params.append(fecha_inicio)
    if fecha_fin:
        where_clause += " AND fecha <= ?"
        params.append(fecha_fin)
    if terceros:
        lista = terceros.split(",")
        where_clause += f" AND tercero_nombre IN ({','.join(['?' for _ in lista])})"
        params.extend(lista)
    if estados:
        lista = estados.split(",")
        where_clause += f" AND estado IN ({','.join(['?' for _ in lista])})"
        params.extend(lista)
    return where_clause, params


@router.get("/descuentos/datos")
async def get_descuentos_datos(
    fecha_inicio: Optional[str] = None, fecha_fin: Optional[str] = None,
    terceros: Optional[str] = None, estados: Optional[str] = None,
    limit: int = Query(default=100000, le=150000)
):
    with get_db() as conn:
        cursor = conn.cursor()
        where_clause, params = build_descuentos_where(fecha_inicio, fecha_fin, terceros, estados)
        cursor.execute(f"SELECT * FROM oc_descuentos {where_clause} LIMIT {limit}", params)
        rows = cursor.fetchall()
        return {"data": [dict(row) for row in rows], "total": len(rows)}


@router.get("/descuentos/filtros")
async def get_descuentos_filtros():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT tercero_nombre FROM oc_descuentos WHERE tercero_nombre IS NOT NULL ORDER BY tercero_nombre LIMIT 500")
        terceros = [row[0] for row in cursor.fetchall()]
        cursor.execute("SELECT DISTINCT estado FROM oc_descuentos WHERE estado IS NOT NULL ORDER BY estado")
        estados = [row[0] for row in cursor.fetchall()]
        cursor.execute("SELECT MIN(fecha), MAX(fecha) FROM oc_descuentos")
        fecha_min, fecha_max = cursor.fetchone()
        return {"terceros": terceros, "estados": estados, "fecha_min": fecha_min, "fecha_max": fecha_max}


@router.get("/descuentos/kpis")
async def get_descuentos_kpis(
    fecha_inicio: Optional[str] = None, fecha_fin: Optional[str] = None,
    terceros: Optional[str] = None, estados: Optional[str] = None
):
    with get_db() as conn:
        cursor = conn.cursor()
        where_clause, params = build_descuentos_where(fecha_inicio, fecha_fin, terceros, estados)
        cursor.execute(f'''SELECT COUNT(*), SUM(COALESCE(total_dcto, 0)), SUM(COALESCE(total, 0)),
            COUNT(DISTINCT documento_num), COUNT(DISTINCT tercero_nombre),
            AVG(COALESCE(porcentaje_descuento, 0))
            FROM oc_descuentos {where_clause}''', params)
        row = cursor.fetchone()
        return {
            "total_registros": row[0], 
            "total_descuentos": row[1] or 0,
            "total_compras": row[2] or 0,
            "ordenes_compra": row[3], 
            "proveedores": row[4],
            "pct_descuento_promedio": round(row[5] or 0, 2)
        }


# ==================== BASE OC GENERADAS ====================
def build_base_where(fecha_inicio, fecha_fin, terceros, tipos, estados):
    where_clause = "WHERE 1=1"
    params = []
    if fecha_inicio:
        where_clause += " AND fecha >= ?"
        params.append(fecha_inicio)
    if fecha_fin:
        where_clause += " AND fecha <= ?"
        params.append(fecha_fin)
    if terceros:
        lista = terceros.split(",")
        where_clause += f" AND tercero_nombre IN ({','.join(['?' for _ in lista])})"
        params.extend(lista)
    if tipos:
        lista = tipos.split(",")
        where_clause += f" AND documento_tipo IN ({','.join(['?' for _ in lista])})"
        params.extend(lista)
    if estados:
        lista = estados.split(",")
        where_clause += f" AND estado IN ({','.join(['?' for _ in lista])})"
        params.extend(lista)
    return where_clause, params


@router.get("/base/datos")
async def get_base_datos(
    fecha_inicio: Optional[str] = None, fecha_fin: Optional[str] = None,
    terceros: Optional[str] = None, tipos: Optional[str] = None, estados: Optional[str] = None,
    limit: int = Query(default=100000, le=150000)
):
    with get_db() as conn:
        cursor = conn.cursor()
        where_clause, params = build_base_where(fecha_inicio, fecha_fin, terceros, tipos, estados)
        cursor.execute(f"SELECT * FROM base_oc_generadas {where_clause} LIMIT {limit}", params)
        rows = cursor.fetchall()
        return {"data": [dict(row) for row in rows], "total": len(rows)}


@router.get("/base/filtros")
async def get_base_filtros():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT tercero_nombre FROM base_oc_generadas WHERE tercero_nombre IS NOT NULL ORDER BY tercero_nombre LIMIT 500")
        terceros = [row[0] for row in cursor.fetchall()]
        cursor.execute("SELECT DISTINCT documento_tipo FROM base_oc_generadas WHERE documento_tipo IS NOT NULL ORDER BY documento_tipo")
        tipos = [row[0] for row in cursor.fetchall()]
        cursor.execute("SELECT DISTINCT estado FROM base_oc_generadas WHERE estado IS NOT NULL ORDER BY estado")
        estados = [row[0] for row in cursor.fetchall()]
        cursor.execute("SELECT MIN(fecha), MAX(fecha) FROM base_oc_generadas")
        fecha_min, fecha_max = cursor.fetchone()
        return {"terceros": terceros, "tipos": tipos, "estados": estados, "fecha_min": fecha_min, "fecha_max": fecha_max}


@router.get("/base/kpis")
async def get_base_kpis(
    fecha_inicio: Optional[str] = None, fecha_fin: Optional[str] = None,
    terceros: Optional[str] = None, tipos: Optional[str] = None, estados: Optional[str] = None
):
    with get_db() as conn:
        cursor = conn.cursor()
        where_clause, params = build_base_where(fecha_inicio, fecha_fin, terceros, tipos, estados)
        cursor.execute(f'''SELECT COUNT(*), COUNT(DISTINCT documento_num), 
            SUM(COALESCE(total, 0)), COUNT(DISTINCT tercero_nombre), COUNT(DISTINCT documento_tipo)
            FROM base_oc_generadas {where_clause}''', params)
        row = cursor.fetchone()
        return {
            "total_registros": row[0], 
            "ordenes_compra": row[1], 
            "valor_total": row[2] or 0, 
            "proveedores": row[3], 
            "tipos_doc": row[4]
        }


# ==================== GRÁFICOS COMBINADOS ====================
@router.get("/grafico/por-mes")
async def get_compras_por_mes(
    fecha_inicio: Optional[str] = None, fecha_fin: Optional[str] = None,
    terceros: Optional[str] = None, tipos: Optional[str] = None, estados: Optional[str] = None
):
    with get_db() as conn:
        cursor = conn.cursor()
        where_clause, params = build_base_where(fecha_inicio, fecha_fin, terceros, tipos, estados)
        cursor.execute(f'''
            SELECT strftime('%Y-%m', fecha) as mes, COUNT(*), SUM(COALESCE(total, 0))
            FROM base_oc_generadas {where_clause}
            GROUP BY mes ORDER BY mes
        ''', params)
        return [{"mes": row[0], "cantidad": row[1], "valor": row[2] or 0} for row in cursor.fetchall()]


@router.get("/grafico/por-tercero")
async def get_compras_por_tercero(
    fecha_inicio: Optional[str] = None, fecha_fin: Optional[str] = None,
    terceros: Optional[str] = None, tipos: Optional[str] = None, estados: Optional[str] = None,
    limit: int = 15
):
    with get_db() as conn:
        cursor = conn.cursor()
        where_clause, params = build_base_where(fecha_inicio, fecha_fin, terceros, tipos, estados)
        cursor.execute(f'''
            SELECT tercero_nombre, COUNT(*), SUM(COALESCE(total, 0))
            FROM base_oc_generadas {where_clause}
            GROUP BY tercero_nombre ORDER BY SUM(COALESCE(total, 0)) DESC LIMIT {limit}
        ''', params)
        return [{"tercero": row[0], "cantidad": row[1], "valor": row[2] or 0} for row in cursor.fetchall()]


@router.get("/grafico/por-tipo")
async def get_compras_por_tipo(
    fecha_inicio: Optional[str] = None, fecha_fin: Optional[str] = None,
    terceros: Optional[str] = None, tipos: Optional[str] = None, estados: Optional[str] = None
):
    with get_db() as conn:
        cursor = conn.cursor()
        where_clause, params = build_base_where(fecha_inicio, fecha_fin, terceros, tipos, estados)
        cursor.execute(f'''
            SELECT documento_tipo, COUNT(*) FROM base_oc_generadas {where_clause}
            GROUP BY documento_tipo ORDER BY COUNT(*) DESC
        ''', params)
        return [{"tipo": row[0], "cantidad": row[1]} for row in cursor.fetchall()]


@router.get("/grafico/por-estado")
async def get_compras_por_estado(
    fecha_inicio: Optional[str] = None, fecha_fin: Optional[str] = None,
    terceros: Optional[str] = None, tipos: Optional[str] = None, estados: Optional[str] = None
):
    with get_db() as conn:
        cursor = conn.cursor()
        where_clause, params = build_base_where(fecha_inicio, fecha_fin, terceros, tipos, estados)
        cursor.execute(f'''
            SELECT estado, COUNT(*) FROM base_oc_generadas {where_clause}
            GROUP BY estado ORDER BY COUNT(*) DESC
        ''', params)
        return [{"estado": row[0], "cantidad": row[1]} for row in cursor.fetchall()]


@router.get("/grafico/descuentos-por-tercero")
async def get_descuentos_por_tercero(
    fecha_inicio: Optional[str] = None, fecha_fin: Optional[str] = None,
    terceros: Optional[str] = None, estados: Optional[str] = None,
    limit: int = 15
):
    with get_db() as conn:
        cursor = conn.cursor()
        where_clause, params = build_descuentos_where(fecha_inicio, fecha_fin, terceros, estados)
        cursor.execute(f'''
            SELECT tercero_nombre, SUM(COALESCE(total_dcto, 0)), COUNT(*)
            FROM oc_descuentos {where_clause}
            GROUP BY tercero_nombre ORDER BY SUM(COALESCE(total_dcto, 0)) DESC LIMIT {limit}
        ''', params)
        return [{"tercero": row[0], "descuento": row[1] or 0, "cantidad": row[2]} for row in cursor.fetchall()]


# ==================== ENDPOINTS POST PARA DASHBOARD ====================

@router.post("/kpis")
async def get_kpis_post(filters: FilterRequest):
    """KPIs combinados para el dashboard"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # KPIs de traza_req_oc
        cursor.execute('''SELECT COUNT(*), COUNT(DISTINCT req_numero), COUNT(DISTINCT oc_numero),
            AVG(COALESCE(dias_aprobar_rq, 0)), AVG(COALESCE(dias_generar_oc, 0)),
            AVG(COALESCE(dias_aprobacion_oc, 0)), AVG(COALESCE(dias_recepcion_servicio, 0)),
            AVG(COALESCE(dias_entrada_almacen, 0))
            FROM traza_req_oc''')
        traza = cursor.fetchone()
        
        # KPIs de oc_descuentos
        cursor.execute('''SELECT COUNT(*), SUM(COALESCE(total_dcto, 0)), SUM(COALESCE(total, 0)),
            COUNT(DISTINCT documento_num), AVG(COALESCE(porcentaje_descuento, 0))
            FROM oc_descuentos''')
        desc = cursor.fetchone()
        
        # Pendientes por aprobar RQ
        cursor.execute("SELECT COUNT(*) FROM traza_req_oc WHERE req_estado = 'PENDIENTE' OR req_estado LIKE '%PEND%'")
        pendientes_rq = cursor.fetchone()[0]
        
        # Pendientes por aprobar OC
        cursor.execute("SELECT COUNT(*) FROM traza_req_oc WHERE oc_estado = 'PENDIENTE' OR oc_estado LIKE '%PEND%'")
        pendientes_oc = cursor.fetchone()[0]
        
        return {
            "success": True,
            "kpis": {
                "totalRQ": traza[1] or 0,
                "totalOC": traza[2] or 0,
                "totalItems": traza[0] or 0,
                "totalSpend": desc[2] or 0,
                "percentDispatched": round(desc[4] or 0, 2),
                "diasPromedioAprobarRQ": round(traza[3] or 0, 1),
                "diasPromedioGenerarOC": round(traza[4] or 0, 1),
                "diasPromedioAprobacionOC": round(traza[5] or 0, 1),
                "diasPromedioRecepcionServicio": round(traza[6] or 0, 1),
                "diasPromedioEntradaAlmacen": round(traza[7] or 0, 1),
                "totalDescuentos": desc[1] or 0,
                "pendientesAprobarRQ": pendientes_rq,
                "pendientesAprobarOC": pendientes_oc
            }
        }


@router.post("/charts/oc-vs-items-by-process")
async def chart_oc_vs_items(filters: FilterRequest):
    """Gráfico OC vs Items por proceso"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT proceso, COUNT(DISTINCT documento_num) as total_oc, COUNT(*) as total_items
            FROM oc_descuentos
            WHERE proceso IS NOT NULL
            GROUP BY proceso ORDER BY total_items DESC LIMIT 10
        ''')
        rows = cursor.fetchall()
        procesos = [r[0] or 'Sin Proceso' for r in rows]
        total_oc = [r[1] for r in rows]
        total_items = [r[2] for r in rows]
        
        return {
            "success": True,
            "data": {
                "procesos": procesos,
                "totalOC": total_oc,
                "totalItems": total_items,
                "total": sum(total_items)
            }
        }


@router.post("/charts/percent-discounts-by-process")
async def chart_percent_discounts(filters: FilterRequest):
    """Gráfico porcentaje descuentos por proceso"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT proceso, AVG(COALESCE(porcentaje_descuento, 0)) as avg_pct
            FROM oc_descuentos
            WHERE proceso IS NOT NULL
            GROUP BY proceso ORDER BY avg_pct DESC LIMIT 10
        ''')
        rows = cursor.fetchall()
        
        # Calcular promedio general
        cursor.execute('SELECT AVG(COALESCE(porcentaje_descuento, 0)) FROM oc_descuentos')
        avg_general = cursor.fetchone()[0] or 0
        
        return {
            "success": True,
            "data": {
                "procesos": [r[0] or 'Sin Proceso' for r in rows],
                "percentages": [round(r[1] or 0, 2) for r in rows],
                "average": round(avg_general, 2)
            }
        }


@router.post("/charts/top-suppliers-discounts")
async def chart_top_suppliers_discounts(filters: FilterRequest):
    """Top proveedores por descuentos"""
    with get_db() as conn:
        cursor = conn.cursor()
        # Obtener total de descuentos para calcular porcentaje
        cursor.execute('SELECT SUM(COALESCE(total_dcto, 0)) FROM oc_descuentos')
        total_general = cursor.fetchone()[0] or 1
        
        cursor.execute('''
            SELECT tercero_nombre, SUM(COALESCE(total_dcto, 0)) as total_desc
            FROM oc_descuentos
            WHERE tercero_nombre IS NOT NULL
            GROUP BY tercero_nombre ORDER BY total_desc DESC LIMIT 10
        ''')
        rows = cursor.fetchall()
        
        proveedores = [r[0] for r in rows]
        montos = [r[1] or 0 for r in rows]
        percentages = [(m / total_general * 100) if total_general > 0 else 0 for m in montos]
        
        return {
            "success": True,
            "data": {
                "proveedores": proveedores,
                "montos": montos,
                "percentages": percentages
            }
        }


@router.post("/charts/avg-approval-days")
async def chart_avg_approval_days(filters: FilterRequest):
    """Días promedio aprobación RQ por aprobador"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT req_usuario_autorizador, AVG(COALESCE(dias_aprobar_rq, 0)) as promedio
            FROM traza_req_oc
            WHERE req_usuario_autorizador IS NOT NULL AND dias_aprobar_rq IS NOT NULL
            GROUP BY req_usuario_autorizador ORDER BY promedio DESC LIMIT 10
        ''')
        rows = cursor.fetchall()
        
        return {
            "success": True,
            "data": {
                "aprobadores": [r[0] for r in rows],
                "promedios": [round(r[1] or 0, 1) for r in rows]
            }
        }


@router.post("/charts/avg-generation-days")
async def chart_avg_generation_days(filters: FilterRequest):
    """Días promedio generación OC por comprador"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT oc_usuario, AVG(COALESCE(dias_generar_oc, 0)) as promedio
            FROM traza_req_oc
            WHERE oc_usuario IS NOT NULL AND dias_generar_oc IS NOT NULL
            GROUP BY oc_usuario ORDER BY promedio DESC LIMIT 10
        ''')
        rows = cursor.fetchall()
        
        return {
            "success": True,
            "data": {
                "aprobadores": [r[0] for r in rows],
                "promedios": [round(r[1] or 0, 1) for r in rows]
            }
        }


@router.post("/charts/avg-approval-management-days")
async def chart_avg_approval_management(filters: FilterRequest):
    """Días promedio aprobación gerencial OC por aprobador"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT oc_usuario_autorizacion, AVG(COALESCE(dias_aprobacion_oc, 0)) as promedio
            FROM traza_req_oc
            WHERE oc_usuario_autorizacion IS NOT NULL AND dias_aprobacion_oc IS NOT NULL
            GROUP BY oc_usuario_autorizacion ORDER BY promedio DESC LIMIT 10
        ''')
        rows = cursor.fetchall()
        
        return {
            "success": True,
            "data": {
                "aprobadores": [r[0] for r in rows],
                "promedios": [round(r[1] or 0, 1) for r in rows]
            }
        }


@router.post("/charts/avg-reception-service-days")
async def chart_avg_reception_service(filters: FilterRequest):
    """Días promedio recepción servicio por usuario"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT entrega_servicio_usuario, AVG(COALESCE(dias_recepcion_servicio, 0)) as promedio
            FROM traza_req_oc
            WHERE entrega_servicio_usuario IS NOT NULL AND dias_recepcion_servicio IS NOT NULL
            GROUP BY entrega_servicio_usuario ORDER BY promedio DESC LIMIT 10
        ''')
        rows = cursor.fetchall()
        
        return {
            "success": True,
            "data": {
                "usuarios": [r[0] for r in rows],
                "promedios": [round(r[1] or 0, 1) for r in rows]
            }
        }


@router.post("/charts/avg-warehouse-entry-days")
async def chart_avg_warehouse_entry(filters: FilterRequest):
    """Días promedio entrada almacén por usuario"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT entrega_almacen_usuario, AVG(COALESCE(dias_entrada_almacen, 0)) as promedio
            FROM traza_req_oc
            WHERE entrega_almacen_usuario IS NOT NULL AND dias_entrada_almacen IS NOT NULL
            GROUP BY entrega_almacen_usuario ORDER BY promedio DESC LIMIT 10
        ''')
        rows = cursor.fetchall()
        
        return {
            "success": True,
            "data": {
                "usuarios": [r[0] for r in rows],
                "promedios": [round(r[1] or 0, 1) for r in rows]
            }
        }


@router.post("/charts/pending-approve-rq")
async def chart_pending_rq(filters: FilterRequest):
    """Pendientes por aprobar RQ por aprobador"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT req_usuario_autorizador, COUNT(*) as cantidad
            FROM traza_req_oc
            WHERE (req_estado = 'PENDIENTE' OR req_estado LIKE '%PEND%') 
            AND req_usuario_autorizador IS NOT NULL
            GROUP BY req_usuario_autorizador ORDER BY cantidad DESC LIMIT 10
        ''')
        rows = cursor.fetchall()
        
        return {
            "success": True,
            "data": {
                "aprobadores": [r[0] for r in rows],
                "cantidades": [r[1] for r in rows]
            }
        }


@router.post("/charts/pending-approve-oc")
async def chart_pending_oc(filters: FilterRequest):
    """Pendientes por aprobar OC por aprobador"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT oc_usuario_autorizacion, COUNT(*) as cantidad
            FROM traza_req_oc
            WHERE (oc_estado = 'PENDIENTE' OR oc_estado LIKE '%PEND%') 
            AND oc_usuario_autorizacion IS NOT NULL
            GROUP BY oc_usuario_autorizacion ORDER BY cantidad DESC LIMIT 10
        ''')
        rows = cursor.fetchall()
        
        return {
            "success": True,
            "data": {
                "aprobadores": [r[0] for r in rows],
                "cantidades": [r[1] for r in rows]
            }
        }


@router.post("/charts/oc-by-state")
async def chart_oc_by_state(filters: FilterRequest):
    """OC por estado"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT oc_estado, COUNT(*) FROM traza_req_oc
            WHERE oc_estado IS NOT NULL
            GROUP BY oc_estado ORDER BY COUNT(*) DESC
        ''')
        rows = cursor.fetchall()
        
        return {
            "success": True,
            "data": {
                "states": [r[0] for r in rows],
                "counts": [r[1] for r in rows]
            }
        }


@router.post("/charts/trend-oc")
async def chart_trend_oc(filters: FilterRequest):
    """Tendencia OC por mes"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT strftime('%Y-%m', oc_fecha) as mes, COUNT(DISTINCT oc_numero)
            FROM traza_req_oc
            WHERE oc_fecha IS NOT NULL
            GROUP BY mes ORDER BY mes DESC LIMIT 12
        ''')
        rows = cursor.fetchall()
        
        return {
            "success": True,
            "data": {
                "months": [r[0] for r in reversed(rows)],
                "counts": [r[1] for r in reversed(rows)]
            }
        }


@router.post("/charts/discounts-by-process")
async def chart_discounts_by_process(filters: FilterRequest):
    """Descuentos por proceso"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT proceso, SUM(COALESCE(total_dcto, 0))
            FROM oc_descuentos
            WHERE proceso IS NOT NULL
            GROUP BY proceso ORDER BY SUM(total_dcto) DESC LIMIT 10
        ''')
        rows = cursor.fetchall()
        
        return {
            "success": True,
            "data": {
                "processes": [r[0] for r in rows],
                "discounts": [r[1] or 0 for r in rows]
            }
        }


@router.post("/charts/top-suppliers")
async def chart_top_suppliers(filters: FilterRequest):
    """Top proveedores por monto"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT tercero_nombre, SUM(COALESCE(total, 0))
            FROM oc_descuentos
            WHERE tercero_nombre IS NOT NULL
            GROUP BY tercero_nombre ORDER BY SUM(total) DESC LIMIT 10
        ''')
        rows = cursor.fetchall()
        
        return {
            "success": True,
            "data": {
                "suppliers": [r[0] for r in rows],
                "amounts": [r[1] or 0 for r in rows]
            }
        }


@router.post("/charts/days-by-stage")
async def chart_days_by_stage(filters: FilterRequest):
    """Días promedio por etapa"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 
                AVG(COALESCE(dias_aprobar_rq, 0)),
                AVG(COALESCE(dias_generar_oc, 0)),
                AVG(COALESCE(dias_aprobacion_oc, 0)),
                AVG(COALESCE(dias_recepcion_servicio, 0)),
                AVG(COALESCE(dias_entrada_almacen, 0))
            FROM traza_req_oc
        ''')
        row = cursor.fetchone()
        
        return {
            "success": True,
            "data": {
                "stages": ["Aprobar RQ", "Generar OC", "Aprobación OC", "Recepción Servicio", "Entrada Almacén"],
                "days": [round(row[i] or 0, 1) for i in range(5)]
            }
        }


@router.post("/charts/spend-by-process")
async def chart_spend_by_process(filters: FilterRequest):
    """Gasto por proceso"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT proceso, SUM(COALESCE(total, 0))
            FROM oc_descuentos
            WHERE proceso IS NOT NULL
            GROUP BY proceso ORDER BY SUM(total) DESC LIMIT 10
        ''')
        rows = cursor.fetchall()
        
        return {
            "success": True,
            "data": {
                "processes": [r[0] for r in rows],
                "amounts": [r[1] or 0 for r in rows]
            }
        }
