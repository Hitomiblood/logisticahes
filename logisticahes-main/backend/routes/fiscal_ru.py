"""
Rutas API para Inventario Fiscal RU
"""
from fastapi import APIRouter, Query
from typing import Optional
from ..database import get_db

router = APIRouter(prefix="/api/fiscal-ru", tags=["Fiscal RU"])

# Mapeo de meses en español a números
MESES_MAP = {
    'ENERO': 1, 'FEBRERO': 2, 'MARZO': 3, 'ABRIL': 4, 'MAYO': 5, 'JUNIO': 6,
    'JULIO': 7, 'AGOSTO': 8, 'SEPTIEMBRE': 9, 'OCTUBRE': 10, 'NOVIEMBRE': 11, 'DICIEMBRE': 12
}

def build_where_clause(fecha_inicio: Optional[str], fecha_fin: Optional[str], sedes: Optional[str], estado: Optional[str], tipo_inventario: Optional[str]):
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
    
    # Filtro de sedes
    if sedes:
        sedes_list = [s.strip() for s in sedes.split(',')]
        placeholders = ','.join('?' * len(sedes_list))
        where_clause += f" AND sede IN ({placeholders})"
        params.extend(sedes_list)
    
    if estado:
        estado_list = estado.split(",")
        placeholders = ",".join(["?" for _ in estado_list])
        where_clause += f" AND estado IN ({placeholders})"
        params.extend(estado_list)
    
    if tipo_inventario:
        tipo_list = tipo_inventario.split(",")
        placeholders = ",".join(["?" for _ in tipo_list])
        where_clause += f" AND tipo_inventario IN ({placeholders})"
        params.extend(tipo_list)
    
    return where_clause, params


@router.get("/filtros")
async def get_filtros():
    """Obtener opciones disponibles para filtros específicos"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Obtener estados únicos
        cursor.execute("SELECT DISTINCT estado FROM fiscal_ru WHERE estado IS NOT NULL ORDER BY estado")
        estados = [row[0] for row in cursor.fetchall()]
        
        # Obtener tipos de inventario únicos
        cursor.execute("SELECT DISTINCT tipo_inventario FROM fiscal_ru WHERE tipo_inventario IS NOT NULL ORDER BY tipo_inventario")
        tipos = [row[0] for row in cursor.fetchall()]
        
        return {
            "estados": estados,
            "tipos_inventario": tipos
        }


@router.get("/kpis")
async def get_kpis(
    fecha_inicio: Optional[str] = None,
    fecha_fin: Optional[str] = None,
    sedes: Optional[str] = None,
    estado: Optional[str] = None,
    tipo_inventario: Optional[str] = None
):
    """Obtener KPIs de Fiscal RU"""
    with get_db() as conn:
        cursor = conn.cursor()
        where_clause, params = build_where_clause(fecha_inicio, fecha_fin, sedes, estado, tipo_inventario)
        
        # Calcular KPIs
        cursor.execute(f"""
            SELECT 
                COUNT(*) as total_registros,
                SUM(costo_total) as costo_inventario,
                SUM(costo_diferencia) as total_diferencia,
                AVG(CASE WHEN saldo_final != 0 THEN ABS(diferencia * 100.0 / saldo_final) END) as desviacion_promedio,
                AVG(objetivo) as promedio_objetivo
            FROM fiscal_ru {where_clause}
        """, params)
        
        row = cursor.fetchone()
        
        return {
            "total_registros": row[0] or 0,
            "costo_inventario": round(row[1] or 0, 2),
            "total_diferencia": round(row[2] or 0, 2),
            "desviacion_promedio": round(row[3] or 0, 2),
            "promedio_objetivo": round((row[4] or 0) * 100, 2)
        }


@router.get("/grafico/por-sede")
async def get_por_sede(
    fecha_inicio: Optional[str] = None,
    fecha_fin: Optional[str] = None,
    sedes: Optional[str] = None,
    estado: Optional[str] = None,
    tipo_inventario: Optional[str] = None
):
    """Datos para gráfico por sede"""
    with get_db() as conn:
        cursor = conn.cursor()
        where_clause, params = build_where_clause(fecha_inicio, fecha_fin, sedes, estado, tipo_inventario)
        
        cursor.execute(f"""
            SELECT 
                sede,
                SUM(costo_total) as costo_inventario,
                SUM(costo_diferencia) as costo_diferencia,
                AVG(CASE WHEN saldo_final != 0 THEN ABS(diferencia * 100.0 / saldo_final) END) as desviacion,
                AVG(objetivo) as promedio_objetivo
            FROM fiscal_ru {where_clause}
            GROUP BY sede 
            ORDER BY costo_inventario DESC
        """, params)
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "sede": row[0],
                "costo_inventario": round(row[1] or 0, 2),
                "costo_diferencia": round(row[2] or 0, 2),
                "desviacion": round(row[3] or 0, 2),
                "promedio_objetivo": round((row[4] or 0) * 100, 2)
            })
        return results


@router.get("/grafico/por-estado")
async def get_por_estado(
    fecha_inicio: Optional[str] = None,
    fecha_fin: Optional[str] = None,
    sedes: Optional[str] = None,
    estado: Optional[str] = None,
    tipo_inventario: Optional[str] = None
):
    """Datos para gráfico por estado"""
    with get_db() as conn:
        cursor = conn.cursor()
        where_clause, params = build_where_clause(fecha_inicio, fecha_fin, sedes, estado, tipo_inventario)
        
        cursor.execute(f"""
            SELECT 
                estado,
                COUNT(*) as cantidad,
                SUM(costo_total) as costo_inventario,
                SUM(costo_diferencia) as costo_diferencia
            FROM fiscal_ru {where_clause}
            GROUP BY estado 
            ORDER BY costo_inventario DESC
        """, params)
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "estado": row[0],
                "cantidad": row[1] or 0,
                "costo_inventario": round(row[2] or 0, 2),
                "costo_diferencia": round(row[3] or 0, 2)
            })
        return results
