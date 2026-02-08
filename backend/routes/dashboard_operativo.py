"""
Rutas API para Dashboard Operativo
- DESCUENTOS: Análisis de descuentos en órdenes de compra
- TRAZA RQ OC: Trazabilidad de requisiciones a órdenes de compra
- COMPRAS: Análisis general de compras

IMPORTANTE: Este dashboard usa tablas separadas de compras.html:
- dashboard_oc_descuentos (consolidada de carpetas DATA BI)
- dashboard_traza_req_oc (consolidada de carpetas DATA BI)

compras.html usa: oc_descuentos, traza_req_oc, base_oc_generadas
"""
from fastapi import APIRouter, Query
from typing import Optional, Dict, Any
from pydantic import BaseModel
from ..database import get_db, execute_sql
from ..config import DB_TYPE
from collections import defaultdict

router = APIRouter(prefix="/api/dashboard-operativo", tags=["Dashboard Operativo"])


def _ph():
    """Retorna el placeholder correcto según el tipo de BD"""
    return "%s" if DB_TYPE == "postgresql" else "?"


def _exec(cursor, sql, params=None):
    """Ejecuta SQL adaptando placeholders ? -> %s para PostgreSQL"""
    return execute_sql(cursor, sql, params)


# Modelo para filtros POST
class FilterRequest(BaseModel):
    dateStart: Optional[str] = None
    dateEnd: Optional[str] = None
    suppliers: Optional[list] = None
    states: Optional[list] = None
    processes: Optional[list] = None
    req_states: Optional[list] = None  # Para traza RQ
    oc_states: Optional[list] = None   # Para traza OC


# ==================== VERIFICACIÓN DE DATOS ====================
@router.get("/load")
async def load_data():
    """Verificar datos cargados en las tablas del dashboard operativo"""
    with get_db() as conn:
        cursor = conn.cursor()
        counts = {}
        for table in ["dashboard_oc_descuentos", "dashboard_traza_req_oc"]:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                counts[table] = cursor.fetchone()[0]
            except:
                counts[table] = 0
        return {"success": True, "counts": counts}


# ==================== FILTROS GLOBALES ====================
@router.get("/filters")
async def get_filters():
    """Obtener todas las opciones de filtros para el dashboard"""
    with get_db() as conn:
        cursor = conn.cursor()
        filters = {}
        
        # Filtros de OC_DESCUENTOS
        cursor.execute("SELECT DISTINCT estado FROM dashboard_oc_descuentos WHERE estado IS NOT NULL ORDER BY estado")
        filters["estados_oc_desc"] = [row[0] for row in cursor.fetchall()]
        
        cursor.execute("SELECT DISTINCT proceso FROM dashboard_oc_descuentos WHERE proceso IS NOT NULL ORDER BY proceso")
        filters["procesos"] = [row[0] for row in cursor.fetchall()]
        
        cursor.execute("SELECT DISTINCT tercero_nombre FROM dashboard_oc_descuentos WHERE tercero_nombre IS NOT NULL ORDER BY tercero_nombre")
        filters["proveedores_desc"] = [row[0] for row in cursor.fetchall()]
        
        cursor.execute("SELECT MAX(fecha), MIN(fecha) FROM dashboard_oc_descuentos WHERE fecha IS NOT NULL")
        row = cursor.fetchone()
        filters["fecha_max_desc"] = row[0]
        filters["fecha_min_desc"] = row[1]
        
        # Filtros de TRAZA_REQ_OC
        cursor.execute("SELECT DISTINCT req_estado FROM dashboard_traza_req_oc WHERE req_estado IS NOT NULL ORDER BY req_estado")
        filters["estados_req"] = [row[0] for row in cursor.fetchall()]
        
        cursor.execute("SELECT DISTINCT oc_estado FROM dashboard_traza_req_oc WHERE oc_estado IS NOT NULL ORDER BY oc_estado")
        filters["estados_oc"] = [row[0] for row in cursor.fetchall()]
        
        cursor.execute("SELECT DISTINCT oc_tercero_nombre FROM dashboard_traza_req_oc WHERE oc_tercero_nombre IS NOT NULL ORDER BY oc_tercero_nombre LIMIT 500")
        filters["proveedores_traza"] = [row[0] for row in cursor.fetchall()]
        
        cursor.execute("SELECT MAX(req_fecha), MIN(req_fecha) FROM dashboard_traza_req_oc WHERE req_fecha IS NOT NULL")
        row = cursor.fetchone()
        filters["fecha_max_traza"] = row[0]
        filters["fecha_min_traza"] = row[1]
        
        return filters


# ==================== TAB 1: DESCUENTOS ====================
@router.post("/descuentos/kpis")
async def get_descuentos_kpis(filters: FilterRequest):
    """KPIs principales para la pestaña DESCUENTOS (POST para evitar URL demasiado larga)"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Construir filtros WHERE
        where_clauses = []
        params = []
        
        if filters.dateStart and filters.dateEnd:
            where_clauses.append(f"fecha BETWEEN {_ph()} AND {_ph()}")
            params.extend([filters.dateStart, filters.dateEnd])
        
        if filters.suppliers:
            placeholders = ','.join([_ph()] * len(filters.suppliers))
            where_clauses.append(f"tercero_nombre IN ({placeholders})")
            params.extend(filters.suppliers)
        
        if filters.states:
            placeholders = ','.join([_ph()] * len(filters.states))
            where_clauses.append(f"estado IN ({placeholders})")
            params.extend(filters.states)
        
        if filters.processes:
            placeholders = ','.join([_ph()] * len(filters.processes))
            where_clauses.append(f"proceso IN ({placeholders})")
            params.extend(filters.processes)
        
        where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        
        # KPI 1: Total de Descuentos Otorgados
        _exec(cursor, f"""
            SELECT COALESCE(SUM(total_dcto), 0) as total_descuentos
            FROM dashboard_oc_descuentos
            {where_sql}
        """, params)
        total_descuentos = cursor.fetchone()[0]
        
        # KPI 2: Promedio de % Descuento
        _exec(cursor, f"""
            SELECT COALESCE(AVG(porcentaje_descuento), 0) as promedio_descuento
            FROM dashboard_oc_descuentos
            {where_sql}
        """, params)
        promedio_descuento = cursor.fetchone()[0]
        
        # KPI 3: Total de Órdenes con Descuento
        _exec(cursor, f"""
            SELECT COUNT(DISTINCT CONCAT(documento_emp, '-', documento_suc, '-', documento_tipo, '-', documento_num)) as total_ordenes
            FROM dashboard_oc_descuentos
            {where_sql} AND total_dcto > 0
        """, params)
        total_ordenes = cursor.fetchone()[0]
        
        # KPI 4: Total de Proveedores con Descuento
        _exec(cursor, f"""
            SELECT COUNT(DISTINCT tercero_nombre) as total_proveedores
            FROM dashboard_oc_descuentos
            {where_sql} AND total_dcto > 0
        """, params)
        total_proveedores = cursor.fetchone()[0]
        
        return {
            "total_descuentos": round(total_descuentos, 2),
            "promedio_descuento": round(promedio_descuento, 2),
            "total_ordenes": total_ordenes,
            "total_proveedores": total_proveedores
        }


@router.post("/descuentos/graficas")
async def get_descuentos_graficas(filters: FilterRequest):
    """Gráficas para la pestaña DESCUENTOS (POST para evitar URL demasiado larga)"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Construir filtros WHERE
        where_clauses = []
        params = []
        
        if filters.dateStart and filters.dateEnd:
            where_clauses.append(f"fecha BETWEEN {_ph()} AND {_ph()}")
            params.extend([filters.dateStart, filters.dateEnd])
        
        if filters.suppliers:
            placeholders = ','.join([_ph()] * len(filters.suppliers))
            where_clauses.append(f"tercero_nombre IN ({placeholders})")
            params.extend(filters.suppliers)
        
        if filters.states:
            placeholders = ','.join([_ph()] * len(filters.states))
            where_clauses.append(f"estado IN ({placeholders})")
            params.extend(filters.states)
        
        if filters.processes:
            placeholders = ','.join([_ph()] * len(filters.processes))
            where_clauses.append(f"proceso IN ({placeholders})")
            params.extend(filters.processes)
        
        where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        
        # Helper para agregar condiciones adicionales
        def add_where(base_where, condition):
            if base_where:
                return f"{base_where} AND {condition}"
            else:
                return f" WHERE {condition}"
        
        # Indicadores superiores
        # Total de items procesados
        _exec(cursor, f"""
            SELECT COUNT(*) as items_procesados
            FROM dashboard_oc_descuentos
            {where_sql}
        """, params)
        items_procesados = cursor.fetchone()[0]
        
        # Total de órdenes de compra
        _exec(cursor, f"""
            SELECT COUNT(DISTINCT CONCAT(documento_emp, '-', documento_suc, '-', documento_tipo, '-', documento_num)) as ordenes_compra
            FROM dashboard_oc_descuentos
            {where_sql}
        """, params)
        ordenes_compra = cursor.fetchone()[0]
        
        # Promedio de descuento
        _exec(cursor, f"""
            SELECT COALESCE(AVG(porcentaje_descuento), 0) as promedio_descuento
            FROM dashboard_oc_descuentos
            {where_sql}
        """, params)
        promedio_descuento = cursor.fetchone()[0]
        
        # Gráfica 1: Órdenes de Compra e Items Procesados por Proceso
        _exec(cursor, f"""
            SELECT 
                proceso,
                COUNT(DISTINCT CONCAT(documento_emp, '-', documento_suc, '-', documento_tipo, '-', documento_num)) as ordenes,
                COUNT(*) as items
            FROM dashboard_oc_descuentos
            {add_where(where_sql, "proceso IS NOT NULL")}
            GROUP BY proceso
            ORDER BY items DESC
        """, params)
        ordenes_items_proceso = [{"proceso": row[0], "ordenes": row[1], "items": row[2]} for row in cursor.fetchall()]
        
        # Gráfica 2: Promedio de % Descuento por Proceso
        _exec(cursor, f"""
            SELECT proceso, AVG(porcentaje_descuento) as promedio
            FROM dashboard_oc_descuentos
            {add_where(where_sql, "proceso IS NOT NULL")}
            GROUP BY proceso
            ORDER BY promedio DESC
        """, params)
        descuento_por_proceso = [{"proceso": row[0], "promedio": round(row[1], 2)} for row in cursor.fetchall()]
        
        # Gráfica 3: Promedio de % Descuento por Proveedor (TODOS con scroll)
        _exec(cursor, f"""
            SELECT tercero_nombre, AVG(porcentaje_descuento) as promedio
            FROM dashboard_oc_descuentos
            {add_where(where_sql, "tercero_nombre IS NOT NULL")}
            GROUP BY tercero_nombre
            ORDER BY promedio DESC
        """, params)
        descuento_por_proveedor = [{"proveedor": row[0], "promedio": round(row[1], 2)} for row in cursor.fetchall()]
        
        return {
            "indicadores": {
                "items_procesados": items_procesados,
                "ordenes_compra": ordenes_compra,
                "promedio_descuento": round(promedio_descuento, 2)
            },
            "ordenes_items_por_proceso": ordenes_items_proceso,
            "descuento_por_proceso": descuento_por_proceso,
            "descuento_por_proveedor": descuento_por_proveedor
        }


# ==================== TAB 2: TRAZA RQ OC ====================
@router.post("/traza/kpis")
async def get_traza_kpis(filters: FilterRequest):
    """KPIs principales para la pestaña TRAZA RQ OC (POST para evitar URL demasiado larga)"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Construir filtros WHERE
        where_clauses = []
        params = []
        
        if filters.dateStart and filters.dateEnd:
            where_clauses.append(f"req_fecha BETWEEN {_ph()} AND {_ph()}")
            params.extend([filters.dateStart, filters.dateEnd])
        
        if filters.suppliers:
            placeholders = ','.join([_ph()] * len(filters.suppliers))
            where_clauses.append(f"oc_tercero_nombre IN ({placeholders})")
            params.extend(filters.suppliers)
        
        if filters.req_states:
            placeholders = ','.join([_ph()] * len(filters.req_states))
            where_clauses.append(f"req_estado IN ({placeholders})")
            params.extend(filters.req_states)
        
        if filters.oc_states:
            placeholders = ','.join([_ph()] * len(filters.oc_states))
            where_clauses.append(f"oc_estado IN ({placeholders})")
            params.extend(filters.oc_states)
        
        where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        
        # KPI 1: Promedio de Días para Aprobar RQ
        _exec(cursor, f"""
            SELECT COALESCE(AVG(dias_aprobar_rq), 0) as promedio_dias_aprobar_rq
            FROM dashboard_traza_req_oc
            {where_sql} AND dias_aprobar_rq IS NOT NULL
        """, params)
        promedio_dias_aprobar_rq = cursor.fetchone()[0]
        
        # KPI 2: Promedio de Días para Generar OC
        _exec(cursor, f"""
            SELECT COALESCE(AVG(dias_generar_oc), 0) as promedio_dias_generar_oc
            FROM dashboard_traza_req_oc
            {where_sql} AND dias_generar_oc IS NOT NULL
        """, params)
        promedio_dias_generar_oc = cursor.fetchone()[0]
        
        # KPI 3: Total de Requisiciones
        _exec(cursor, f"""
            SELECT COUNT(DISTINCT req_numero) as total_requisiciones
            FROM dashboard_traza_req_oc
            {where_sql}
        """, params)
        total_requisiciones = cursor.fetchone()[0]
        
        # KPI 4: Total de Órdenes de Compra
        _exec(cursor, f"""
            SELECT COUNT(DISTINCT oc_numero) as total_oc
            FROM dashboard_traza_req_oc
            {where_sql} AND oc_numero IS NOT NULL
        """, params)
        total_oc = cursor.fetchone()[0]
        
        return {
            "promedio_dias_aprobar_rq": round(promedio_dias_aprobar_rq, 1),
            "promedio_dias_generar_oc": round(promedio_dias_generar_oc, 1),
            "total_requisiciones": total_requisiciones,
            "total_oc": total_oc
        }


@router.post("/traza/graficas")
async def get_traza_graficas(filters: FilterRequest):
    """Gráficas para la pestaña TRAZA RQ OC (POST para evitar URL demasiado larga)"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Construir filtros WHERE
        where_clauses = []
        params = []
        
        if filters.dateStart and filters.dateEnd:
            where_clauses.append(f"req_fecha BETWEEN {_ph()} AND {_ph()}")
            params.extend([filters.dateStart, filters.dateEnd])
        
        if filters.suppliers:
            placeholders = ','.join([_ph()] * len(filters.suppliers))
            where_clauses.append(f"oc_tercero_nombre IN ({placeholders})")
            params.extend(filters.suppliers)
        
        if filters.req_states:
            placeholders = ','.join([_ph()] * len(filters.req_states))
            where_clauses.append(f"req_estado IN ({placeholders})")
            params.extend(filters.req_states)
        
        if filters.oc_states:
            placeholders = ','.join([_ph()] * len(filters.oc_states))
            where_clauses.append(f"oc_estado IN ({placeholders})")
            params.extend(filters.oc_states)
        
        where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        
        # Helper para agregar condiciones adicionales
        def add_where(base_where, condition):
            if base_where:
                return base_where + " AND " + condition
            else:
                return " WHERE " + condition
        
        # Gráfica 1: Promedio Días Aprobación RQ por Usuario Autorizador (req_usuario_autorizador)
        _exec(cursor, f"""
            SELECT req_usuario_autorizador, COALESCE(AVG(dias_aprobar_rq), 0) as promedio
            FROM dashboard_traza_req_oc
            {add_where(where_sql, "req_usuario_autorizador IS NOT NULL AND dias_aprobar_rq IS NOT NULL")}
            GROUP BY req_usuario_autorizador
            ORDER BY promedio DESC
        """, params)
        dias_aprobar_rq_usuario = [{"usuario": row[0], "promedio": round(row[1], 1)} for row in cursor.fetchall()]
        
        # Gráfica 2: Promedio Días Generar OC por Orden Compra|Usuario (oc_usuario)
        _exec(cursor, f"""
            SELECT oc_usuario, COALESCE(AVG(dias_generar_oc), 0) as promedio
            FROM dashboard_traza_req_oc
            {add_where(where_sql, "oc_usuario IS NOT NULL AND dias_generar_oc IS NOT NULL")}
            GROUP BY oc_usuario
            ORDER BY promedio DESC
        """, params)
        dias_generar_oc_usuario = [{"usuario": row[0], "promedio": round(row[1], 1)} for row in cursor.fetchall()]
        
        # Gráfica 3: Días Aprobación OC por Usuario Autorizador (oc_usuario_autorizacion)
        _exec(cursor, f"""
            SELECT oc_usuario_autorizacion, COALESCE(AVG(dias_aprobacion_oc), 0) as promedio
            FROM dashboard_traza_req_oc
            {add_where(where_sql, "oc_usuario_autorizacion IS NOT NULL AND dias_aprobacion_oc IS NOT NULL")}
            GROUP BY oc_usuario_autorizacion
            ORDER BY promedio DESC
        """, params)
        dias_aprobacion_oc_autorizador = [{"usuario": row[0], "promedio": round(row[1], 1)} for row in cursor.fetchall()]
        
        # Gráfica 4: Promedio Días Entrada Almacén por Entrega de Almacen|Usuario
        _exec(cursor, f"""
            SELECT entrega_almacen_usuario, COALESCE(AVG(dias_entrada_almacen), 0) as promedio
            FROM dashboard_traza_req_oc
            {add_where(where_sql, "entrega_almacen_usuario IS NOT NULL AND dias_entrada_almacen IS NOT NULL")}
            GROUP BY entrega_almacen_usuario
            ORDER BY promedio DESC
        """, params)
        dias_entrada_almacen_usuario = [{"usuario": row[0], "promedio": round(row[1], 1)} for row in cursor.fetchall()]
        
        return {
            "dias_aprobar_rq_usuario": dias_aprobar_rq_usuario,
            "dias_generar_oc_usuario": dias_generar_oc_usuario,
            "dias_aprobacion_oc_autorizador": dias_aprobacion_oc_autorizador,
            "dias_entrada_almacen_usuario": dias_entrada_almacen_usuario
        }


# ==================== TAB 3: COMPRAS (resumen general) ====================
@router.post("/compras/graficas")
async def get_compras_graficas(filters: FilterRequest):
    """Gráficas para la pestaña COMPRAS (POST para evitar URL demasiado larga)
    
    Retorna datos para 4 gráficas del dashboard Power BI:
    1. Gauge GASTO MES (total general)
    2. PROVEEDORES (barras horizontales top proveedores por Suma de Total)
    3. Treemap de items/productos por valor
    4. Tabla resumen por Proceso con Suma de Total
    """
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Construir filtros WHERE (mismos filtros que DESCUENTOS)
        where_clauses = []
        params = []
        
        if filters.dateStart and filters.dateEnd:
            where_clauses.append(f"fecha BETWEEN {_ph()} AND {_ph()}")
            params.extend([filters.dateStart, filters.dateEnd])
        
        if filters.suppliers:
            placeholders = ','.join([_ph()] * len(filters.suppliers))
            where_clauses.append(f"tercero_nombre IN ({placeholders})")
            params.extend(filters.suppliers)
        
        if filters.states:
            placeholders = ','.join([_ph()] * len(filters.states))
            where_clauses.append(f"estado IN ({placeholders})")
            params.extend(filters.states)
        
        if filters.processes:
            placeholders = ','.join([_ph()] * len(filters.processes))
            where_clauses.append(f"proceso IN ({placeholders})")
            params.extend(filters.processes)
        
        where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        
        # Helper para agregar condiciones adicionales
        def add_where(base_where, condition):
            if base_where:
                return f"{base_where} AND {condition}"
            return f" WHERE {condition}"
        
        # 1. GASTO MES - Total general (para gauge)
        _exec(cursor, f"""
            SELECT COALESCE(SUM(total), 0) as gasto_total
            FROM dashboard_oc_descuentos
            {where_sql}
        """, params)
        gasto_total = cursor.fetchone()[0] or 0
        
        # 2. PROVEEDORES - Top proveedores por Suma de Total (barras horizontales)
        _exec(cursor, f"""
            SELECT tercero_nombre, COALESCE(SUM(total), 0) as total_compras
            FROM dashboard_oc_descuentos
            {add_where(where_sql, "tercero_nombre IS NOT NULL")}
            GROUP BY tercero_nombre
            ORDER BY total_compras DESC
        """, params)
        top_proveedores = [{"proveedor": row[0], "monto": round(row[1] or 0, 2)} for row in cursor.fetchall()]
        
        # 3. TREEMAP - Items/productos agrupados por descripción y valor total
        _exec(cursor, f"""
            SELECT item_descripcion, COALESCE(SUM(total), 0) as total_item_sum
            FROM dashboard_oc_descuentos
            {add_where(where_sql, "item_descripcion IS NOT NULL")}
            GROUP BY item_descripcion
            ORDER BY total_item_sum DESC
        """, params)
        treemap_items = [{"item": row[0], "valor": round(row[1] or 0, 2)} for row in cursor.fetchall()]
        
        # 4. TABLA PROCESO - Resumen por proceso con Suma de Total
        _exec(cursor, f"""
            SELECT proceso, COALESCE(SUM(total), 0) as total_compras
            FROM dashboard_oc_descuentos
            {add_where(where_sql, "proceso IS NOT NULL")}
            GROUP BY proceso
            ORDER BY total_compras DESC
        """, params)
        compras_proceso = [{"proceso": row[0], "monto": round(row[1] or 0, 2)} for row in cursor.fetchall()]
        
        return {
            "gasto_total": round(gasto_total, 2),
            "top_proveedores": top_proveedores,
            "treemap_items": treemap_items,
            "compras_por_proceso": compras_proceso
        }
