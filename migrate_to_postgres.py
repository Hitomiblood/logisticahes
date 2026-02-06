"""
Script para migrar datos de SQLite a PostgreSQL
Ejecutar después de iniciar los servicios de Docker
"""
import sqlite3
import psycopg2
import psycopg2.extras
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración
BASE_DIR = Path(__file__).resolve().parent
SQLITE_DB = BASE_DIR / "backend" / "logistica.db"

# PostgreSQL - leer de .env o usar valores por defecto
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", 5433))  # Puerto mapeado en docker-compose
POSTGRES_USER = os.getenv("POSTGRES_USER", "logistica_user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "logistica_password_2026")
POSTGRES_DB = os.getenv("POSTGRES_DB", "logistica_hesego")

# Tablas a migrar
TABLES = [
    "costos_mensuales",
    "operatividad_vehiculos",
    "traza_req_oc",
    "oc_descuentos",
    "base_oc_generadas",
    "indicadores",
    "fiscal_ru",
    "brigadas",
    "errores",
    "programados_ejecutados",
    "gestion"
]


def connect_sqlite():
    """Conectar a SQLite"""
    if not SQLITE_DB.exists():
        print(f"❌ Base de datos SQLite no encontrada: {SQLITE_DB}")
        sys.exit(1)
    
    conn = sqlite3.connect(str(SQLITE_DB))
    conn.row_factory = sqlite3.Row
    return conn


def connect_postgres():
    """Conectar a PostgreSQL"""
    try:
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            database=POSTGRES_DB
        )
        return conn
    except psycopg2.Error as e:
        print(f"❌ Error conectando a PostgreSQL: {e}")
        print(f"\nVerificar que Docker esté corriendo:")
        print(f"  docker-compose ps")
        print(f"\nO configurar variables de entorno:")
        print(f"  POSTGRES_HOST={POSTGRES_HOST}")
        print(f"  POSTGRES_PORT={POSTGRES_PORT}")
        sys.exit(1)


def get_column_names(cursor, table):
    """Obtener nombres de columnas (excluyendo 'id' y 'created_at')"""
    cursor.execute(f"SELECT * FROM {table} LIMIT 0")
    columns = [desc[0] for desc in cursor.description]
    # Excluir id y created_at (se generan automáticamente)
    return [col for col in columns if col not in ['id', 'created_at']]


def migrate_table(sqlite_conn, pg_conn, table_name):
    """Migrar una tabla de SQLite a PostgreSQL"""
    print(f"\n📦 Migrando tabla: {table_name}")
    
    sqlite_cursor = sqlite_conn.cursor()
    pg_cursor = pg_conn.cursor()
    
    # Contar registros en SQLite
    sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    total_rows = sqlite_cursor.fetchone()[0]
    
    if total_rows == 0:
        print(f"   ⚠️ Tabla vacía, saltando...")
        return
    
    print(f"   Registros a migrar: {total_rows}")
    
    # Obtener columnas
    columns = get_column_names(sqlite_cursor, table_name)
    columns_str = ", ".join(columns)
    placeholders = ", ".join(["%s"] * len(columns))
    
    # Limpiar tabla de destino
    print(f"   🗑️ Limpiando tabla destino...")
    pg_cursor.execute(f"TRUNCATE TABLE {table_name} RESTART IDENTITY CASCADE")
    
    # Leer datos de SQLite
    print(f"   📖 Leyendo datos...")
    sqlite_cursor.execute(f"SELECT {columns_str} FROM {table_name}")
    rows = sqlite_cursor.fetchall()
    
    # Insertar en PostgreSQL en lotes
    print(f"   💾 Insertando datos...")
    batch_size = 1000
    inserted = 0
    
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i + batch_size]
        values = [tuple(row) for row in batch]
        
        insert_query = f"""
            INSERT INTO {table_name} ({columns_str})
            VALUES ({placeholders})
        """
        
        try:
            psycopg2.extras.execute_batch(pg_cursor, insert_query, values, page_size=batch_size)
            inserted += len(batch)
            print(f"   Progress: {inserted}/{total_rows} ({inserted*100//total_rows}%)", end='\r')
        except Exception as e:
            print(f"\n   ❌ Error insertando lote: {e}")
            print(f"   Primer registro del lote: {batch[0] if batch else 'N/A'}")
            raise
    
    pg_conn.commit()
    print(f"\n   ✅ Migrados {inserted} registros")


def main():
    """Función principal de migración"""
    print("=" * 60)
    print("🔄 MIGRACIÓN DE DATOS: SQLite → PostgreSQL")
    print("=" * 60)
    print(f"\nOrigen:  SQLite - {SQLITE_DB}")
    print(f"Destino: PostgreSQL - {POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}")
    print()
    
    # Confirmar
    response = input("¿Continuar con la migración? (s/n): ")
    if response.lower() not in ['s', 'si', 'y', 'yes']:
        print("❌ Migración cancelada")
        sys.exit(0)
    
    # Conectar a ambas bases de datos
    print("\n📡 Conectando a bases de datos...")
    sqlite_conn = connect_sqlite()
    pg_conn = connect_postgres()
    
    print("✅ Conexiones establecidas")
    
    # Migrar cada tabla
    migrated = 0
    failed = 0
    
    for table in TABLES:
        try:
            migrate_table(sqlite_conn, pg_conn, table)
            migrated += 1
        except Exception as e:
            print(f"\n❌ Error migrando tabla {table}: {e}")
            failed += 1
            continue
    
    # Cerrar conexiones
    sqlite_conn.close()
    pg_conn.close()
    
    # Resumen
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE MIGRACIÓN")
    print("=" * 60)
    print(f"✅ Tablas migradas exitosamente: {migrated}")
    print(f"❌ Tablas con errores: {failed}")
    print(f"📋 Total de tablas: {len(TABLES)}")
    
    if failed == 0:
        print("\n🎉 ¡Migración completada exitosamente!")
    else:
        print("\n⚠️ Migración completada con errores")
        sys.exit(1)


if __name__ == "__main__":
    main()
