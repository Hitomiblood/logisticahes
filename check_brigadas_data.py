import sqlite3

conn = sqlite3.connect('backend/logistica.db')
cursor = conn.cursor()

# Verificar datos de brigadas
print("Total registros brigadas:", cursor.execute('SELECT COUNT(*) FROM brigadas').fetchone()[0])

# Ver columnas
print("\nColumnas de la tabla brigadas:")
cursor.execute("PRAGMA table_info(brigadas)")
for col in cursor.fetchall():
    print(f"  {col[1]} ({col[2]})")

# Ver primeros registros
print("\nPrimeros 3 registros:")
for row in cursor.execute("SELECT sede, mes, tercero_nombre, estado FROM brigadas LIMIT 3").fetchall():
    print(row)

# Ver sedes únicas
print("\nSedes disponibles:")
for row in cursor.execute("SELECT DISTINCT sede FROM brigadas ORDER BY sede").fetchall():
    print(f"  {row[0]}")

conn.close()
