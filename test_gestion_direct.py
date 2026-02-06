import sqlite3

conn = sqlite3.connect('backend/logistica.db')
cursor = conn.cursor()

# Simular la query del endpoint
query = """
    SELECT 
        sede,
        SUM(CASE WHEN indicador_inventario = 'Dentro del plazo' THEN 1 ELSE 0 END) as dentro_plazo,
        SUM(CASE WHEN indicador_inventario = 'Fuera del plazo' THEN 1 ELSE 0 END) as fuera_plazo,
        AVG(dias) as promedio_dias,
        COUNT(*) as total
    FROM gestion
    GROUP BY sede
    ORDER BY sede
"""

print("Resultados de la query:")
rows = cursor.execute(query).fetchall()
for row in rows:
    print(f"Sede: {row[0]}, Dentro: {row[1]}, Fuera: {row[2]}, Promedio días: {row[3]:.2f}, Total: {row[4]}")

print(f"\nTotal de sedes: {len(rows)}")

# Verificar valores únicos de indicador_inventario
print("\nValores de indicador_inventario:")
cursor.execute("SELECT DISTINCT indicador_inventario FROM gestion")
for val in cursor.fetchall():
    print(f"  '{val[0]}'")

conn.close()
