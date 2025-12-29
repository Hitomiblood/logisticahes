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
        conditions.append(f"responsable IN ({placeholders})")
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
        responsables = [row[0] for row in cursor.execute("SELECT DISTINCT responsable FROM gestion WHERE responsable IS NOT NULL ORDER BY responsable").fetchall()]
        
        return {
            "sedes": sedes,
            "tipos_inventario": tipos,
            "responsables": responsables
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
        query = f"SELECT AVG(dias) FROM gestion {where_clause} AND dias IS NOT NULL"
        promedio_dias = cursor.execute(query, params).fetchone()[0] or 0
        
        # Promedio de días de respuesta
        query = f"SELECT AVG(dias_respuesta) FROM gestion {where_clause} AND dias_respuesta IS NOT NULL"
        promedio_dias_respuesta = cursor.execute(query, params).fetchone()[0] or 0
        
        # Total de registros
        query = f"SELECT COUNT(*) FROM gestion {where_clause}"
        total_registros = cursor.execute(query, params).fetchone()[0]
        
        # Dentro del plazo (respuesta)
        query = f"SELECT COUNT(*) FROM gestion {where_clause} AND indicador_respuesta = 'Dentro del plazo'"
        dentro_plazo = cursor.execute(query, params).fetchone()[0]
        
        # Porcentaje dentro del plazo
        porcentaje_plazo = (dentro_plazo / total_registros * 100) if total_registros > 0 else 0
        
        return {
            "promedio_dias_inventario": round(promedio_dias, 2),
            "promedio_dias_respuesta": round(promedio_dias_respuesta, 2),
            "total_registros": total_registros,
            "dentro_plazo": dentro_plazo,
            "porcentaje_plazo": round(porcentaje_plazo, 2)
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
                SUM(CASE WHEN indicador_respuesta = 'Dentro del plazo' THEN 1 ELSE 0 END) as dentro_plazo,
                SUM(CASE WHEN indicador_respuesta = 'Fuera del plazo' THEN 1 ELSE 0 END) as fuera_plazo,
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
        total = []
        
        for row in rows:
            sedes_list.append(row[0])
            dentro_plazo.append(row[1])
            fuera_plazo.append(row[2])
            total.append(row[3])
        
        return {
            "sedes": sedes_list,
            "dentro_plazo": dentro_plazo,
            "fuera_plazo": fuera_plazo,
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
                responsable,
                SUM(CASE WHEN indicador_respuesta = 'Dentro del plazo' THEN 1 ELSE 0 END) as dentro_plazo,
                SUM(CASE WHEN indicador_respuesta = 'Fuera del plazo' THEN 1 ELSE 0 END) as fuera_plazo,
                AVG(dias_respuesta) as promedio_dias_respuesta,
                COUNT(*) as total
            FROM gestion
            {where_clause}
            GROUP BY responsable
            ORDER BY promedio_dias_respuesta DESC
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
            "promedio_dias_respuesta": promedio_dias,
            "total": total
        }
