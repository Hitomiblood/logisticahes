"""
Script para importar datos de Excel a la base de datos (SQLite o PostgreSQL)
"""
import pandas as pd
import sys
from pathlib import Path

# Agregar el directorio padre al path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.config import EXCEL_FILES, DB_PATH, DB_TYPE
from backend.database import init_db, clear_table, get_db


def adapt_sql(sql):
    """Adaptar SQL para el tipo de base de datos (? -> %s para PostgreSQL)"""
    if DB_TYPE == "postgresql":
        return sql.replace("?", "%s")
    return sql

def fix_encoding(text):
    """Corregir caracteres mal codificados"""
    if not isinstance(text, str):
        return text
    
    replacements = [
        ("Ã¡", "á"), ("Ã©", "é"), ("Ã­", "í"), ("Ã³", "ó"), ("Ãº", "ú"),
        ("Ã±", "ñ"), ("Ã¼", "ü"), ("Ã\x81", "Á"), ("Ã‰", "É"),
        ("Ã\x91", "Ñ"), ("Ãš", "Ú"), ("Ãœ", "Ü"),
        ("Âª", "ª"), ("Âº", "º"), ("Â°", "°")
    ]
    
    result = text
    for bad, good in replacements:
        result = result.replace(bad, good)
    return result


def safe_numeric(value, target_type='real'):
    """Convertir valor a numérico de forma segura, retorna None si no es posible"""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, (int, float)):
        return int(value) if target_type == 'integer' else float(value)
    if isinstance(value, str):
        # Limpiar el string
        cleaned = value.strip().replace(',', '.').replace('$', '').replace(' ', '')
        try:
            num = float(cleaned)
            return int(num) if target_type == 'integer' else num
        except (ValueError, TypeError):
            return None
    return None

def import_costos_mensuales():
    """Importar datos de Costos Mensuales"""
    config = EXCEL_FILES["costos_mensuales"]
    print(f"📂 Leyendo {config['path']}...")
    
    try:
        df = pd.read_excel(config["path"], sheet_name=config["sheet"])
        print(f"   Registros encontrados: {len(df)}")
        
        # Limpiar tabla
        clear_table("costos_mensuales")
        
        # Mapear columnas
        column_mapping = {
            "Fecha": "fecha",
            "Catalogo": "catalogo",
            "Neto": "neto",
            "Ciudad|Descripción": "ciudad",
            "Proyecto|Nombre": "proyecto",
            "Tercero|Nombre": "tercero",
            "Descripción": "descripcion"
        }
        
        # Preparar datos
        records = []
        for _, row in df.iterrows():
            record = {}
            for excel_col, db_col in column_mapping.items():
                value = row.get(excel_col)
                if pd.isna(value):
                    value = None
                elif isinstance(value, str):
                    value = fix_encoding(value)
                elif db_col == "fecha" and value is not None:
                    value = str(value)[:10]  # Formato YYYY-MM-DD
                record[db_col] = value
            records.append(record)
        
        # Insertar en BD
        with get_db() as conn:
            cursor = conn.cursor()
            for record in records:
                cursor.execute(adapt_sql('''
                    INSERT INTO costos_mensuales 
                    (fecha, catalogo, neto, ciudad, proyecto, tercero, descripcion)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                '''), (
                    record["fecha"],
                    record["catalogo"],
                    record["neto"],
                    record["ciudad"],
                    record["proyecto"],
                    record["tercero"],
                    record["descripcion"]
                ))
            conn.commit()
        
        print(f"✅ Costos Mensuales: {len(records)} registros importados")
        return len(records)
        
    except Exception as e:
        print(f"❌ Error importando Costos Mensuales: {e}")
        raise

def import_operatividad_vehiculos():
    """Importar datos de Operatividad Vehículos"""
    config = EXCEL_FILES["operatividad_vehiculos"]
    print(f"📂 Leyendo {config['path']}...")
    
    try:
        df = pd.read_excel(config["path"], sheet_name=config["sheet"])
        print(f"   Registros encontrados: {len(df)}")
        
        # Limpiar tabla
        clear_table("operatividad_vehiculos")
        
        # Mapear columnas
        column_mapping = {
            "Fecha ejecucion": "fecha_ejecucion",
            "placa": "placa",
            "Tipo vehiculo": "tipo_vehiculo",
            "Sede": "sede",
            "Estado Vehiculo": "estado_vehiculo",
            "Brigada": "brigada",
            "Conductor": "conductor",
            "Contrato": "contrato",
            "GPS": "gps",
            "justificacion no salida": "justificacion_no_salida",
            "Tipo de Daño": "tipo_dano",
            "Daño inoperatividad": "dano_inoperatividad",
            "Motivo de inoperatividad": "motivo_inoperatividad",
            "Observacion inoperatividad": "observacion_inoperatividad",
            "Tipo Mantenimiento": "tipo_mantenimiento",
            "Km mantenimiento": "km_mantenimiento",
            "Vehiculos programados": "vehiculos_programados",
            "Vehiculos operativos": "vehiculos_operativos",
            "Dias en taller": "dias_en_taller",
            "Propietario": "propietario",
            "Indicador": "indicador"
        }
        
        # Preparar datos
        records = []
        for _, row in df.iterrows():
            record = {}
            for excel_col, db_col in column_mapping.items():
                value = row.get(excel_col)
                if pd.isna(value):
                    value = None
                elif isinstance(value, str):
                    value = fix_encoding(value)
                elif db_col == "fecha_ejecucion" and value is not None:
                    value = str(value)[:10]  # Formato YYYY-MM-DD
                record[db_col] = value
            records.append(record)
        
        # Insertar en BD por lotes para mejor rendimiento
        with get_db() as conn:
            cursor = conn.cursor()
            batch_size = 1000
            for i in range(0, len(records), batch_size):
                batch = records[i:i+batch_size]
                cursor.executemany(adapt_sql('''
                    INSERT INTO operatividad_vehiculos 
                    (fecha_ejecucion, placa, tipo_vehiculo, sede, estado_vehiculo,
                     brigada, conductor, contrato, gps, justificacion_no_salida,
                     tipo_dano, dano_inoperatividad, motivo_inoperatividad,
                     observacion_inoperatividad, tipo_mantenimiento, km_mantenimiento,
                     vehiculos_programados, vehiculos_operativos, dias_en_taller,
                     propietario, indicador)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                '''), [
                    (r["fecha_ejecucion"], r["placa"], r["tipo_vehiculo"], r["sede"],
                     r["estado_vehiculo"], r["brigada"], r["conductor"], r["contrato"],
                     r["gps"], r["justificacion_no_salida"], r["tipo_dano"],
                     r["dano_inoperatividad"], r["motivo_inoperatividad"],
                     r["observacion_inoperatividad"], r["tipo_mantenimiento"],
                     r["km_mantenimiento"], r["vehiculos_programados"],
                     r["vehiculos_operativos"], r["dias_en_taller"],
                     r["propietario"], r["indicador"])
                    for r in batch
                ])
                conn.commit()
                print(f"   Insertados {min(i+batch_size, len(records))}/{len(records)}...")
        
        print(f"✅ Operatividad Vehículos: {len(records)} registros importados")
        return len(records)
        
    except Exception as e:
        print(f"❌ Error importando Operatividad Vehículos: {e}")
        raise


def import_indicadores_almacenes():
    """Importar datos de Indicadores de Almacenes (6 hojas)"""
    config = EXCEL_FILES["indicadores_almacenes"]
    print(f"📂 Leyendo {config['path']}...")
    
    total_records = 0
    
    try:
        # ========== OYMM (Indicadores) ==========
        print("   📋 Hoja: OYMM...")
        df = pd.read_excel(config["path"], sheet_name=config["sheets"]["oymm"])
        print(f"      Registros encontrados: {len(df)}")
        
        clear_table("indicadores")
        
        column_mapping = {
            "AÑO": "anio",
            "MES": "mes",
            "SEDE": "sede",
            "RESPONSABLE": "responsable",
            "CODIGO": "codigo",
            "DESCRIPCION": "descripcion",
            "INVENTARIO INICIAL": "inventario_inicial",
            "TOTAL ENTREGADO EN EL PERIODO": "total_entregado",
            "TOTAL CONSUMOS EN EL PERIODO": "total_consumos",
            "TOTAL REINTEGROS EN EL PERIODO": "total_reintegros",
            "DENUNCIO FISCALIA POR HURTO EN EL PERIODO": "denuncio_fiscalia",
            "INVENTARIO FINAL": "inventario_final",
            "DIFERENCIA": "diferencia",
            "PRECIO UNIDAD": "precio_unidad",
            "PRECIO TOTAL": "precio_total",
            "COSTO FINAL  INVENTARIO ": "costo_inventario_final",
            "COSTO DIFERENCIA ": "costo_diferencia",
            "OBJETIVO ": "objetivo",
            "ESTADO": "estado"
        }
        
        records = []
        for _, row in df.iterrows():
            record = {}
            for excel_col, db_col in column_mapping.items():
                value = row.get(excel_col)
                if pd.isna(value):
                    value = None
                elif isinstance(value, str):
                    value = fix_encoding(value)
                record[db_col] = value
            records.append(record)
        
        with get_db() as conn:
            cursor = conn.cursor()
            batch_size = 1000
            for i in range(0, len(records), batch_size):
                batch = records[i:i+batch_size]
                cursor.executemany(adapt_sql('''
                    INSERT INTO indicadores 
                    (anio, mes, sede, responsable, codigo, descripcion, inventario_inicial,
                     total_entregado, total_consumos, total_reintegros, denuncio_fiscalia,
                     inventario_final, diferencia, precio_unidad, precio_total,
                     costo_inventario_final, costo_diferencia, objetivo, estado)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                '''), [(r.get("anio"), r["mes"], r["sede"], r["responsable"], r["codigo"], r["descripcion"],
                       r["inventario_inicial"], r["total_entregado"], r["total_consumos"],
                       r["total_reintegros"], r["denuncio_fiscalia"], r["inventario_final"],
                       r["diferencia"], r["precio_unidad"], r["precio_total"],
                       r["costo_inventario_final"], r["costo_diferencia"], r["objetivo"], r.get("estado")) for r in batch])
                conn.commit()
                print(f"      Insertados {min(i+batch_size, len(records))}/{len(records)}...")
        
        total_records += len(records)
        print(f"   ✅ OYMM: {len(records)} registros")
        
        # ========== FISCAL-RU ==========
        print("   📋 Hoja: FISCAL-RU...")
        df = pd.read_excel(config["path"], sheet_name=config["sheets"]["fiscal_ru"])
        print(f"      Registros encontrados: {len(df)}")
        
        clear_table("fiscal_ru")
        
        column_mapping = {
            "MES ": "mes",
            "Item": "item",
            "Descripción": "descripcion",
            "Bodega": "bodega",
            "SEDE ": "sede",
            "Saldo Final": "saldo_final",
            "Costo Promedio": "costo_promedio",
            "Costo Total": "costo_total",
            "Inf. Fisico": "inf_fisico",
            "Diferencia": "diferencia",
            "Estado": "estado",
            "Costo Diferencia": "costo_diferencia",
            "Unidad": "unidad",
            "Clasificación": "clasificacion",
            "Descripción3": "descripcion3",
            "TIPO INVENTARIO ": "tipo_inventario",
            "OBJETIVO ": "objetivo"
        }
        
        records = []
        for _, row in df.iterrows():
            record = {}
            for excel_col, db_col in column_mapping.items():
                value = row.get(excel_col)
                if pd.isna(value):
                    value = None
                elif isinstance(value, str):
                    value = fix_encoding(value)
                record[db_col] = value
            records.append(record)
        
        with get_db() as conn:
            cursor = conn.cursor()
            batch_size = 1000
            for i in range(0, len(records), batch_size):
                batch = records[i:i+batch_size]
                cursor.executemany(adapt_sql('''
                    INSERT INTO fiscal_ru 
                    (mes, item, descripcion, bodega, sede, saldo_final, costo_promedio,
                     costo_total, inf_fisico, diferencia, estado, costo_diferencia,
                     unidad, clasificacion, descripcion3, tipo_inventario, objetivo)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                '''), [(r["mes"], r["item"], r["descripcion"], r["bodega"], r["sede"],
                       r["saldo_final"], r["costo_promedio"], r["costo_total"], r["inf_fisico"],
                       r["diferencia"], r["estado"], r["costo_diferencia"], r["unidad"],
                       r["clasificacion"], r["descripcion3"], r["tipo_inventario"], r["objetivo"]) for r in batch])
                conn.commit()
                print(f"      Insertados {min(i+batch_size, len(records))}/{len(records)}...")
        
        total_records += len(records)
        print(f"   ✅ FISCAL-RU: {len(records)} registros")
        
        # ========== BRIGADAS ==========
        print("   📋 Hoja: BRIGADAS...")
        df = pd.read_excel(config["path"], sheet_name=config["sheets"]["brigadas"])
        print(f"      Registros encontrados: {len(df)}")
        
        clear_table("brigadas")
        
        column_mapping = {
            "MES ": "mes",
            "SEDE ": "sede",
            "ITEM CODIGO": "item_codigo",
            "DESCRIPCION ": "descripcion",
            "TERCERO IDENTIFICACION": "tercero_id",
            "TERCERO NOMBRE": "tercero_nombre",
            "NETO": "neto",
            "CONTEO": "conteo",
            "RECONTEO": "reconteo",
            "DIFERENCIA": "diferencia",
            "ESTADO": "estado",
            "COSTO UNIT": "costo_unitario",
            "COSTO TOTAL": "costo_total",
            "COSTO DIFERENCIA ": "costo_diferencia"
        }
        
        records = []
        for _, row in df.iterrows():
            record = {}
            for excel_col, db_col in column_mapping.items():
                value = row.get(excel_col)
                if pd.isna(value):
                    value = None
                elif isinstance(value, str):
                    value = fix_encoding(value)
                record[db_col] = value
            records.append(record)
        
        with get_db() as conn:
            cursor = conn.cursor()
            batch_size = 1000
            for i in range(0, len(records), batch_size):
                batch = records[i:i+batch_size]
                cursor.executemany(adapt_sql('''
                    INSERT INTO brigadas 
                    (mes, sede, item_codigo, descripcion, tercero_id, tercero_nombre,
                     neto, conteo, reconteo, diferencia, estado, costo_unitario,
                     costo_total, costo_diferencia)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                '''), [(r["mes"], r["sede"], r["item_codigo"], r["descripcion"], r["tercero_id"],
                       r["tercero_nombre"], r["neto"], r["conteo"], r["reconteo"], r["diferencia"],
                       r["estado"], r["costo_unitario"], r["costo_total"], r["costo_diferencia"]) for r in batch])
                conn.commit()
                print(f"      Insertados {min(i+batch_size, len(records))}/{len(records)}...")
        
        total_records += len(records)
        print(f"   ✅ BRIGADAS: {len(records)} registros")
        
        # ========== ERRORES ==========
        print("   📋 Hoja: ERRORES...")
        df = pd.read_excel(config["path"], sheet_name=config["sheets"]["errores"])
        print(f"      Registros encontrados: {len(df)}")
        
        clear_table("errores")
        
        column_mapping = {
            "Error": "error",
            "Zona": "zona",
            "Bodega": "bodega",
            "DOC": "doc",
            "Fecha": "fecha",
            "Tipo numero": "tipo_numero",
            "Tipo numero2": "tipo_numero2",
            "Codigo": "codigo",
            "Descripcion": "descripcion",
            "Bodega2": "bodega2",
            "Tercero": "tercero",
            "Nombre": "nombre",
            "Nombre 2": "nombre2",
            "Cantidad": "cantidad",
            "Costo": "costo",
            "Total": "total",
            "Cantidad3": "cantidad3",
            "Costo4": "costo4",
            "Total5": "total5",
            "Codigo6": "codigo6",
            "Nombre7": "nombre7",
            "OBS": "observacion"
        }
        
        records = []
        for _, row in df.iterrows():
            record = {}
            for excel_col, db_col in column_mapping.items():
                value = row.get(excel_col)
                if pd.isna(value):
                    value = None
                elif isinstance(value, str):
                    value = fix_encoding(value)
                elif db_col == "fecha" and value is not None:
                    value = str(value)[:10]
                record[db_col] = value
            records.append(record)
        
        with get_db() as conn:
            cursor = conn.cursor()
            batch_size = 1000
            for i in range(0, len(records), batch_size):
                batch = records[i:i+batch_size]
                cursor.executemany(adapt_sql('''
                    INSERT INTO errores 
                    (error, zona, bodega, doc, fecha, tipo_numero, tipo_numero2, codigo,
                     descripcion, bodega2, tercero, nombre, nombre2, cantidad, costo,
                     total, cantidad3, costo4, total5, codigo6, nombre7, observacion)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                '''), [(r["error"], r["zona"], r["bodega"], r["doc"], r["fecha"], r["tipo_numero"],
                       r["tipo_numero2"], r["codigo"], r["descripcion"], r["bodega2"], r["tercero"],
                       r["nombre"], r["nombre2"], r["cantidad"], r["costo"], r["total"],
                       r["cantidad3"], r["costo4"], r["total5"], r["codigo6"], r["nombre7"],
                       r["observacion"]) for r in batch])
                conn.commit()
                print(f"      Insertados {min(i+batch_size, len(records))}/{len(records)}...")
        
        total_records += len(records)
        print(f"   ✅ ERRORES: {len(records)} registros")
        
        # ========== PROGRAMADOS vs EJECUTADOS ==========
        print("   📋 Hoja: PRO VS EJECU...")
        df = pd.read_excel(config["path"], sheet_name=config["sheets"]["programados"])
        print(f"      Registros encontrados: {len(df)}")
        
        clear_table("programados_ejecutados")
        
        column_mapping = {
            "FECHA PROPUESTA": "fecha_propuesta",
            "SEDE": "sede",
            "PROGRAMADOS": "programados",
            "EJECUTADOS": "ejecutados",
            "Indicador Programacion": "indicador_programacion",
            "TIPO INVENTARIO ": "tipo_inventario"
        }
        
        records = []
        for _, row in df.iterrows():
            record = {}
            for excel_col, db_col in column_mapping.items():
                value = row.get(excel_col)
                if pd.isna(value):
                    value = None
                elif isinstance(value, str):
                    value = fix_encoding(value)
                elif db_col == "fecha_propuesta" and value is not None:
                    value = str(value)[:10]
                record[db_col] = value
            records.append(record)
        
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.executemany(adapt_sql('''
                INSERT INTO programados_ejecutados 
                (fecha_propuesta, sede, programados, ejecutados, indicador_programacion, tipo_inventario)
                VALUES (?, ?, ?, ?, ?, ?)
            '''), [(r["fecha_propuesta"], r["sede"], r["programados"], r["ejecutados"],
                   r["indicador_programacion"], r["tipo_inventario"]) for r in records])
            conn.commit()
        
        total_records += len(records)
        print(f"   ✅ PROGRAMADOS: {len(records)} registros")
        
        # ========== GESTION ==========
        print("   📋 Hoja: GESTION...")
        df = pd.read_excel(config["path"], sheet_name=config["sheets"]["gestion"])
        print(f"      Registros encontrados: {len(df)}")
        
        clear_table("gestion")
        
        column_mapping = {
            "MES": "mes",
            "SEDE": "sede",
            "TIPO INVENTARIO": "tipo_inventario",
            "ALMACENISTA ": "almacenista",
            "Fecha Ejecución Invetario": "fecha_ejecucion",
            "Fecha Reporte Operaciones": "fecha_reporte",
            "DIAS ": "dias",
            "Indicador Inventario ": "indicador_inventario"
        }
        
        records = []
        for _, row in df.iterrows():
            record = {}
            for excel_col, db_col in column_mapping.items():
                value = row.get(excel_col)
                if pd.isna(value):
                    value = None
                elif isinstance(value, str):
                    value = fix_encoding(value)
                elif "fecha" in db_col and value is not None:
                    value = str(value)[:10]
                record[db_col] = value
            records.append(record)
        
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.executemany(adapt_sql('''
                INSERT INTO gestion 
                (mes, sede, tipo_inventario, almacenista, fecha_ejecucion,
                 fecha_reporte, dias, indicador_inventario)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            '''), [(r["mes"], r["sede"], r["tipo_inventario"], r["almacenista"],
                   r["fecha_ejecucion"], r["fecha_reporte"], r["dias"],
                   r["indicador_inventario"]) for r in records])
            conn.commit()
        
        total_records += len(records)
        print(f"   ✅ GESTION: {len(records)} registros")
        
        print(f"✅ Indicadores Almacenes Total: {total_records} registros importados")
        return total_records
        
    except Exception as e:
        print(f"❌ Error importando Indicadores Almacenes: {e}")
        import traceback
        traceback.print_exc()
        raise


def main():
    """Función principal de importación"""
    print("=" * 60)
    print("🚀 IMPORTADOR DE DATOS - LOGÍSTICA HESEGO")
    print("=" * 60)
    
    # Inicializar BD
    init_db()
    
    # Importar datos
    total = 0
    
    try:
        total += import_costos_mensuales()
    except Exception as e:
        print(f"⚠️ Error en Costos Mensuales: {e}")
    
    try:
        total += import_operatividad_vehiculos()
    except Exception as e:
        print(f"⚠️ Error en Operatividad Vehículos: {e}")
    
    try:
        total += import_compras()
    except Exception as e:
        print(f"⚠️ Error en Compras: {e}")
    
    try:
        total += import_dashboard_operativo()
    except Exception as e:
        print(f"⚠️ Error en Dashboard Operativo: {e}")
    
    try:
        total += import_indicadores_almacenes()
    except Exception as e:
        print(f"⚠️ Error en Indicadores Almacenes: {e}")
    
    print("=" * 60)
    print(f"✅ IMPORTACIÓN COMPLETADA - Total: {total:,} registros")
    print(f"📁 Base de datos: {DB_PATH}")
    print("=" * 60)


def import_dashboard_operativo():
    """
    Importar datos del Dashboard Operativo desde carpetas consolidadas (DATA BI)
    
    IMPORTANTE: Este proceso usa TABLAS SEPARADAS para evitar conflictos:
    - dashboard_oc_descuentos (consolidada de carpetas DATA BI)
    - dashboard_traza_req_oc (consolidada de carpetas DATA BI)
    
    Las tablas originales (oc_descuentos, traza_req_oc) son usadas por compras.html
    y se importan desde BASE INFORME COMPRAS.xlsx mediante import_compras().
    
    Esto permite que ambos dashboards coexistan sin sobrescribirse.
    """
    config = EXCEL_FILES["dashboard_operativo"]
    print(f"📂 Importando datos del Dashboard Operativo...")
    
    total_records = 0
    
    try:
        # ========== OC_DESCUENTOS - Consolidar todos los archivos ==========
        print("   📋 Consolidando archivos de OC_DESCUENTOS...")
        oc_descuentos_folder = config["oc_descuentos_folder"]
        
        if not oc_descuentos_folder.exists():
            print(f"   ⚠️ Carpeta no encontrada: {oc_descuentos_folder}")
        else:
            # Leer todos los archivos Excel de la carpeta
            excel_files = list(oc_descuentos_folder.glob("*.xlsx"))
            print(f"   📁 Archivos encontrados: {[f.name for f in excel_files]}")
            
            if excel_files:
                dfs = []
                for file in excel_files:
                    try:
                        df_temp = pd.read_excel(file)
                        # Agregar columna de origen
                        df_temp['Source.Name'] = file.name
                        dfs.append(df_temp)
                        print(f"      ✓ {file.name}: {len(df_temp)} registros")
                    except Exception as e:
                        print(f"      ✗ Error leyendo {file.name}: {e}")
                
                if dfs:
                    # Consolidar todos los DataFrames
                    df = pd.concat(dfs, ignore_index=True)
                    print(f"   📊 Total registros consolidados: {len(df)}")
                    
                    # Limpiar tabla
                    clear_table("dashboard_oc_descuentos")
                    
                    # Mapear columnas según PowerBI
                    column_mapping = {
                        "Fecha|Fecha": "fecha",
                        "Fecha|Fecha Entrega": "fecha_entrega",
                        "Fecha|Dias Entrega": "dias_entrega",
                        "Documento|Emp": "documento_emp",
                        "Documento|Suc": "documento_suc",
                        "Documento|Tipo": "documento_tipo",
                        "Documento|Núm": "documento_num",
                        "Item|Código": "item_codigo",
                        "Item|Descripción": "item_descripcion",
                        "Item|Bodega": "item_bodega",
                        "Item|Cantidad": "item_cantidad",
                        "Talla": "talla",
                        "Item|Unidad": "item_unidad",
                        "Item|Proyecto": "item_proyecto",
                        "Item|Solicitante": "item_solicitante",
                        "Item|Fecha Requ.": "item_fecha_requ",
                        "Tercero|Identificación": "tercero_id",
                        "Tercero|Nombre": "tercero_nombre",
                        "Costo Unitario": "costo_unitario",
                        "Total Item": "total_item",
                        "Tasa Dcto": "tasa_dcto",
                        "Total Dcto": "total_dcto",
                        "Subtotal": "subtotal",
                        "Tasa IVA": "tasa_iva",
                        "Total IVA": "total_iva",
                        "Total": "total",
                        "Estado": "estado",
                        "Moneda": "moneda",
                        "Observaciones": "observaciones",
                        "Proceso": "proceso",
                        "Concatenado": "concatenado",
                        "%Descuento": "porcentaje_descuento"
                    }
                    
                    # Columnas numéricas según transformaciones de PowerBI y esquema de BD
                    integer_cols = {'dias_entrega', 'documento_suc', 'documento_num', 'item_codigo', 
                                    'item_proyecto'}
                    real_cols = {'item_bodega', 'item_cantidad', 'costo_unitario', 'total_item', 
                                 'tasa_dcto', 'total_dcto', 'subtotal', 'tasa_iva', 
                                 'total_iva', 'total', 'porcentaje_descuento'}
                    
                    records = []
                    for _, row in df.iterrows():
                        record = {}
                        for excel_col, db_col in column_mapping.items():
                            if excel_col in df.columns:
                                value = row[excel_col]
                                
                                # Aplicar conversión de tipos según PowerBI
                                if db_col in integer_cols:
                                    record[db_col] = safe_numeric(value, 'integer')
                                elif db_col in real_cols:
                                    record[db_col] = safe_numeric(value, 'real')
                                elif pd.isna(value):
                                    record[db_col] = None
                                else:
                                    record[db_col] = fix_encoding(str(value))
                            else:
                                record[db_col] = None
                        records.append(record)
                    
                    # Insertar en BD
                    with get_db() as conn:
                        cursor = conn.cursor()
                        sql = adapt_sql('''
                            INSERT INTO dashboard_oc_descuentos (
                                fecha, fecha_entrega, dias_entrega, documento_emp, documento_suc,
                                documento_tipo, documento_num, item_codigo, item_descripcion, item_bodega,
                                item_cantidad, talla, item_unidad, item_proyecto, item_solicitante,
                                item_fecha_requ, tercero_id, tercero_nombre, costo_unitario, total_item,
                                tasa_dcto, total_dcto, subtotal, tasa_iva, total_iva, total,
                                estado, moneda, observaciones, proceso, concatenado, porcentaje_descuento
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''')
                        
                        for record in records:
                            cursor.execute(sql, (
                                record.get('fecha'), record.get('fecha_entrega'), record.get('dias_entrega'),
                                record.get('documento_emp'), record.get('documento_suc'), record.get('documento_tipo'),
                                record.get('documento_num'), record.get('item_codigo'), record.get('item_descripcion'),
                                record.get('item_bodega'), record.get('item_cantidad'), record.get('talla'),
                                record.get('item_unidad'), record.get('item_proyecto'), record.get('item_solicitante'),
                                record.get('item_fecha_requ'), record.get('tercero_id'), record.get('tercero_nombre'),
                                record.get('costo_unitario'), record.get('total_item'), record.get('tasa_dcto'),
                                record.get('total_dcto'), record.get('subtotal'), record.get('tasa_iva'),
                                record.get('total_iva'), record.get('total'), record.get('estado'),
                                record.get('moneda'), record.get('observaciones'), record.get('proceso'),
                                record.get('concatenado'), record.get('porcentaje_descuento')
                            ))
                        
                        conn.commit()
                    
                    total_records += len(records)
                    print(f"   ✅ DASHBOARD OC_DESCUENTOS: {len(records)} registros importados")
        
        # ========== TRAZA_RQ_OC - Consolidar todos los archivos ==========
        print("   📋 Consolidando archivos de TRAZA_RQ_OC...")
        traza_folder = config["traza_rq_oc_folder"]
        
        if not traza_folder.exists():
            print(f"   ⚠️ Carpeta no encontrada: {traza_folder}")
        else:
            # Leer todos los archivos Excel de la carpeta
            excel_files = list(traza_folder.glob("*.xlsx"))
            print(f"   📁 Archivos encontrados: {[f.name for f in excel_files]}")
            
            if excel_files:
                dfs = []
                for file in excel_files:
                    try:
                        df_temp = pd.read_excel(file)
                        # Agregar columna de origen
                        df_temp['Source.Name'] = file.name
                        dfs.append(df_temp)
                        print(f"      ✓ {file.name}: {len(df_temp)} registros")
                    except Exception as e:
                        print(f"      ✗ Error leyendo {file.name}: {e}")
                
                if dfs:
                    # Consolidar todos los DataFrames
                    df = pd.concat(dfs, ignore_index=True)
                    print(f"   📊 Total registros consolidados: {len(df)}")
                    
                    # Limpiar tabla
                    clear_table("dashboard_traza_req_oc")
                    
                    # Mapear columnas según PowerBI
                    column_mapping = {
                        "Requisición|Fecha Entrega": "req_fecha_entrega",
                        "Requisición|Fecha": "req_fecha",
                        "Requisición|Usuario": "req_usuario",
                        "Requisición|Fecha Autorizada": "req_fecha_autorizada",
                        "Requisición|Usuario Autorizador": "req_usuario_autorizador",
                        "Requisición|Emp": "req_emp",
                        "Requisición|Suc": "req_suc",
                        "Requisición| Descripción Tipo Doc": "req_descripcion_tipo_doc",
                        "Requisición|Tipo": "req_tipo",
                        "Requisición|Numero": "req_numero",
                        "Requisición|Estado": "req_estado",
                        "Item|Codigo": "item_codigo",
                        "Item|Descripción": "item_descripcion",
                        "Cotización|Tipo": "cotizacion_tipo",
                        "Cotización|Numero": "cotizacion_numero",
                        "Orden Compra|Fecha": "oc_fecha",
                        "Orden Compra|Usuario ": "oc_usuario",
                        "Orden Compra|Fecha Autorizacion": "oc_fecha_autorizacion",
                        "Orden Compra|Usuario Autorizacion": "oc_usuario_autorizacion",
                        "Orden Compra|Tipo": "oc_tipo",
                        "Orden Compra|Numero": "oc_numero",
                        "Orden Compra|Estado": "oc_estado",
                        "Orden Compra|Tercero|Identificación": "oc_tercero_id",
                        "Orden Compra|Tercero|Suc": "oc_tercero_suc",
                        "Orden Compra|Tercero|Nombre": "oc_tercero_nombre",
                        "Entrega de Servicio|Fecha": "entrega_servicio_fecha",
                        "Entrega de Servicio|Usuario": "entrega_servicio_usuario",
                        "Entrega de Servicio|Tipo": "entrega_servicio_tipo",
                        "Entrega de Servicio|Numero": "entrega_servicio_numero",
                        "Entrega de Almacen|Fecha": "entrega_almacen_fecha",
                        "Entrega de Almacen|Usuario": "entrega_almacen_usuario",
                        "Entrega de Almacen|Tipo": "entrega_almacen_tipo",
                        "Entrega de Almacen|Numero": "entrega_almacen_numero",
                        "Factura de Compra|Fecha": "factura_compra_fecha",
                        "Factura de Compra|Tipo": "factura_compra_tipo",
                        "Factura de Compra|Numero": "factura_compra_numero",
                        "Devolucion de Compra|Fecha": "devolucion_compra_fecha",
                        "Devolucion de Compra|Tipo": "devolucion_compra_tipo",
                        "Devolucion de Compra|Numero": "devolucion_compra_numero",
                        "DÍAS APROBAR RQ": "dias_aprobar_rq",
                        "DÍAS GENERAR OC": "dias_generar_oc",
                        "DÍAS APROBACIÓN OC": "dias_aprobacion_oc",
                        "DÍAS RECEPCIÓN SERVICIO": "dias_recepcion_servicio",
                        "DÍAS ENTRADA ALMACEN": "dias_entrada_almacen",
                        "mes": "mes",
                        "SUMARQ": "suma_rq"
                    }
                    
                    # Columnas numéricas según transformaciones de PowerBI y esquema de BD
                    integer_cols = {'req_emp', 'req_suc', 'req_numero', 'item_codigo', 'cotizacion_numero',
                                    'oc_numero', 'oc_tercero_suc', 'dias_aprobar_rq', 'dias_generar_oc', 
                                    'dias_aprobacion_oc', 'suma_rq'}
                    real_cols = {'entrega_servicio_numero', 'entrega_almacen_numero', 
                                 'factura_compra_numero', 'devolucion_compra_numero',
                                 'dias_recepcion_servicio', 'dias_entrada_almacen', 'mes'}
                    
                    records = []
                    for _, row in df.iterrows():
                        record = {}
                        for excel_col, db_col in column_mapping.items():
                            if excel_col in df.columns:
                                value = row[excel_col]
                                
                                # Aplicar conversión de tipos según PowerBI
                                if db_col in integer_cols:
                                    record[db_col] = safe_numeric(value, 'integer')
                                elif pd.isna(value):
                                    record[db_col] = None
                                else:
                                    record[db_col] = fix_encoding(str(value))
                            else:
                                record[db_col] = None
                        records.append(record)
                    
                    # Insertar en BD
                    with get_db() as conn:
                        cursor = conn.cursor()
                        sql = adapt_sql('''
                            INSERT INTO dashboard_traza_req_oc (
                                req_fecha_entrega, req_fecha, req_usuario, req_fecha_autorizada,
                                req_usuario_autorizador, req_emp, req_suc, req_descripcion_tipo_doc,
                                req_tipo, req_numero, req_estado, item_codigo, item_descripcion,
                                cotizacion_tipo, cotizacion_numero, oc_fecha, oc_usuario,
                                oc_fecha_autorizacion, oc_usuario_autorizacion, oc_tipo, oc_numero,
                                oc_estado, oc_tercero_id, oc_tercero_suc, oc_tercero_nombre,
                                entrega_servicio_fecha, entrega_servicio_usuario, entrega_servicio_tipo,
                                entrega_servicio_numero, entrega_almacen_fecha, entrega_almacen_usuario,
                                entrega_almacen_tipo, entrega_almacen_numero, factura_compra_fecha,
                                factura_compra_tipo, factura_compra_numero, devolucion_compra_fecha,
                                devolucion_compra_tipo, devolucion_compra_numero, dias_aprobar_rq,
                                dias_generar_oc, dias_aprobacion_oc, dias_recepcion_servicio,
                                dias_entrada_almacen, mes, suma_rq
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''')
                        
                        for record in records:
                            cursor.execute(sql, (
                                record.get('req_fecha_entrega'), record.get('req_fecha'), record.get('req_usuario'),
                                record.get('req_fecha_autorizada'), record.get('req_usuario_autorizador'),
                                record.get('req_emp'), record.get('req_suc'), record.get('req_descripcion_tipo_doc'),
                                record.get('req_tipo'), record.get('req_numero'), record.get('req_estado'),
                                record.get('item_codigo'), record.get('item_descripcion'), record.get('cotizacion_tipo'),
                                record.get('cotizacion_numero'), record.get('oc_fecha'), record.get('oc_usuario'),
                                record.get('oc_fecha_autorizacion'), record.get('oc_usuario_autorizacion'),
                                record.get('oc_tipo'), record.get('oc_numero'), record.get('oc_estado'),
                                record.get('oc_tercero_id'), record.get('oc_tercero_suc'), record.get('oc_tercero_nombre'),
                                record.get('entrega_servicio_fecha'), record.get('entrega_servicio_usuario'),
                                record.get('entrega_servicio_tipo'), record.get('entrega_servicio_numero'),
                                record.get('entrega_almacen_fecha'), record.get('entrega_almacen_usuario'),
                                record.get('entrega_almacen_tipo'), record.get('entrega_almacen_numero'),
                                record.get('factura_compra_fecha'), record.get('factura_compra_tipo'),
                                record.get('factura_compra_numero'), record.get('devolucion_compra_fecha'),
                                record.get('devolucion_compra_tipo'), record.get('devolucion_compra_numero'),
                                record.get('dias_aprobar_rq'), record.get('dias_generar_oc'),
                                record.get('dias_aprobacion_oc'), record.get('dias_recepcion_servicio'),
                                record.get('dias_entrada_almacen'), record.get('mes'), record.get('suma_rq')
                            ))
                        
                        conn.commit()
                    
                    total_records += len(records)
                    print(f"   ✅ DASHBOARD TRAZA_RQ_OC: {len(records)} registros importados")
        
        print(f"✅ Dashboard Operativo Total: {total_records:,} registros importados")
        return total_records
        
    except Exception as e:
        print(f"❌ Error importando Dashboard Operativo: {e}")
        import traceback
        traceback.print_exc()
        raise


def import_compras():
    """
    Importar datos de Compras (3 hojas) - ARCHIVO ÚNICO
    
    Este proceso importa desde BASE INFORME COMPRAS.xlsx:
    - TRAZA REQ OC
    - OC DESCUENTOS  
    - BASE OC GENERADAS (única fuente para esta tabla)
    
    NOTA: Si también ejecutas import_dashboard_operativo(), las tablas 
    traza_req_oc y oc_descuentos serán sobrescritas con datos de las carpetas consolidadas.
    """
    config = EXCEL_FILES["compras"]
    print(f"📂 Leyendo {config['path']}...")
    
    total_records = 0
    
    try:
        # ========== TRAZA REQ OC ==========
        print("   📋 Hoja: TRAZA REQ OC...")
        df = pd.read_excel(config["path"], sheet_name=config["sheets"]["traza_req_oc"])
        print(f"      Registros encontrados: {len(df)}")
        
        clear_table("traza_req_oc")
        
        column_mapping = {
            "Requisición|Fecha Entrega": "req_fecha_entrega",
            "Requisición|Fecha": "req_fecha",
            "Requisición|Usuario": "req_usuario",
            "Requisición|Fecha Autorizada": "req_fecha_autorizada",
            "Requisición|Usuario Autorizador": "req_usuario_autorizador",
            "Requisición|Emp": "req_emp",
            "Requisición|Suc": "req_suc",
            "Requisición| Descripción Tipo Doc": "req_descripcion_tipo_doc",
            "Requisición|Tipo": "req_tipo",
            "Requisición|Numero": "req_numero",
            "Requisición|Estado": "req_estado",
            "Item|Codigo": "item_codigo",
            "Item|Descripción": "item_descripcion",
            "Cotización|Tipo": "cotizacion_tipo",
            "Cotización|Numero": "cotizacion_numero",
            "Orden Compra|Fecha": "oc_fecha",
            "Orden Compra|Usuario ": "oc_usuario",
            "Orden Compra|Fecha Autorizacion": "oc_fecha_autorizacion",
            "Orden Compra|Usuario Autorizacion": "oc_usuario_autorizacion",
            "Orden Compra|Tipo": "oc_tipo",
            "Orden Compra|Numero": "oc_numero",
            "Orden Compra|Estado": "oc_estado",
            "Orden Compra|Tercero|Identificación": "oc_tercero_id",
            "Orden Compra|Tercero|Suc": "oc_tercero_suc",
            "Orden Compra|Tercero|Nombre": "oc_tercero_nombre",
            "Entrega de Servicio|Fecha": "entrega_servicio_fecha",
            "Entrega de Servicio|Usuario": "entrega_servicio_usuario",
            "Entrega de Servicio|Tipo": "entrega_servicio_tipo",
            "Entrega de Servicio|Numero": "entrega_servicio_numero",
            "Entrega de Almacen|Fecha": "entrega_almacen_fecha",
            "Entrega de Almacen|Usuario": "entrega_almacen_usuario",
            "Entrega de Almacen|Tipo": "entrega_almacen_tipo",
            "Entrega de Almacen|Numero": "entrega_almacen_numero",
            "Factura de Compra|Fecha": "factura_compra_fecha",
            "Factura de Compra|Tipo": "factura_compra_tipo",
            "Factura de Compra|Numero": "factura_compra_numero",
            "Devolucion de Compra|Fecha": "devolucion_compra_fecha",
            "Devolucion de Compra|Tipo": "devolucion_compra_tipo",
            "Devolucion de Compra|Numero": "devolucion_compra_numero",
            "DÍAS APROBAR RQ": "dias_aprobar_rq",
            "DÍAS GENERAR OC": "dias_generar_oc",
            "DÍAS APROBACIÓN OC": "dias_aprobacion_oc",
            "DÍAS RECEPCIÓN SERVICIO": "dias_recepcion_servicio",
            "DÍAS ENTRADA ALMACEN": "dias_entrada_almacen",
            "mes": "mes",
            "SUMARQ": "suma_rq"
        }
        
        # Columnas numéricas que necesitan validación de tipo
        integer_cols = {'req_emp', 'req_suc', 'req_numero', 'item_codigo', 'cotizacion_numero', 
                        'oc_numero', 'oc_tercero_suc', 'dias_aprobar_rq', 'dias_generar_oc', 
                        'dias_aprobacion_oc', 'suma_rq'}
        real_cols = {'entrega_servicio_numero', 'entrega_almacen_numero', 'factura_compra_numero',
                     'devolucion_compra_numero', 'dias_recepcion_servicio', 'dias_entrada_almacen', 'mes'}
        
        records = []
        for _, row in df.iterrows():
            record = {}
            for excel_col, db_col in column_mapping.items():
                value = row.get(excel_col)
                if pd.isna(value):
                    value = None
                elif isinstance(value, str):
                    value = fix_encoding(value)
                    # Fechas inválidas
                    if value == "31/12/1899":
                        value = None
                elif "fecha" in db_col and value is not None:
                    value = str(value)[:10]
                # Validar columnas numéricas
                if db_col in integer_cols:
                    value = safe_numeric(value, 'integer')
                elif db_col in real_cols:
                    value = safe_numeric(value, 'real')
                record[db_col] = value
            records.append(record)
        
        with get_db() as conn:
            cursor = conn.cursor()
            batch_size = 1000
            for i in range(0, len(records), batch_size):
                batch = records[i:i+batch_size]
                cursor.executemany(adapt_sql('''
                    INSERT INTO traza_req_oc 
                    (req_fecha_entrega, req_fecha, req_usuario, req_fecha_autorizada, req_usuario_autorizador,
                     req_emp, req_suc, req_descripcion_tipo_doc, req_tipo, req_numero, req_estado,
                     item_codigo, item_descripcion, cotizacion_tipo, cotizacion_numero,
                     oc_fecha, oc_usuario, oc_fecha_autorizacion, oc_usuario_autorizacion,
                     oc_tipo, oc_numero, oc_estado, oc_tercero_id, oc_tercero_suc, oc_tercero_nombre,
                     entrega_servicio_fecha, entrega_servicio_usuario, entrega_servicio_tipo, entrega_servicio_numero,
                     entrega_almacen_fecha, entrega_almacen_usuario, entrega_almacen_tipo, entrega_almacen_numero,
                     factura_compra_fecha, factura_compra_tipo, factura_compra_numero,
                     devolucion_compra_fecha, devolucion_compra_tipo, devolucion_compra_numero,
                     dias_aprobar_rq, dias_generar_oc, dias_aprobacion_oc, dias_recepcion_servicio, dias_entrada_almacen,
                     mes, suma_rq)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                '''), [tuple(r.values()) for r in batch])
                conn.commit()
                print(f"      Insertados {min(i+batch_size, len(records))}/{len(records)}...")
        
        total_records += len(records)
        print(f"   ✅ TRAZA REQ OC: {len(records)} registros")
        
        # ========== OC DESCUENTOS ==========
        print("   📋 Hoja: OC DESCUENTOS...")
        df = pd.read_excel(config["path"], sheet_name=config["sheets"]["oc_descuentos"])
        print(f"      Registros encontrados: {len(df)}")
        
        clear_table("oc_descuentos")
        
        column_mapping = {
            "Fecha|Fecha": "fecha",
            "Fecha|Fecha Entrega": "fecha_entrega",
            "Fecha|Dias Entrega": "dias_entrega",
            "Documento|Emp": "documento_emp",
            "Documento|Suc": "documento_suc",
            "Documento|Tipo": "documento_tipo",
            "Documento|Núm": "documento_num",
            "Item|Código": "item_codigo",
            "Item|Descripción": "item_descripcion",
            "Item|Bodega": "item_bodega",
            "Item|Cantidad": "item_cantidad",
            "Talla": "talla",
            "Item|Unidad": "item_unidad",
            "Item|Proyecto": "item_proyecto",
            "Item|Solicitante": "item_solicitante",
            "Item|Fecha Requ.": "item_fecha_requ",
            "Tercero|Identificación": "tercero_id",
            "Tercero|Nombre": "tercero_nombre",
            "Costo Unitario": "costo_unitario",
            "Total Item": "total_item",
            "Tasa Dcto": "tasa_dcto",
            "Total Dcto": "total_dcto",
            "Subtotal": "subtotal",
            "Tasa IVA": "tasa_iva",
            "Total IVA": "total_iva",
            "Total": "total",
            "Estado": "estado",
            "Moneda": "moneda",
            "Observaciones": "observaciones",
            "Proceso": "proceso",
            "Concatenado": "concatenado",
            "%Descuento": "porcentaje_descuento"
        }
        
        # Columnas numéricas de oc_descuentos
        oc_integer_cols = {'dias_entrega', 'documento_suc', 'documento_num', 'item_codigo', 'item_proyecto'}
        oc_real_cols = {'item_bodega', 'item_cantidad', 'costo_unitario', 'total_item', 'tasa_dcto', 
                        'total_dcto', 'subtotal', 'tasa_iva', 'total_iva', 'total', 'porcentaje_descuento'}
        
        records = []
        for _, row in df.iterrows():
            record = {}
            for excel_col, db_col in column_mapping.items():
                value = row.get(excel_col)
                if pd.isna(value):
                    value = None
                elif isinstance(value, str):
                    value = fix_encoding(value)
                    # Limpiar valores numéricos con formato
                    if db_col in ["costo_unitario", "total_item", "total_iva", "total"]:
                        value = value.replace(",", "").replace("$", "").replace(" ", "").strip()
                        try:
                            value = float(value) if value else None
                        except:
                            value = None
                elif "fecha" in db_col and value is not None and not isinstance(value, str):
                    value = str(value)[:10]
                # Convertir cualquier tipo datetime/time a string
                elif hasattr(value, 'isoformat'):
                    value = str(value)
                # Validar columnas numéricas
                if db_col in oc_integer_cols:
                    value = safe_numeric(value, 'integer')
                elif db_col in oc_real_cols:
                    value = safe_numeric(value, 'real')
                record[db_col] = value
            records.append(record)
        
        with get_db() as conn:
            cursor = conn.cursor()
            batch_size = 1000
            for i in range(0, len(records), batch_size):
                batch = records[i:i+batch_size]
                cursor.executemany(adapt_sql('''
                    INSERT INTO oc_descuentos 
                    (fecha, fecha_entrega, dias_entrega, documento_emp, documento_suc, documento_tipo, documento_num,
                     item_codigo, item_descripcion, item_bodega, item_cantidad, talla, item_unidad, item_proyecto,
                     item_solicitante, item_fecha_requ, tercero_id, tercero_nombre, costo_unitario, total_item,
                     tasa_dcto, total_dcto, subtotal, tasa_iva, total_iva, total, estado, moneda, observaciones,
                     proceso, concatenado, porcentaje_descuento)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                '''), [tuple(r.values()) for r in batch])
                conn.commit()
                print(f"      Insertados {min(i+batch_size, len(records))}/{len(records)}...")
        
        total_records += len(records)
        print(f"   ✅ OC DESCUENTOS: {len(records)} registros")
        
        # ========== BASE OC GENERADAS ==========
        print("   📋 Hoja: BASE OC GENERADAS...")
        df = pd.read_excel(config["path"], sheet_name=config["sheets"]["base_oc_generadas"])
        print(f"      Registros encontrados: {len(df)}")
        
        clear_table("base_oc_generadas")
        
        column_mapping = {
            "Fecha|Fecha": "fecha",
            "Fecha|Fecha Entrega": "fecha_entrega",
            "Fecha|Dias Entrega": "dias_entrega",
            "Documento|Emp": "documento_emp",
            "Documento|Suc": "documento_suc",
            "Documento|Tipo": "documento_tipo",
            "Documento|Núm": "documento_num",
            "Item|Código": "item_codigo",
            "Item|Descripción": "item_descripcion",
            "Item|Bodega": "item_bodega",
            "Item|Cantidad": "item_cantidad",
            "Talla": "talla",
            "Item|Unidad": "item_unidad",
            "Item|Proyecto": "item_proyecto",
            "Item|Solicitante": "item_solicitante",
            "Item|Fecha Requ.": "item_fecha_requ",
            "Tercero|Identificación": "tercero_id",
            "Tercero|Nombre": "tercero_nombre",
            "Costo Unitario": "costo_unitario",
            "Total Item": "total_item",
            "Tasa Dcto": "tasa_dcto",
            "Total Dcto": "total_dcto",
            "Subtotal": "subtotal",
            "Tasa IVA": "tasa_iva",
            "Total IVA": "total_iva",
            "Total": "total",
            "Estado": "estado",
            "Moneda": "moneda",
            "Observaciones": "observaciones"
        }
        
        records = []
        # Columnas numéricas de base_oc_generadas (misma estructura que oc_descuentos)
        base_integer_cols = {'dias_entrega', 'documento_suc', 'documento_num', 'item_codigo', 'item_proyecto'}
        base_real_cols = {'item_bodega', 'item_cantidad', 'costo_unitario', 'total_item', 'tasa_dcto', 
                          'total_dcto', 'subtotal', 'tasa_iva', 'total_iva', 'total'}
        
        for _, row in df.iterrows():
            record = {}
            for excel_col, db_col in column_mapping.items():
                value = row.get(excel_col)
                if pd.isna(value):
                    value = None
                elif isinstance(value, str):
                    value = fix_encoding(value)
                    if db_col in ["costo_unitario", "total_item", "total_iva", "total", "item_cantidad"]:
                        value = value.replace(",", "").replace("$", "").replace(" ", "").strip()
                        try:
                            value = float(value) if value else None
                        except:
                            value = None
                elif "fecha" in db_col and value is not None and not isinstance(value, str):
                    value = str(value)[:10]
                # Validar columnas numéricas
                if db_col in base_integer_cols:
                    value = safe_numeric(value, 'integer')
                elif db_col in base_real_cols:
                    value = safe_numeric(value, 'real')
                record[db_col] = value
            records.append(record)
        
        with get_db() as conn:
            cursor = conn.cursor()
            batch_size = 1000
            for i in range(0, len(records), batch_size):
                batch = records[i:i+batch_size]
                cursor.executemany(adapt_sql('''
                    INSERT INTO base_oc_generadas 
                    (fecha, fecha_entrega, dias_entrega, documento_emp, documento_suc, documento_tipo, documento_num,
                     item_codigo, item_descripcion, item_bodega, item_cantidad, talla, item_unidad, item_proyecto,
                     item_solicitante, item_fecha_requ, tercero_id, tercero_nombre, costo_unitario, total_item,
                     tasa_dcto, total_dcto, subtotal, tasa_iva, total_iva, total, estado, moneda, observaciones)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                '''), [tuple(r.values()) for r in batch])
                conn.commit()
                print(f"      Insertados {min(i+batch_size, len(records))}/{len(records)}...")
        
        total_records += len(records)
        print(f"   ✅ BASE OC GENERADAS: {len(records)} registros")
        
        print(f"✅ Compras Total: {total_records} registros importados")
        return total_records
        
    except Exception as e:
        print(f"❌ Error importando Compras: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
