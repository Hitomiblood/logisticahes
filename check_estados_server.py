import sqlite3

# Conectar a la base de datos
conn = sqlite3.connect('/app/backend/logistica.db')
cursor = conn.cursor()

# Ver cuántos registros hay
cursor.execute("SELECT COUNT(*) FROM indicadores")
total = cursor.fetchone()[0]
print(f"Total de registros en indicadores: {total}")

# Ver cuántos registros tienen estado no nulo
cursor.execute("SELECT COUNT(*) FROM indicadores WHERE estado IS NOT NULL")
con_estado = cursor.fetchone()[0]
print(f"Registros con estado no nulo: {con_estado}")

# Ver valores únicos de estado
cursor.execute("SELECT DISTINCT estado FROM indicadores WHERE estado IS NOT NULL ORDER BY estado")
estados = cursor.fetchall()
print(f"\nEstados únicos: {[e[0] for e in estados]}")

# Ver algunos ejemplos
cursor.execute("SELECT anio, mes, sede, responsable, estado FROM indicadores WHERE estado IS NOT NULL LIMIT 5")
print("\nEjemplos de registros con estado:")
for row in cursor.fetchall():
    print(f"  {row}")

conn.close()
