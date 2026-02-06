import sqlite3

conn = sqlite3.connect('backend/logistica.db')
cursor = conn.cursor()

# Simular la query del endpoint
query = '''
    SELECT 
        sede,
        COALESCE(SUM(costo_total), 0) as costo_total,
        COALESCE(SUM(costo_diferencia), 0) as costo_diferencia,
        COALESCE(AVG(diferencia), 0) as diferencia
    FROM brigadas
    WHERE 1=1
    GROUP BY sede
    ORDER BY sede
'''

print("Resultados del endpoint brigadas por sede:")
rows = cursor.execute(query).fetchall()
for row in rows:
    print(f"Sede: {row[0]}, Costo Total: {row[1]:,.2f}, Costo Dif: {row[2]:,.2f}, Diferencia: {row[3]:.2f}")

print(f"\nTotal de sedes: {len(rows)}")

# Simular el formato de retorno
result = {
    "sedes": [row[0] for row in rows],
    "costo_total": [row[1] for row in rows],
    "costo_diferencia": [row[2] for row in rows],
    "diferencia": [row[3] for row in rows]
}

print(f"\nFormato de respuesta:")
print(f"  sedes: {result['sedes']}")
print(f"  costo_total: {result['costo_total']}")
print(f"  costo_diferencia: {result['costo_diferencia']}")

conn.close()
