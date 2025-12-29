"""
Rutas API para Indicadores de Almacenes (OYMM)
"""
from fastapi import APIRouter, Query
from typing import Optional, List
from ..database import get_db

router = APIRouter(prefix="/api/indicadores", tags=["Indicadores"])

# Mapeo de meses en español a números
MESES_MAP = {
    'ENERO': 1, 'FEBRERO': 2, 'MARZO': 3, 'ABRIL': 4, 'MAYO': 5, 'JUNIO': 6,
    'JULIO': 7, 'AGOSTO': 8, 'SEPTIEMBRE': 9, 'OCTUBRE': 10, 'NOVIEMBRE': 11, 'DICIEMBRE': 12
}

def build_where_clause(fecha_inicio: Optional[str], fecha_fin: Optional[str], sedes: Optional[str], responsables: Optional[str]):
    """Construir cláusula WHERE y parámetros"""
    where_clause = "WHERE 1=1"
    params = []
    
    if fecha_inicio and fecha_fin:
        from datetime import datetime
        # Manejar formato YYYY-MM del input type="month"
        fecha_ini_obj = datetime.strptime(fecha_inicio, "%Y-%m")
        fecha_fin_obj = datetime.strptime(fecha_fin, "%Y-%m")
        mes_inicio = fecha_ini_obj.month
        mes_fin = fecha_fin_obj.month
        
        # Obtener meses válidos en el rango
        meses_validos = [k for k, v in MESES_MAP.items() if mes_inicio <= v <= mes_fin]
        if meses_validos:
            placeholders = ",".join(["?" for _ in meses_validos])
            where_clause += f" AND mes IN ({placeholders})"
            params.extend(meses_validos)
    elif fecha_inicio:
        from datetime import datetime
        fecha_obj = datetime.strptime(fecha_inicio, "%Y-%m")
        mes_inicio = fecha_obj.month
        meses_validos = [k for k, v in MESES_MAP.items() if v >= mes_inicio]
        if meses_validos:
            placeholders = ",".join(["?" for _ in meses_validos])
            where_clause += f" AND mes IN ({placeholders})"
            params.extend(meses_validos)
    elif fecha_fin:
        from datetime import datetime
        fecha_obj = datetime.strptime(fecha_fin, "%Y-%m")
        mes_fin = fecha_obj.month
        meses_validos = [k for k, v in MESES_MAP.items() if v <= mes_fin]
        if meses_validos:
            placeholders = ",".join(["?" for _ in meses_validos])
            where_clause += f" AND mes IN ({placeholders})"
            params.extend(meses_validos)
    
    if sedes:
        sede_list = sedes.split(",")
        placeholders = ",".join(["?" for _ in sede_list])
        where_clause += f" AND sede IN ({placeholders})"
        params.extend(sede_list)
    
    if responsables:
        responsable_list = responsables.split(",")
        placeholders = ",".join(["?" for _ in responsable_list])
        where_clause += f" AND responsable IN ({placeholders})"
        params.extend(responsable_list)
    
    return where_clause, params


@router.get("/datos")
async def get_datos(
    fecha_inicio: Optional[str] = None,
    fecha_fin: Optional[str] = None,
    sedes: Optional[str] = None,
    responsables: Optional[str] = None,
    limit: int = Query(default=50000, le=150000)
):
    """Obtener datos de indicadores con filtros"""
    with get_db() as conn:
        cursor = conn.cursor()
        where_clause, params = build_where_clause(fecha_inicio, fecha_fin, sedes, responsables)
        query = f"SELECT * FROM indicadores {where_clause} ORDER BY mes, sede LIMIT {limit}"
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return {"data": [dict(row) for row in rows], "total": len(rows)}


@router.get("/filtros")
async def get_filtros():
    """Obtener opciones disponibles para filtros"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Obtener sedes únicas
        cursor.execute("SELECT DISTINCT sede FROM indicadores WHERE sede IS NOT NULL ORDER BY sede")
        sedes = [row[0] for row in cursor.fetchall()]
        
        # Obtener responsables únicos
        cursor.execute("SELECT DISTINCT responsable FROM indicadores WHERE responsable IS NOT NULL ORDER BY responsable")
        responsables = [row[0] for row in cursor.fetchall()]
        
        return {
            "sedes": sedes,
            "responsables": responsables
        }


@router.get("/kpis")
async def get_kpis(
    fecha_inicio: Optional[str] = None,
    fecha_fin: Optional[str] = None,
    sedes: Optional[str] = None,
    responsables: Optional[str] = None
):
    """Obtener KPIs de indicadores"""
    with get_db() as conn:
        cursor = conn.cursor()
        where_clause, params = build_where_clause(fecha_inicio, fecha_fin, sedes, responsables)
        
        # Contar registros totales
        cursor.execute(f"SELECT COUNT(*) FROM indicadores {where_clause}", params)
        total_registros = cursor.fetchone()[0]
        
        # Calcular costo total inventario final
        cursor.execute(f"""
            SELECT SUM(costo_inventario_final), SUM(costo_diferencia), SUM(diferencia)
            FROM indicadores {where_clause}
        """, params)
        row = cursor.fetchone()
        costo_inventario_total = row[0] or 0
        costo_diferencia_total = row[1] or 0
        diferencia_total = row[2] or 0
        
        # Calcular desviación promedio
        cursor.execute(f"""
            SELECT AVG(ABS(diferencia * 100.0 / NULLIF(inventario_final, 0)))
            FROM indicadores {where_clause}
            AND inventario_final != 0
        """, params)
        desviacion_promedio = cursor.fetchone()[0] or 0
        
        # Contar códigos únicos
        cursor.execute(f"SELECT COUNT(DISTINCT codigo) FROM indicadores {where_clause}", params)
        codigos_unicos = cursor.fetchone()[0]
        
        return {
            "total_registros": total_registros,
            "costo_inventario_final": round(costo_inventario_total, 2),
            "costo_diferencia": round(costo_diferencia_total, 2),
            "diferencia_total": round(diferencia_total, 2),
            "desviacion_promedio": round(desviacion_promedio, 2),
            "codigos_unicos": codigos_unicos
        }


@router.get("/grafico/inventario-por-sede")
async def get_inventario_por_sede(
    fecha_inicio: Optional[str] = None,
    fecha_fin: Optional[str] = None,
    sedes: Optional[str] = None,
    responsables: Optional[str] = None
):
    """Datos para gráfico de inventario por sede"""
    with get_db() as conn:
        cursor = conn.cursor()
        where_clause, params = build_where_clause(fecha_inicio, fecha_fin, sedes, responsables)
        
        cursor.execute(f"""
            SELECT sede, 
                   SUM(costo_inventario_final) as costo_inventario,
                   SUM(costo_diferencia) as costo_diferencia,
                   AVG(ABS(diferencia * 100.0 / NULLIF(inventario_final, 0))) as desviacion_promedio
            FROM indicadores {where_clause}
            GROUP BY sede 
            ORDER BY costo_inventario DESC
        """, params)
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "sede": row[0],
                "costo_inventario": round(row[1] or 0, 2),
                "costo_diferencia": round(row[2] or 0, 2),
                "desviacion_promedio": round(row[3] or 0, 2)
            })
        return results


@router.get("/grafico/inventario-por-mes")
async def get_inventario_por_mes(
    meses: Optional[str] = None,
    sedes: Optional[str] = None,
    responsables: Optional[str] = None
):
    """Datos para gráfico de inventario por mes (con orden correcto de meses)"""
    with get_db() as conn:
        cursor = conn.cursor()
        where_clause, params = build_where_clause(meses, sedes, responsables)
        
        # Definir el orden de los meses
        orden_meses = {
            'ENERO': 1, 'FEBRERO': 2, 'MARZO': 3, 'ABRIL': 4, 'MAYO': 5, 'JUNIO': 6,
            'JULIO': 7, 'AGOSTO': 8, 'SEPTIEMBRE': 9, 'OCTUBRE': 10, 'NOVIEMBRE': 11, 'DICIEMBRE': 12
        }
        
        cursor.execute(f"""
            SELECT mes, 
                   SUM(costo_inventario_final) as costo_inventario,
                   SUM(costo_diferencia) as costo_diferencia,
                   AVG(ABS(diferencia * 100.0 / NULLIF(inventario_final, 0))) as desviacion_promedio
            FROM indicadores {where_clause}
            GROUP BY mes
        """, params)
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "mes": row[0],
                "costo_inventario": round(row[1] or 0, 2),
                "costo_diferencia": round(row[2] or 0, 2),
                "desviacion_promedio": round(row[3] or 0, 2),
                "orden": orden_meses.get(row[0], 99)
            })
        
        # Ordenar por el orden de los meses
        results.sort(key=lambda x: x["orden"])
        
        # Remover el campo de orden antes de devolver
        for r in results:
            del r["orden"]
        
        return results

