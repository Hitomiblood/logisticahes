import sqlite3
conn = sqlite3.connect("/app/backend/logistica.db")
cur = conn.cursor()

# Ver rango de fechas en traza_req_oc
print("=== TRAZA_REQ_OC ===")
cur.execute("SELECT MIN(oc_fecha), MAX(oc_fecha), COUNT(*) FROM traza_req_oc WHERE oc_fecha IS NOT NULL")
row = cur.fetchone()
print(f"Rango fechas OC: {row[0]} a {row[1]}")
print(f"Total registros con oc_fecha: {row[2]}")

# Ver rango de fechas en oc_descuentos  
print("\n=== OC_DESCUENTOS ===")
cur.execute("SELECT MIN(fecha), MAX(fecha), COUNT(*) FROM oc_descuentos WHERE fecha IS NOT NULL")
row = cur.fetchone()
print(f"Rango fechas: {row[0]} a {row[1]}")
print(f"Total registros con fecha: {row[2]}")

# Ver distribución por proceso
print("\n=== DISTRIBUCIÓN POR PROCESO ===")
cur.execute("SELECT proceso, COUNT(*) FROM oc_descuentos GROUP BY proceso ORDER BY COUNT(*) DESC")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]:,} registros")

# Ver algunos registros recientes
print("\n=== ÚLTIMOS 5 REGISTROS EN TRAZA ===")
cur.execute("SELECT oc_fecha, oc_tipo, oc_numero FROM traza_req_oc WHERE oc_fecha IS NOT NULL ORDER BY oc_fecha DESC LIMIT 5")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]}-{row[2]}")
