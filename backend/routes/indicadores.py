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

def build_where_clause(fecha_inicio: Optional[str] = None, fecha_fin: Optional[str] = None, sedes: Optional[str] = None, responsables: Optional[str] = None, estados: Optional[str] = None, anios: Optional[str] = None, meses: Optional[str] = None):
    """Construir cláusula WHERE y parámetros"""
    where_clause = "WHERE 1=1"
    params = []
    
    if anios:
        anio_list = [int(a) for a in anios.split(",")]
        placeholders = ",".join(["?" for _ in anio_list])
        where_clause += f" AND anio IN ({placeholders})"
        params.extend(anio_list)
    
    if meses:
        mes_list = meses.split(",")
        placeholders = ",".join(["?" for _ in mes_list])
        where_clause += f" AND mes IN ({placeholders})"
        params.extend(mes_list)
    
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
    
    if estados:
        estado_list = estados.split(",")
        placeholders = ",".join(["?" for _ in estado_list])
        where_clause += f" AND estado IN ({placeholders})"
        params.extend(estado_list)
    
    return where_clause, params


@router.get("/datos")
async def get_datos(
    fecha_inicio: Optional[str] = None,
    fecha_fin: Optional[str] = None,
    sedes: Optional[str] = None,
    responsables: Optional[str] = None,
    estados: Optional[str] = None,
    anios: Optional[str] = None,
    meses: Optional[str] = None,
    limit: int = Query(default=50000, le=150000)
):
    """Obtener datos de indicadores con filtros"""
    with get_db() as conn:
        cursor = conn.cursor()
        where_clause, params = build_where_clause(fecha_inicio, fecha_fin, sedes, responsables, estados, anios, meses)
        query = f"SELECT * FROM indicadores {where_clause} ORDER BY anio DESC, mes, sede LIMIT {limit}"
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return {"data": [dict(row) for row in rows], "total": len(rows)}


@router.get("/filtros")
async def get_filtros():
    """Obtener opciones disponibles para filtros"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Obtener años únicos
        cursor.execute("SELECT DISTINCT anio FROM indicadores WHERE anio IS NOT NULL ORDER BY anio DESC")
        anios = [row[0] for row in cursor.fetchall()]
        
        # Obtener meses únicos
        cursor.execute("SELECT DISTINCT mes FROM indicadores WHERE mes IS NOT NULL ORDER BY CASE mes WHEN 'ENERO' THEN 1 WHEN 'FEBRERO' THEN 2 WHEN 'MARZO' THEN 3 WHEN 'ABRIL' THEN 4 WHEN 'MAYO' THEN 5 WHEN 'JUNIO' THEN 6 WHEN 'JULIO' THEN 7 WHEN 'AGOSTO' THEN 8 WHEN 'SEPTIEMBRE' THEN 9 WHEN 'OCTUBRE' THEN 10 WHEN 'NOVIEMBRE' THEN 11 WHEN 'DICIEMBRE' THEN 12 END")
        meses = [row[0] for row in cursor.fetchall()]
        
        # Obtener sedes únicas
        cursor.execute("SELECT DISTINCT sede FROM indicadores WHERE sede IS NOT NULL ORDER BY sede")
        sedes = [row[0] for row in cursor.fetchall()]
        
        # Obtener responsables únicos
        cursor.execute("SELECT DISTINCT responsable FROM indicadores WHERE responsable IS NOT NULL ORDER BY responsable")
        responsables = [row[0] for row in cursor.fetchall()]
        
        # Obtener estados únicos
        cursor.execute("SELECT DISTINCT estado FROM indicadores WHERE estado IS NOT NULL ORDER BY estado")
        estados = [row[0] for row in cursor.fetchall()]
        
        return {
            "anios": anios,
            "meses": meses,
            "sedes": sedes,
            "responsables": responsables,
            "estados": estados
        }


@router.get("/kpis")
async def get_kpis(
    fecha_inicio: Optional[str] = None,
    fecha_fin: Optional[str] = None,
    sedes: Optional[str] = None,
    responsables: Optional[str] = None,
    estados: Optional[str] = None,
    anios: Optional[str] = None,
    meses: Optional[str] = None
):
    """Obtener KPIs de indicadores"""
    with get_db() as conn:
        cursor = conn.cursor()
        where_clause, params = build_where_clause(fecha_inicio, fecha_fin, sedes, responsables, estados, anios, meses)
        
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
    responsables: Optional[str] = None,
    estados: Optional[str] = None,
    anios: Optional[str] = None,
    meses: Optional[str] = None
):
    """Datos para gráfico de inventario por sede"""
    with get_db() as conn:
        cursor = conn.cursor()
        where_clause, params = build_where_clause(fecha_inicio, fecha_fin, sedes, responsables, estados, anios, meses)
        
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

@router.get("/materiales")
async def get_materiales(
    sedes: Optional[str] = None,
    responsables: Optional[str] = None,
    estados: Optional[str] = None,
    anios: Optional[str] = None,
    meses: Optional[str] = None,
    limit: int = Query(default=10000, le=50000)
):
    """Obtener detalle de materiales según filtros"""
    with get_db() as conn:
        cursor = conn.cursor()
        where_clause, params = build_where_clause(None, None, sedes, responsables, estados, anios, meses)
        
        query = f"""
            SELECT 
                codigo,
                descripcion,
                SUM(inventario_final) as cantidad,
                SUM(costo_inventario_final) as valor_total,
                sede
            FROM indicadores 
            {where_clause}
            GROUP BY codigo, descripcion, sede
            ORDER BY valor_total DESC
            LIMIT {limit}
        """
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        return [{
            "codigo": row[0] or "N/A",
            "descripcion": row[1] or "N/A",
            "cantidad": round(row[2] or 0, 2),
            "valor_total": round(row[3] or 0, 2),
            "sede": row[4] or "N/A"
        } for row in rows]