"""Agregar columna año a la tabla indicadores"""
import sqlite3

# Conectar a la base de datos
conn = sqlite3.connect('/app/backend/logistica.db')
cursor = conn.cursor()

# Agregar columna año
try:
    cursor.execute('ALTER TABLE indicadores ADD COLUMN anio INTEGER')
    print('✅ Columna anio agregada exitosamente')
except Exception as e:
    print(f'⚠️ Error al agregar columna (puede que ya exista): {e}')

# Crear índice
try:
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_indicadores_anio ON indicadores(anio)')
    print('✅ Índice para anio creado exitosamente')
    conn.commit()
except Exception as e:
    print(f'❌ Error al crear índice: {e}')

conn.close()
print('✅ Proceso completado')
