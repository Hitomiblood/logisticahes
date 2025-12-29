import sqlite3
from contextlib import contextmanager
from .config import DB_PATH

def get_connection():
    """Obtener conexión a la base de datos"""
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

@contextmanager
def get_db():
    """Context manager para conexión a BD"""
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    """Inicializar tablas de la base de datos"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Tabla para Costos Mensuales
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS costos_mensuales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TEXT,
                catalogo TEXT,
                neto REAL,
                ciudad TEXT,
                proyecto TEXT,
                tercero TEXT,
                descripcion TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabla para Operatividad Vehículos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS operatividad_vehiculos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha_ejecucion TEXT,
                placa TEXT,
                tipo_vehiculo TEXT,
                sede TEXT,
                estado_vehiculo TEXT,
                brigada TEXT,
                conductor TEXT,
                contrato TEXT,
                gps TEXT,
                justificacion_no_salida TEXT,
                tipo_dano TEXT,
                dano_inoperatividad TEXT,
                motivo_inoperatividad TEXT,
                observacion_inoperatividad TEXT,
                tipo_mantenimiento TEXT,
                km_mantenimiento REAL,
                vehiculos_programados REAL,
                vehiculos_operativos REAL,
                dias_en_taller REAL,
                propietario TEXT,
                indicador REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # ========== TABLAS PARA COMPRAS ==========
        
        # Tabla para TRAZA REQ OC (Trazabilidad Requisición a OC)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS traza_req_oc (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                req_fecha_entrega TEXT,
                req_fecha TEXT,
                req_usuario TEXT,
                req_fecha_autorizada TEXT,
                req_usuario_autorizador TEXT,
                req_emp INTEGER,
                req_suc INTEGER,
                req_descripcion_tipo_doc TEXT,
                req_tipo TEXT,
                req_numero INTEGER,
                req_estado TEXT,
                item_codigo INTEGER,
                item_descripcion TEXT,
                cotizacion_tipo TEXT,
                cotizacion_numero INTEGER,
                oc_fecha TEXT,
                oc_usuario TEXT,
                oc_fecha_autorizacion TEXT,
                oc_usuario_autorizacion TEXT,
                oc_tipo TEXT,
                oc_numero INTEGER,
                oc_estado TEXT,
                oc_tercero_id TEXT,
                oc_tercero_suc INTEGER,
                oc_tercero_nombre TEXT,
                entrega_servicio_fecha TEXT,
                entrega_servicio_usuario TEXT,
                entrega_servicio_tipo TEXT,
                entrega_servicio_numero REAL,
                entrega_almacen_fecha TEXT,
                entrega_almacen_usuario TEXT,
                entrega_almacen_tipo TEXT,
                entrega_almacen_numero REAL,
                factura_compra_fecha TEXT,
                factura_compra_tipo TEXT,
                factura_compra_numero REAL,
                devolucion_compra_fecha TEXT,
                devolucion_compra_tipo TEXT,
                devolucion_compra_numero REAL,
                dias_aprobar_rq INTEGER,
                dias_generar_oc INTEGER,
                dias_aprobacion_oc INTEGER,
                dias_recepcion_servicio REAL,
                dias_entrada_almacen REAL,
                mes REAL,
                suma_rq INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabla para OC DESCUENTOS
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS oc_descuentos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TEXT,
                fecha_entrega TEXT,
                dias_entrega INTEGER,
                documento_emp TEXT,
                documento_suc INTEGER,
                documento_tipo TEXT,
                documento_num INTEGER,
                item_codigo INTEGER,
                item_descripcion TEXT,
                item_bodega REAL,
                item_cantidad REAL,
                talla TEXT,
                item_unidad TEXT,
                item_proyecto INTEGER,
                item_solicitante TEXT,
                item_fecha_requ TEXT,
                tercero_id TEXT,
                tercero_nombre TEXT,
                costo_unitario REAL,
                total_item REAL,
                tasa_dcto REAL,
                total_dcto REAL,
                subtotal REAL,
                tasa_iva REAL,
                total_iva REAL,
                total REAL,
                estado TEXT,
                moneda TEXT,
                observaciones TEXT,
                proceso TEXT,
                concatenado TEXT,
                porcentaje_descuento REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabla para BASE OC GENERADAS
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS base_oc_generadas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha TEXT,
                fecha_entrega TEXT,
                dias_entrega INTEGER,
                documento_emp INTEGER,
                documento_suc INTEGER,
                documento_tipo TEXT,
                documento_num INTEGER,
                item_codigo INTEGER,
                item_descripcion TEXT,
                item_bodega REAL,
                item_cantidad REAL,
                talla TEXT,
                item_unidad TEXT,
                item_proyecto INTEGER,
                item_solicitante TEXT,
                item_fecha_requ TEXT,
                tercero_id TEXT,
                tercero_nombre TEXT,
                costo_unitario REAL,
                total_item REAL,
                tasa_dcto REAL,
                total_dcto REAL,
                subtotal REAL,
                tasa_iva REAL,
                total_iva REAL,
                total REAL,
                estado TEXT,
                moneda TEXT,
                observaciones TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabla para Indicadores de Almacenes (OYMM)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS indicadores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mes TEXT,
                sede TEXT,
                responsable TEXT,
                codigo INTEGER,
                descripcion TEXT,
                inventario_inicial REAL,
                total_entregado REAL,
                total_consumos REAL,
                total_reintegros REAL,
                denuncio_fiscalia INTEGER,
                inventario_final REAL,
                diferencia REAL,
                precio_unidad REAL,
                precio_total REAL,
                costo_inventario_final REAL,
                costo_diferencia REAL,
                objetivo REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Índices para mejorar rendimiento
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_costos_fecha ON costos_mensuales(fecha)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_costos_catalogo ON costos_mensuales(catalogo)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_costos_ciudad ON costos_mensuales(ciudad)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_operatividad_fecha ON operatividad_vehiculos(fecha_ejecucion)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_operatividad_sede ON operatividad_vehiculos(sede)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_operatividad_estado ON operatividad_vehiculos(estado_vehiculo)')
        
        # Índices para compras
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_traza_oc_fecha ON traza_req_oc(oc_fecha)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_traza_req_estado ON traza_req_oc(req_estado)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_traza_oc_estado ON traza_req_oc(oc_estado)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_oc_desc_fecha ON oc_descuentos(fecha)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_oc_desc_proceso ON oc_descuentos(proceso)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_oc_desc_tercero ON oc_descuentos(tercero_nombre)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_base_oc_fecha ON base_oc_generadas(fecha)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_base_oc_estado ON base_oc_generadas(estado)')
        
        # Índices para indicadores
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_indicadores_mes ON indicadores(mes)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_indicadores_sede ON indicadores(sede)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_indicadores_responsable ON indicadores(responsable)')
        
        # Tabla para Fiscal RU
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS fiscal_ru (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mes TEXT,
                item TEXT,
                descripcion TEXT,
                bodega TEXT,
                sede TEXT,
                saldo_final REAL,
                costo_promedio REAL,
                costo_total REAL,
                inf_fisico REAL,
                diferencia REAL,
                estado TEXT,
                costo_diferencia REAL,
                unidad TEXT,
                clasificacion TEXT,
                descripcion3 TEXT,
                tipo_inventario TEXT,
                objetivo REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_fiscal_ru_mes ON fiscal_ru(mes)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_fiscal_ru_estado ON fiscal_ru(estado)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_fiscal_ru_tipo ON fiscal_ru(tipo_inventario)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_fiscal_ru_sede ON fiscal_ru(sede)')
        
        # Tabla para Brigadas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS brigadas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mes TEXT,
                sede TEXT,
                item_codigo INTEGER,
                descripcion TEXT,
                tercero_identificacion TEXT,
                tercero_nombre TEXT,
                neto REAL,
                conteo REAL,
                reconteo REAL,
                diferencia REAL,
                estado TEXT,
                costo_unit REAL,
                costo_total REAL,
                costo_diferencia REAL,
                desviacion REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_brigadas_mes ON brigadas(mes)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_brigadas_sede ON brigadas(sede)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_brigadas_estado ON brigadas(estado)')
        
        # Tabla para Errores Movimientos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS errores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mes TEXT,
                sede TEXT,
                error TEXT,
                bodega TEXT,
                doc TEXT,
                fecha TEXT,
                tipo_numero TEXT,
                codigo INTEGER,
                descripcion TEXT,
                tercero INTEGER,
                nombre TEXT,
                cantidad INTEGER,
                costo REAL,
                total REAL,
                cuenta_doc TEXT,
                nombre_cuenta TEXT,
                observaciones TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_errores_mes ON errores(mes)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_errores_sede ON errores(sede)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_errores_error ON errores(error)')
        
        # Tabla para Programados vs Ejecutados
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS programados_ejecutados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mes TEXT,
                sede TEXT,
                tipo_inventario TEXT,
                programados REAL,
                ejecutados REAL,
                indicador_programacion REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_prog_mes ON programados_ejecutados(mes)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_prog_sede ON programados_ejecutados(sede)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_prog_tipo ON programados_ejecutados(tipo_inventario)')
        
        # Tabla gestion (GESTION PROCESO)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS gestion (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mes TEXT,
                sede TEXT,
                tipo_inventario TEXT,
                almacenista TEXT,
                fecha_ejecucion_inventario DATE,
                fecha_reporte_operaciones DATE,
                dias INTEGER,
                indicador_inventario TEXT,
                area TEXT,
                responsable TEXT,
                fecha_respuesta DATE,
                dias_respuesta INTEGER,
                indicador_respuesta TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_gestion_mes ON gestion(mes)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_gestion_sede ON gestion(sede)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_gestion_tipo ON gestion(tipo_inventario)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_gestion_responsable ON gestion(responsable)')
        
        conn.commit()
        print("✅ Base de datos inicializada correctamente")

def clear_table(table_name: str):
    """Limpiar una tabla antes de reimportar"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f'DELETE FROM {table_name}')
        conn.commit()
        print(f"🗑️ Tabla {table_name} limpiada")
