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
        
        cursor.execute("SELECT DISTINCT tercero_nombre FROM dashboard_oc_descuentos WHERE tercero_nombre IS NOT NULL ORDER BY tercero_nombre LIMIT 500")
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
@router.get("/descuentos/kpis")
async def get_descuentos_kpis(
    dateStart: Optional[str] = None,
    dateEnd: Optional[str] = None,
    suppliers: Optional[str] = None,
    states: Optional[str] = None,
    processes: Optional[str] = None
):
    """KPIs principales para la pestaña DESCUENTOS"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Construir filtros WHERE
        where_clauses = []
        params = []
        
        if dateStart and dateEnd:
            where_clauses.append(f"fecha BETWEEN {_ph()} AND {_ph()}")
            params.extend([dateStart, dateEnd])
        
        if suppliers:
            supplier_list = suppliers.split(',')
            placeholders = ','.join([_ph()] * len(supplier_list))
            where_clauses.append(f"tercero_nombre IN ({placeholders})")
            params.extend(supplier_list)
        
        if states:
            state_list = states.split(',')
            placeholders = ','.join([_ph()] * len(state_list))
            where_clauses.append(f"estado IN ({placeholders})")
            params.extend(state_list)
        
        if processes:
            process_list = processes.split(',')
            placeholders = ','.join([_ph()] * len(process_list))
            where_clauses.append(f"proceso IN ({placeholders})")
            params.extend(process_list)
        
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


@router.get("/descuentos/graficas")
async def get_descuentos_graficas(
    dateStart: Optional[str] = None,
    dateEnd: Optional[str] = None,
    suppliers: Optional[str] = None,
    states: Optional[str] = None,
    processes: Optional[str] = None
):
    """Gráficas para la pestaña DESCUENTOS"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Construir filtros WHERE
        where_clauses = []
        params = []
        
        if dateStart and dateEnd:
            where_clauses.append(f"fecha BETWEEN {_ph()} AND {_ph()}")
            params.extend([dateStart, dateEnd])
        
        if suppliers:
            supplier_list = suppliers.split(',')
            placeholders = ','.join([_ph()] * len(supplier_list))
            where_clauses.append(f"tercero_nombre IN ({placeholders})")
            params.extend(supplier_list)
        
        if states:
            state_list = states.split(',')
            placeholders = ','.join([_ph()] * len(state_list))
            where_clauses.append(f"estado IN ({placeholders})")
            params.extend(state_list)
        
        if processes:
            process_list = processes.split(',')
            placeholders = ','.join([_ph()] * len(process_list))
            where_clauses.append(f"proceso IN ({placeholders})")
            params.extend(process_list)
        
        where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        
        # Gráfica 1: Top 10 Proveedores por Descuento
        _exec(cursor, f"""
            SELECT tercero_nombre, SUM(total_dcto) as total_descuento
            FROM dashboard_oc_descuentos
            {where_sql} AND total_dcto > 0
            GROUP BY tercero_nombre
            ORDER BY total_descuento DESC
            LIMIT 10
        """, params)
        top_proveedores = [{"proveedor": row[0], "descuento": round(row[1], 2)} for row in cursor.fetchall()]
        
        # Gráfica 2: Descuentos por Mes
        _exec(cursor, f"""
            SELECT strftime('%Y-%m', fecha) as mes, SUM(total_dcto) as total_descuento
            FROM dashboard_oc_descuentos
            {where_sql} AND fecha IS NOT NULL
            GROUP BY mes
            ORDER BY mes
        """, params)
        descuentos_mes = [{"mes": row[0], "descuento": round(row[1], 2)} for row in cursor.fetchall()]
        
        # Gráfica 3: Distribución de Descuentos por Rango de %
        _exec(cursor, f"""
            SELECT 
                CASE 
                    WHEN porcentaje_descuento = 0 THEN 'Sin descuento'
                    WHEN porcentaje_descuento > 0 AND porcentaje_descuento <= 5 THEN '0-5%'
                    WHEN porcentaje_descuento > 5 AND porcentaje_descuento <= 10 THEN '5-10%'
                    WHEN porcentaje_descuento > 10 AND porcentaje_descuento <= 15 THEN '10-15%'
                    WHEN porcentaje_descuento > 15 THEN '>15%'
                END as rango,
                COUNT(*) as cantidad
            FROM dashboard_oc_descuentos
            {where_sql}
            GROUP BY rango
            ORDER BY rango
        """, params)
        distribucion_descuentos = [{"rango": row[0], "cantidad": row[1]} for row in cursor.fetchall()]
        
        return {
            "top_proveedores": top_proveedores,
            "descuentos_por_mes": descuentos_mes,
            "distribucion_descuentos": distribucion_descuentos
        }


# ==================== TAB 2: TRAZA RQ OC ====================
@router.get("/traza/kpis")
async def get_traza_kpis(
    dateStart: Optional[str] = None,
    dateEnd: Optional[str] = None,
    suppliers: Optional[str] = None,
    req_states: Optional[str] = None,
    oc_states: Optional[str] = None
):
    """KPIs principales para la pestaña TRAZA RQ OC"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Construir filtros WHERE
        where_clauses = []
        params = []
        
        if dateStart and dateEnd:
            where_clauses.append(f"req_fecha BETWEEN {_ph()} AND {_ph()}")
            params.extend([dateStart, dateEnd])
        
        if suppliers:
            supplier_list = suppliers.split(',')
            placeholders = ','.join([_ph()] * len(supplier_list))
            where_clauses.append(f"oc_tercero_nombre IN ({placeholders})")
            params.extend(supplier_list)
        
        if req_states:
            state_list = req_states.split(',')
            placeholders = ','.join([_ph()] * len(state_list))
            where_clauses.append(f"req_estado IN ({placeholders})")
            params.extend(state_list)
        
        if oc_states:
            state_list = oc_states.split(',')
            placeholders = ','.join([_ph()] * len(state_list))
            where_clauses.append(f"oc_estado IN ({placeholders})")
            params.extend(state_list)
        
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


@router.get("/traza/graficas")
async def get_traza_graficas(
    dateStart: Optional[str] = None,
    dateEnd: Optional[str] = None,
    suppliers: Optional[str] = None,
    req_states: Optional[str] = None,
    oc_states: Optional[str] = None
):
    """Gráficas para la pestaña TRAZA RQ OC"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Construir filtros WHERE
        where_clauses = []
        params = []
        
        if dateStart and dateEnd:
            where_clauses.append(f"req_fecha BETWEEN {_ph()} AND {_ph()}")
            params.extend([dateStart, dateEnd])
        
        if suppliers:
            supplier_list = suppliers.split(',')
            placeholders = ','.join([_ph()] * len(supplier_list))
            where_clauses.append(f"oc_tercero_nombre IN ({placeholders})")
            params.extend(supplier_list)
        
        if req_states:
            state_list = req_states.split(',')
            placeholders = ','.join([_ph()] * len(state_list))
            where_clauses.append(f"req_estado IN ({placeholders})")
            params.extend(state_list)
        
        if oc_states:
            state_list = oc_states.split(',')
            placeholders = ','.join([_ph()] * len(state_list))
            where_clauses.append(f"oc_estado IN ({placeholders})")
            params.extend(state_list)
        
        where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        
        # Gráfica 1: Tiempos Promedio por Etapa
        _exec(cursor, f"""
            SELECT 
                COALESCE(AVG(dias_aprobar_rq), 0) as aprobar_rq,
                COALESCE(AVG(dias_generar_oc), 0) as generar_oc,
                COALESCE(AVG(dias_aprobacion_oc), 0) as aprobar_oc,
                COALESCE(AVG(dias_recepcion_servicio), 0) as recepcion_servicio,
                COALESCE(AVG(dias_entrada_almacen), 0) as entrada_almacen
            FROM dashboard_traza_req_oc
            {where_sql}
        """, params)
        row = cursor.fetchone()
        tiempos_etapas = {
            "etapas": ["Aprobar RQ", "Generar OC", "Aprobar OC", "Recepción Servicio", "Entrada Almacén"],
            "dias": [round(row[0], 1), round(row[1], 1), round(row[2], 1), round(row[3], 1), round(row[4], 1)]
        }
        
        # Gráfica 2: Requisiciones por Estado
        _exec(cursor, f"""
            SELECT req_estado, COUNT(*) as cantidad
            FROM dashboard_traza_req_oc
            {where_sql}
            GROUP BY req_estado
            ORDER BY cantidad DESC
        """, params)
        requisiciones_estado = [{"estado": row[0], "cantidad": row[1]} for row in cursor.fetchall()]
        
        # Gráfica 3: OC por Estado
        _exec(cursor, f"""
            SELECT oc_estado, COUNT(DISTINCT oc_numero) as cantidad
            FROM dashboard_traza_req_oc
            {where_sql} AND oc_numero IS NOT NULL
            GROUP BY oc_estado
            ORDER BY cantidad DESC
        """, params)
        oc_estado = [{"estado": row[0], "cantidad": row[1]} for row in cursor.fetchall()]
        
        return {
            "tiempos_por_etapa": tiempos_etapas,
            "requisiciones_por_estado": requisiciones_estado,
            "oc_por_estado": oc_estado
        }


# ==================== TAB 3: COMPRAS (resumen general) ====================
@router.get("/compras/kpis")
async def get_compras_kpis(
    dateStart: Optional[str] = None,
    dateEnd: Optional[str] = None,
    suppliers: Optional[str] = None
):
    """KPIs principales para la pestaña COMPRAS"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Construir filtros WHERE
        where_clauses = []
        params = []
        
        if dateStart and dateEnd:
            where_clauses.append(f"fecha BETWEEN {_ph()} AND {_ph()}")
            params.extend([dateStart, dateEnd])
        
        if suppliers:
            supplier_list = suppliers.split(',')
            placeholders = ','.join([_ph()] * len(supplier_list))
            where_clauses.append(f"tercero_nombre IN ({placeholders})")
            params.extend(supplier_list)
        
        where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        
        # KPI 1: Total Facturado
        _exec(cursor, f"""
            SELECT COALESCE(SUM(total), 0) as total_facturado
            FROM dashboard_oc_descuentos
            {where_sql}
        """, params)
        total_facturado = cursor.fetchone()[0]
        
        # KPI 2: Total de Órdenes
        _exec(cursor, f"""
            SELECT COUNT(DISTINCT CONCAT(documento_emp, '-', documento_suc, '-', documento_tipo, '-', documento_num)) as total_ordenes
            FROM dashboard_oc_descuentos
            {where_sql}
        """, params)
        total_ordenes = cursor.fetchone()[0]
        
        # KPI 3: Promedio por Orden
        promedio_orden = total_facturado / total_ordenes if total_ordenes > 0 else 0
        
        # KPI 4: Total de Proveedores Activos
        _exec(cursor, f"""
            SELECT COUNT(DISTINCT tercero_nombre) as total_proveedores
            FROM dashboard_oc_descuentos
            {where_sql}
        """, params)
        total_proveedores = cursor.fetchone()[0]
        
        return {
            "total_facturado": round(total_facturado, 2),
            "total_ordenes": total_ordenes,
            "promedio_por_orden": round(promedio_orden, 2),
            "total_proveedores": total_proveedores
        }


@router.get("/compras/graficas")
async def get_compras_graficas(
    dateStart: Optional[str] = None,
    dateEnd: Optional[str] = None,
    suppliers: Optional[str] = None
):
    """Gráficas para la pestaña COMPRAS"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Construir filtros WHERE
        where_clauses = []
        params = []
        
        if dateStart and dateEnd:
            where_clauses.append(f"fecha BETWEEN {_ph()} AND {_ph()}")
            params.extend([dateStart, dateEnd])
        
        if suppliers:
            supplier_list = suppliers.split(',')
            placeholders = ','.join([_ph()] * len(supplier_list))
            where_clauses.append(f"tercero_nombre IN ({placeholders})")
            params.extend(supplier_list)
        
        where_sql = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        
        # Gráfica 1: Top 10 Proveedores por Monto
        _exec(cursor, f"""
            SELECT tercero_nombre, SUM(total) as total_compras
            FROM dashboard_oc_descuentos
            {where_sql}
            GROUP BY tercero_nombre
            ORDER BY total_compras DESC
            LIMIT 10
        """, params)
        top_proveedores = [{"proveedor": row[0], "monto": round(row[1], 2)} for row in cursor.fetchall()]
        
        # Gráfica 2: Compras por Mes
        _exec(cursor, f"""
            SELECT strftime('%Y-%m', fecha) as mes, SUM(total) as total_compras
            FROM dashboard_oc_descuentos
            {where_sql} AND fecha IS NOT NULL
            GROUP BY mes
            ORDER BY mes
        """, params)
        compras_mes = [{"mes": row[0], "monto": round(row[1], 2)} for row in cursor.fetchall()]
        
        # Gráfica 3: Compras por Proceso
        _exec(cursor, f"""
            SELECT proceso, SUM(total) as total_compras
            FROM dashboard_oc_descuentos
            {where_sql} AND proceso IS NOT NULL
            GROUP BY proceso
            ORDER BY total_compras DESC
        """, params)
        compras_proceso = [{"proceso": row[0], "monto": round(row[1], 2)} for row in cursor.fetchall()]
        
        return {
            "top_proveedores": top_proveedores,
            "compras_por_mes": compras_mes,
            "compras_por_proceso": compras_proceso
        }
