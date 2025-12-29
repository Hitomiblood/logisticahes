"""
Script para importar datos de Excel a la base de datos SQLite
"""
import pandas as pd
import sys
from pathlib import Path

# Agregar el directorio padre al path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.config import EXCEL_FILES, DB_PATH
from backend.database import init_db, clear_table, get_db

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
                cursor.execute('''
                    INSERT INTO costos_mensuales 
                    (fecha, catalogo, neto, ciudad, proyecto, tercero, descripcion)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
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
                cursor.executemany('''
                    INSERT INTO operatividad_vehiculos 
                    (fecha_ejecucion, placa, tipo_vehiculo, sede, estado_vehiculo,
                     brigada, conductor, contrato, gps, justificacion_no_salida,
                     tipo_dano, dano_inoperatividad, motivo_inoperatividad,
                     observacion_inoperatividad, tipo_mantenimiento, km_mantenimiento,
                     vehiculos_programados, vehiculos_operativos, dias_en_taller,
                     propietario, indicador)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', [
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
        total += import_indicadores()
    except Exception as e:
        print(f"⚠️ Error en Indicadores: {e}")
    
    try:
        total += import_fiscal_ru()
    except Exception as e:
        print(f"⚠️ Error en Fiscal RU: {e}")
    
    try:
        total += import_brigadas()
    except Exception as e:
        print(f"⚠️ Error en Brigadas: {e}")
    
    try:
        total += import_errores()
    except Exception as e:
        print(f"⚠️ Error en Errores: {e}")
    
    try:
        total += import_programados_ejecutados()
    except Exception as e:
        print(f"⚠️ Error en Programados vs Ejecutados: {e}")
    
    try:
        total += import_gestion()
    except Exception as e:
        print(f"⚠️ Error en Gestión Proceso: {e}")
    
    print("=" * 60)
    print(f"✅ IMPORTACIÓN COMPLETADA - Total: {total:,} registros")
    print(f"📁 Base de datos: {DB_PATH}")
    print("=" * 60)


def import_compras():
    """Importar datos de Compras (3 hojas)"""
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
                record[db_col] = value
            records.append(record)
        
        with get_db() as conn:
            cursor = conn.cursor()
            batch_size = 1000
            for i in range(0, len(records), batch_size):
                batch = records[i:i+batch_size]
                cursor.executemany('''
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
                ''', [tuple(r.values()) for r in batch])
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
                record[db_col] = value
            records.append(record)
        
        with get_db() as conn:
            cursor = conn.cursor()
            batch_size = 1000
            for i in range(0, len(records), batch_size):
                batch = records[i:i+batch_size]
                cursor.executemany('''
                    INSERT INTO oc_descuentos 
                    (fecha, fecha_entrega, dias_entrega, documento_emp, documento_suc, documento_tipo, documento_num,
                     item_codigo, item_descripcion, item_bodega, item_cantidad, talla, item_unidad, item_proyecto,
                     item_solicitante, item_fecha_requ, tercero_id, tercero_nombre, costo_unitario, total_item,
                     tasa_dcto, total_dcto, subtotal, tasa_iva, total_iva, total, estado, moneda, observaciones,
                     proceso, concatenado, porcentaje_descuento)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', [tuple(r.values()) for r in batch])
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
                record[db_col] = value
            records.append(record)
        
        with get_db() as conn:
            cursor = conn.cursor()
            batch_size = 1000
            for i in range(0, len(records), batch_size):
                batch = records[i:i+batch_size]
                cursor.executemany('''
                    INSERT INTO base_oc_generadas 
                    (fecha, fecha_entrega, dias_entrega, documento_emp, documento_suc, documento_tipo, documento_num,
                     item_codigo, item_descripcion, item_bodega, item_cantidad, talla, item_unidad, item_proyecto,
                     item_solicitante, item_fecha_requ, tercero_id, tercero_nombre, costo_unitario, total_item,
                     tasa_dcto, total_dcto, subtotal, tasa_iva, total_iva, total, estado, moneda, observaciones)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', [tuple(r.values()) for r in batch])
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


def import_indicadores():
    """Importar datos de Indicadores OYMM"""
    config = EXCEL_FILES["indicadores"]
    print(f"📂 Leyendo {config['path']}...")
    
    try:
        df = pd.read_excel(config["path"], sheet_name=config["sheet"])
        print(f"   Registros encontrados: {len(df)}")
        
        # Limpiar tabla
        clear_table("indicadores")
        
        # Mapear columnas
        column_mapping = {
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
            "OBJETIVO ": "objetivo"
        }
        
        # Preparar datos
        records = []
        for _, row in df.iterrows():
            record = {}
            for excel_col, db_col in column_mapping.items():
                value = row.get(excel_col)
                
                # Procesar valores especiales
                if pd.isna(value):
                    value = None
                elif isinstance(value, str):
                    value = fix_encoding(value.strip())
                    # Convertir strings numéricos con formato especial
                    if db_col in ['inventario_inicial', 'total_entregado', 'total_consumos', 
                                  'total_reintegros', 'inventario_final', 'costo_inventario_final']:
                        try:
                            # Limpiar formato de números con puntos como separadores de miles
                            value = str(value).replace('.', '').replace(',', '.')
                            value = float(value) if value else 0.0
                        except:
                            value = 0.0
                
                record[db_col] = value
            records.append(record)
        
        # Insertar en BD
        with get_db() as conn:
            cursor = conn.cursor()
            for record in records:
                cursor.execute('''
                    INSERT INTO indicadores 
                    (mes, sede, responsable, codigo, descripcion, inventario_inicial,
                     total_entregado, total_consumos, total_reintegros, denuncio_fiscalia,
                     inventario_final, diferencia, precio_unidad, precio_total,
                     costo_inventario_final, costo_diferencia, objetivo)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    record["mes"],
                    record["sede"],
                    record["responsable"],
                    record["codigo"],
                    record["descripcion"],
                    record["inventario_inicial"],
                    record["total_entregado"],
                    record["total_consumos"],
                    record["total_reintegros"],
                    record["denuncio_fiscalia"],
                    record["inventario_final"],
                    record["diferencia"],
                    record["precio_unidad"],
                    record["precio_total"],
                    record["costo_inventario_final"],
                    record["costo_diferencia"],
                    record["objetivo"]
                ))
            conn.commit()
        
        print(f"✅ Indicadores: {len(records)} registros importados")
        return len(records)
        
    except Exception as e:
        print(f"❌ Error importando Indicadores: {e}")
        import traceback
        traceback.print_exc()
        raise


def import_fiscal_ru():
    """Importar datos de Inventario Fiscal RU"""
    config = EXCEL_FILES["fiscal_ru"]
    print(f"📂 Leyendo {config['path']}...")
    
    try:
        df = pd.read_excel(config["path"], sheet_name=config["sheet"])
        print(f"   Registros encontrados: {len(df)}")
        
        # Limpiar tabla
        clear_table("fiscal_ru")
        
        # Mapear columnas
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
        
        # Preparar datos
        records = []
        for _, row in df.iterrows():
            record = {}
            for excel_col, db_col in column_mapping.items():
                value = row.get(excel_col)
                
                # Procesar valores especiales
                if pd.isna(value):
                    value = None
                elif isinstance(value, str):
                    value = fix_encoding(value.strip())
                
                record[db_col] = value
            records.append(record)
        
        # Insertar en BD
        with get_db() as conn:
            cursor = conn.cursor()
            for record in records:
                cursor.execute('''
                    INSERT INTO fiscal_ru 
                    (mes, item, descripcion, bodega, sede, saldo_final,
                     costo_promedio, costo_total, inf_fisico, diferencia,
                     estado, costo_diferencia, unidad, clasificacion,
                     descripcion3, tipo_inventario, objetivo)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    record["mes"],
                    record["item"],
                    record["descripcion"],
                    record["bodega"],
                    record["sede"],
                    record["saldo_final"],
                    record["costo_promedio"],
                    record["costo_total"],
                    record["inf_fisico"],
                    record["diferencia"],
                    record["estado"],
                    record["costo_diferencia"],
                    record["unidad"],
                    record["clasificacion"],
                    record["descripcion3"],
                    record["tipo_inventario"],
                    record["objetivo"]
                ))
            conn.commit()
        
        print(f"✅ Fiscal RU: {len(records)} registros importados")
        return len(records)
        
    except Exception as e:
        print(f"❌ Error importando Fiscal RU: {e}")
        import traceback
        traceback.print_exc()
        raise


def import_brigadas():
    """Importar datos de Brigadas"""
    config = EXCEL_FILES["brigadas"]
    print(f"📂 Leyendo {config['path']} - Hoja: {config['sheet']}...")
    
    try:
        df = pd.read_excel(config["path"], sheet_name=config["sheet"])
        print(f"   Registros encontrados: {len(df)}")
        
        # Limpiar tabla
        clear_table("brigadas")
        
        # Mapear columnas (con espacios al final)
        column_mapping = {
            "MES ": "mes",
            "SEDE ": "sede",
            "ITEM CODIGO": "item_codigo",
            "DESCRIPCION ": "descripcion",
            "TERCERO IDENTIFICACION": "tercero_identificacion",
            "TERCERO NOMBRE": "tercero_nombre",
            "NETO": "neto",
            "CONTEO": "conteo",
            "RECONTEO": "reconteo",
            "DIFERENCIA": "diferencia",
            "ESTADO": "estado",
            "COSTO UNIT": "costo_unit",
            "COSTO TOTAL": "costo_total",
            "COSTO DIFERENCIA ": "costo_diferencia"
        }
        
        # Preparar registros
        records = []
        for _, row in df.iterrows():
            record = {}
            for excel_col, db_col in column_mapping.items():
                value = row.get(excel_col)
                
                # Convertir NaN a None
                if pd.isna(value):
                    value = None
                elif isinstance(value, str):
                    value = fix_encoding(value.strip())
                
                record[db_col] = value
            
            # Calcular DESVIACION = (costo_diferencia / costo_total) * 100
            costo_total = record.get("costo_total", 0) or 0
            costo_diferencia = record.get("costo_diferencia", 0) or 0
            
            if costo_total != 0:
                record["desviacion"] = (costo_diferencia / costo_total) * 100
            else:
                record["desviacion"] = 0
            
            records.append(record)
        
        # Insertar en BD
        with get_db() as conn:
            cursor = conn.cursor()
            for record in records:
                cursor.execute('''
                    INSERT INTO brigadas 
                    (mes, sede, item_codigo, descripcion, tercero_identificacion,
                     tercero_nombre, neto, conteo, reconteo, diferencia,
                     estado, costo_unit, costo_total, costo_diferencia, desviacion)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    record["mes"],
                    record["sede"],
                    record["item_codigo"],
                    record["descripcion"],
                    record["tercero_identificacion"],
                    record["tercero_nombre"],
                    record["neto"],
                    record["conteo"],
                    record["reconteo"],
                    record["diferencia"],
                    record["estado"],
                    record["costo_unit"],
                    record["costo_total"],
                    record["costo_diferencia"],
                    record["desviacion"]
                ))
            conn.commit()
        
        print(f"✅ Brigadas: {len(records)} registros importados")
        return len(records)
        
    except Exception as e:
        print(f"❌ Error importando Brigadas: {e}")
        import traceback
        traceback.print_exc()
        raise


def import_errores():
    """Importar datos de Errores Movimientos"""
    config = EXCEL_FILES["errores"]
    print(f"📂 Leyendo {config['path']} - Hoja: {config['sheet']}...")
    
    try:
        df = pd.read_excel(config["path"], sheet_name=config["sheet"])
        print(f"   Registros encontrados: {len(df)}")
        
        # Limpiar tabla
        clear_table("errores")
        
        # Mapeo de meses abreviados a nombres completos en español
        meses_map = {
            'jan': 'ENERO', 'feb': 'FEBRERO', 'mar': 'MARZO', 'apr': 'ABRIL',
            'may': 'MAYO', 'jun': 'JUNIO', 'jul': 'JULIO', 'aug': 'AGOSTO',
            'sep': 'SEPTIEMBRE', 'oct': 'OCTUBRE', 'nov': 'NOVIEMBRE', 'dec': 'DICIEMBRE'
        }
        
        # Extraer mes de la fecha y transformar
        df['mes_abrev'] = df['Fecha'].dt.strftime('%b').str.lower()  # jun, jul
        df['mes'] = df['mes_abrev'].map(meses_map)
        
        # Transformar Zona a mayúsculas para coincidir con otras tablas
        df['sede'] = df['Zona'].str.upper()
        
        # Preparar registros
        records = []
        for _, row in df.iterrows():
            record = {
                "mes": row.get('mes'),
                "sede": row.get('sede'),
                "error": row.get('Error'),
                "bodega": row.get('Bodega'),
                "doc": row.get('DOC'),
                "fecha": row.get('Fecha').strftime('%Y-%m-%d') if pd.notna(row.get('Fecha')) else None,
                "tipo_numero": row.get('Tipo numero'),
                "codigo": row.get('Codigo'),
                "descripcion": row.get('Descripcion'),
                "tercero": row.get('Tercero'),
                "nombre": row.get('Nombre'),
                "cantidad": row.get('Cantidad'),
                "costo": row.get('Costo'),
                "total": row.get('Total'),
                "cuenta_doc": row.get('Codigo6'),
                "nombre_cuenta": row.get('Nombre7'),
                "observaciones": row.get('OBS')
            }
            
            # Convertir NaN a None
            for key, value in record.items():
                if pd.isna(value):
                    record[key] = None
                elif isinstance(value, str):
                    record[key] = fix_encoding(value.strip())
            
            records.append(record)
        
        # Insertar en BD
        with get_db() as conn:
            cursor = conn.cursor()
            for record in records:
                cursor.execute('''
                    INSERT INTO errores 
                    (mes, sede, error, bodega, doc, fecha, tipo_numero, codigo,
                     descripcion, tercero, nombre, cantidad, costo, total,
                     cuenta_doc, nombre_cuenta, observaciones)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    record["mes"],
                    record["sede"],
                    record["error"],
                    record["bodega"],
                    record["doc"],
                    record["fecha"],
                    record["tipo_numero"],
                    record["codigo"],
                    record["descripcion"],
                    record["tercero"],
                    record["nombre"],
                    record["cantidad"],
                    record["costo"],
                    record["total"],
                    record["cuenta_doc"],
                    record["nombre_cuenta"],
                    record["observaciones"]
                ))
            conn.commit()
        
        print(f"✅ Errores: {len(records)} registros importados")
        return len(records)
        
    except Exception as e:
        print(f"❌ Error importando Errores: {e}")
        import traceback
        traceback.print_exc()
        raise


def import_programados_ejecutados():
    """Importar datos de Programados vs Ejecutados"""
    config = EXCEL_FILES["programados_ejecutados"]
    print(f"📂 Leyendo {config['path']} - Hoja: {config['sheet']}...")
    
    try:
        df = pd.read_excel(config["path"], sheet_name=config["sheet"])
        print(f"   Registros encontrados: {len(df)}")
        
        # Limpiar tabla
        clear_table("programados_ejecutados")
        
        # Corregir typo en mes JUNIIO -> JUNIO
        df['FECHA PROPUESTA'] = df['FECHA PROPUESTA'].str.replace('JUNIIO', 'JUNIO')
        
        # Preparar registros
        records = []
        for _, row in df.iterrows():
            # Limpiar tipo inventario (tiene espacios al final)
            tipo_inv = row.get('TIPO INVENTARIO ')
            if pd.notna(tipo_inv):
                tipo_inv = tipo_inv.strip()
            
            record = {
                "mes": row.get('FECHA PROPUESTA'),
                "sede": row.get('SEDE'),
                "tipo_inventario": tipo_inv,
                "programados": row.get('PROGRAMADOS'),
                "ejecutados": row.get('EJECUTADOS'),
                "indicador_programacion": row.get('Indicador Programacion')
            }
            
            # Convertir NaN a None
            for key, value in record.items():
                if pd.isna(value):
                    record[key] = None
                elif isinstance(value, str):
                    record[key] = fix_encoding(value.strip())
            
            records.append(record)
        
        # Insertar en BD
        with get_db() as conn:
            cursor = conn.cursor()
            for record in records:
                cursor.execute('''
                    INSERT INTO programados_ejecutados 
                    (mes, sede, tipo_inventario, programados, ejecutados, indicador_programacion)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    record["mes"],
                    record["sede"],
                    record["tipo_inventario"],
                    record["programados"],
                    record["ejecutados"],
                    record["indicador_programacion"]
                ))
            conn.commit()
        
        print(f"✅ Programados vs Ejecutados: {len(records)} registros importados")
        return len(records)
        
    except Exception as e:
        print(f"❌ Error importando Programados vs Ejecutados: {e}")
        import traceback
        traceback.print_exc()
        raise


def import_gestion():
    """Importar datos de Gestión Proceso"""
    config = EXCEL_FILES["gestion"]
    print(f"📂 Leyendo {config['path']}, hoja: {config['sheet']}...")
    
    try:
        df = pd.read_excel(config["path"], sheet_name=config["sheet"])
        print(f"   Registros encontrados: {len(df)}")
        
        # Limpiar espacios en nombres de columnas
        df.columns = df.columns.str.strip()
        
        # Limpiar tabla
        clear_table("gestion")
        
        # Limpiar y transformar datos
        for col in df.select_dtypes(include=['object']).columns:
            if col in df.columns:
                df[col] = df[col].str.strip() if hasattr(df[col], 'str') else df[col]
        
        # Convertir DIAS y DIAS RESPUESTA a numérico (reemplazar '-' por None)
        df['DIAS'] = pd.to_numeric(df['DIAS'], errors='coerce')
        df['DIAS RESPUESTA'] = pd.to_numeric(df['DIAS RESPUESTA'], errors='coerce')
        
        # Convertir fechas a string formato ISO
        df['Fecha Ejecución Invetario'] = pd.to_datetime(df['Fecha Ejecución Invetario'], errors='coerce').dt.strftime('%Y-%m-%d')
        df['Fecha Reporte Operaciones'] = pd.to_datetime(df['Fecha Reporte Operaciones'], errors='coerce').dt.strftime('%Y-%m-%d')
        df['FECHA RESPUESTA'] = pd.to_datetime(df['FECHA RESPUESTA'], errors='coerce').dt.strftime('%Y-%m-%d')
        
        # Preparar registros
        records = []
        for _, row in df.iterrows():
            records.append({
                "mes": row.get("MES"),
                "sede": row.get("SEDE"),
                "tipo_inventario": row.get("TIPO INVENTARIO"),
                "almacenista": row.get("ALMACENISTA"),
                "fecha_ejecucion_inventario": row.get("Fecha Ejecución Invetario") if pd.notna(row.get("Fecha Ejecución Invetario")) else None,
                "fecha_reporte_operaciones": row.get("Fecha Reporte Operaciones") if pd.notna(row.get("Fecha Reporte Operaciones")) else None,
                "dias": int(row.get("DIAS")) if pd.notna(row.get("DIAS")) else None,
                "indicador_inventario": row.get("Indicador Inventario"),
                "area": row.get("AREA"),
                "responsable": row.get("RESPONSABLE"),
                "fecha_respuesta": row.get("FECHA RESPUESTA") if pd.notna(row.get("FECHA RESPUESTA")) else None,
                "dias_respuesta": int(row.get("DIAS RESPUESTA")) if pd.notna(row.get("DIAS RESPUESTA")) else None,
                "indicador_respuesta": row.get("Indicador respuesta")
            })
        
        # Insertar en BD
        with get_db() as conn:
            cursor = conn.cursor()
            for record in records:
                cursor.execute('''
                    INSERT INTO gestion (
                        mes, sede, tipo_inventario, almacenista,
                        fecha_ejecucion_inventario, fecha_reporte_operaciones,
                        dias, indicador_inventario, area, responsable,
                        fecha_respuesta, dias_respuesta, indicador_respuesta
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    record["mes"],
                    record["sede"],
                    record["tipo_inventario"],
                    record["almacenista"],
                    record["fecha_ejecucion_inventario"],
                    record["fecha_reporte_operaciones"],
                    record["dias"],
                    record["indicador_inventario"],
                    record["area"],
                    record["responsable"],
                    record["fecha_respuesta"],
                    record["dias_respuesta"],
                    record["indicador_respuesta"]
                ))
            conn.commit()
        
        print(f"✅ Gestión Proceso: {len(records)} registros importados")
        return len(records)
        
    except Exception as e:
        print(f"❌ Error importando Gestión Proceso: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
