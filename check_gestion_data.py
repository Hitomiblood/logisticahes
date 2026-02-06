import sqlite3

conn = sqlite3.connect('backend/logistica.db')
cursor = conn.cursor()

# Verificar total de registros
total = cursor.execute('SELECT COUNT(*) FROM gestion').fetchone()[0]
print(f'Total registros gestion: {total}')

# Primeros 5 registros
print('\nPrimeros 5 registros:')
for row in cursor.execute('SELECT sede, mes, tipo_inventario, almacenista, dias, indicador_inventario FROM gestion LIMIT 5').fetchall():
    print(row)

# Verificar valores únicos de tipo_inventario
print('\nTipos de inventario:')
for row in cursor.execute('SELECT DISTINCT tipo_inventario FROM gestion').fetchall():
    print(row[0])

conn.close()
