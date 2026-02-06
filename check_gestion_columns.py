import sqlite3

conn = sqlite3.connect('backend/logistica.db')
cursor = conn.cursor()

# Ver columnas de la tabla gestion
print("Columnas de la tabla gestion:")
cursor.execute("PRAGMA table_info(gestion)")
for col in cursor.fetchall():
    print(f"  {col[1]} ({col[2]})")

# Ver un ejemplo de registro
print("\nEjemplo de registro:")
row = cursor.execute("SELECT * FROM gestion LIMIT 1").fetchone()
cursor.execute("PRAGMA table_info(gestion)")
columns = [col[1] for col in cursor.fetchall()]
for col, val in zip(columns, row):
    print(f"  {col}: {val}")

conn.close()
