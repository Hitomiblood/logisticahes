"""
Rutas para el módulo de Gestión Proceso
"""
from fastapi import APIRouter, Query
from typing import Optional
from ..database import get_db
from datetime import datetime

router = APIRouter(prefix="/api/gestion", tags=["gestion"])

# Mapeo de nombres de mes en español a números
MESES_MAP = {
    "ENERO": 1, "FEBRERO": 2, "MARZO": 3, "ABRIL": 4,
    "MAYO": 5, "JUNIO": 6, "JULIO": 7, "AGOSTO": 8,
    "SEPTIEMBRE": 9, "OCTUBRE": 10, "NOVIEMBRE": 11, "DICIEMBRE": 12
}

def build_where_clause(
    fecha_inicio: Optional[str] = None,
    fecha_fin: Optional[str] = None,
    sedes: Optional[str] = None,
    tipos_inventario: Optional[str] = None,
    responsables: Optional[str] = None
):
    """Construir cláusula WHERE con filtros opcionales"""
    conditions = []
    params = []
    
    # Filtro por rango de fechas (usando mes)
    if fecha_inicio:
        try:
            fecha = datetime.strptime(fecha_inicio, '%Y-%m-%d')
            mes_inicio = fecha.month
            conditions.append("CAST(substr('0' || CASE mes WHEN 'ENERO' THEN 1 WHEN 'FEBRERO' THEN 2 WHEN 'MARZO' THEN 3 WHEN 'ABRIL' THEN 4 WHEN 'MAYO' THEN 5 WHEN 'JUNIO' THEN 6 WHEN 'JULIO' THEN 7 WHEN 'AGOSTO' THEN 8 WHEN 'SEPTIEMBRE' THEN 9 WHEN 'OCTUBRE' THEN 10 WHEN 'NOVIEMBRE' THEN 11 WHEN 'DICIEMBRE' THEN 12 END, -2, 2) AS INTEGER) >= ?")
            params.append(mes_inicio)
        except:
            pass
    
    if fecha_fin:
        try:
            fecha = datetime.strptime(fecha_fin, '%Y-%m-%d')
            mes_fin = fecha.month
            conditions.append("CAST(substr('0' || CASE mes WHEN 'ENERO' THEN 1 WHEN 'FEBRERO' THEN 2 WHEN 'MARZO' THEN 3 WHEN 'ABRIL' THEN 4 WHEN 'MAYO' THEN 5 WHEN 'JUNIO' THEN 6 WHEN 'JULIO' THEN 7 WHEN 'AGOSTO' THEN 8 WHEN 'SEPTIEMBRE' THEN 9 WHEN 'OCTUBRE' THEN 10 WHEN 'NOVIEMBRE' THEN 11 WHEN 'DICIEMBRE' THEN 12 END, -2, 2) AS INTEGER) <= ?")
            params.append(mes_fin)
        except:
            pass
    
    # Filtros por listas
    if sedes:
        sede_list = sedes.split(',')
        placeholders = ','.join('?' * len(sede_list))
        conditions.append(f"sede IN ({placeholders})")
        params.extend(sede_list)
    
    if tipos_inventario:
        tipo_list = tipos_inventario.split(',')
        placeholders = ','.join('?' * len(tipo_list))
        conditions.append(f"tipo_inventario IN ({placeholders})")
        params.extend(tipo_list)
    
    if responsables:
        resp_list = responsables.split(',')
        placeholders = ','.join('?' * len(resp_list))
        conditions.append(f"almacenista IN ({placeholders})")
        params.extend(resp_list)
    
    where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
    return where_clause, params


@router.get("/filtros")
async def get_filtros():
    """Obtener valores únicos para filtros"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        sedes = [row[0] for row in cursor.execute("SELECT DISTINCT sede FROM gestion WHERE sede IS NOT NULL ORDER BY sede").fetchall()]
        tipos = [row[0] for row in cursor.execute("SELECT DISTINCT tipo_inventario FROM gestion WHERE tipo_inventario IS NOT NULL ORDER BY tipo_inventario").fetchall()]
        almacenistas = [row[0] for row in cursor.execute("SELECT DISTINCT almacenista FROM gestion WHERE almacenista IS NOT NULL ORDER BY almacenista").fetchall()]
        
        return {
            "sedes": sedes,
            "tipos_inventario": tipos,
            "responsables": almacenistas
        }


@router.get("/kpis")
async def get_kpis(
    fecha_inicio: Optional[str] = Query(None),
    fecha_fin: Optional[str] = Query(None),
    sedes: Optional[str] = Query(None),
    tipos_inventario: Optional[str] = Query(None),
    responsables: Optional[str] = Query(None)
):
    """Obtener KPIs de gestión"""
    where_clause, params = build_where_clause(fecha_inicio, fecha_fin, sedes, tipos_inventario, responsables)
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Promedio de días de inventario
        if where_clause:
            query = f"SELECT AVG(dias) FROM gestion {where_clause} AND dias IS NOT NULL"
        else:
            query = "SELECT AVG(dias) FROM gestion WHERE dias IS NOT NULL"
        promedio_dias = cursor.execute(query, params).fetchone()[0] or 0
        
        # Total de registros
        query = f"SELECT COUNT(*) FROM gestion {where_clause}"
        total_registros = cursor.execute(query, params).fetchone()[0]
        
        # Cumple indicador (dentro del plazo)
        if where_clause:
            query = f"SELECT COUNT(*) FROM gestion {where_clause} AND indicador_inventario = 'Dentro del plazo'"
        else:
            query = "SELECT COUNT(*) FROM gestion WHERE indicador_inventario = 'Dentro del plazo'"
        cumple_indicador = cursor.execute(query, params).fetchone()[0]
        
        # Porcentaje que cumple
        porcentaje_cumple = (cumple_indicador / total_registros * 100) if total_registros > 0 else 0
        
        return {
            "promedio_dias_inventario": round(promedio_dias, 2),
            "total_registros": total_registros,
            "cumple_indicador": cumple_indicador,
            "porcentaje_cumple": round(porcentaje_cumple, 2)
        }


@router.get("/grafico/por-sede")
async def get_por_sede(
    fecha_inicio: Optional[str] = Query(None),
    fecha_fin: Optional[str] = Query(None),
    sedes: Optional[str] = Query(None),
    tipos_inventario: Optional[str] = Query(None),
    responsables: Optional[str] = Query(None)
):
    """Obtener datos agrupados por sede (indicador de respuesta)"""
    where_clause, params = build_where_clause(fecha_inicio, fecha_fin, sedes, tipos_inventario, responsables)
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        query = f"""
            SELECT 
                sede,
                SUM(CASE WHEN indicador_inventario = 'Dentro del plazo' THEN 1 ELSE 0 END) as dentro_plazo,
                SUM(CASE WHEN indicador_inventario = 'Fuera del plazo' THEN 1 ELSE 0 END) as fuera_plazo,
                AVG(dias) as promedio_dias,
                COUNT(*) as total
            FROM gestion
            {where_clause}
            GROUP BY sede
            ORDER BY sede
        """
        
        rows = cursor.execute(query, params).fetchall()
        
        sedes_list = []
        dentro_plazo = []
        fuera_plazo = []
        promedio_dias = []
        total = []
        
        for row in rows:
            sedes_list.append(row[0])
            dentro_plazo.append(row[1])
            fuera_plazo.append(row[2])
            promedio_dias.append(round(row[3], 2) if row[3] else 0)
            total.append(row[4])
        
        return {
            "sedes": sedes_list,
            "dentro_plazo": dentro_plazo,
            "fuera_plazo": fuera_plazo,
            "promedio_dias": promedio_dias,
            "total": total
        }


@router.get("/grafico/por-responsable")
async def get_por_responsable(
    fecha_inicio: Optional[str] = Query(None),
    fecha_fin: Optional[str] = Query(None),
    sedes: Optional[str] = Query(None),
    tipos_inventario: Optional[str] = Query(None),
    responsables: Optional[str] = Query(None)
):
    """Obtener datos agrupados por responsable"""
    where_clause, params = build_where_clause(fecha_inicio, fecha_fin, sedes, tipos_inventario, responsables)
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        query = f"""
            SELECT 
                almacenista,
                SUM(CASE WHEN indicador_inventario = 'Dentro del plazo' THEN 1 ELSE 0 END) as dentro_plazo,
                SUM(CASE WHEN indicador_inventario = 'Fuera del plazo' THEN 1 ELSE 0 END) as fuera_plazo,
                AVG(dias) as promedio_dias,
                COUNT(*) as total
            FROM gestion
            {where_clause}
            GROUP BY almacenista
            ORDER BY promedio_dias DESC
        """
        
        rows = cursor.execute(query, params).fetchall()
        
        responsables_list = []
        dentro_plazo = []
        fuera_plazo = []
        promedio_dias = []
        total = []
        
        for row in rows:
            responsables_list.append(row[0])
            dentro_plazo.append(row[1])
            fuera_plazo.append(row[2])
            promedio_dias.append(round(row[3], 2) if row[3] else 0)
            total.append(row[4])
        
        return {
            "responsables": responsables_list,
            "dentro_plazo": dentro_plazo,
            "fuera_plazo": fuera_plazo,
            "promedio_dias": promedio_dias,
            "total": total
        }
