import sqlite3
conn = sqlite3.connect('/app/backend/logistica.db')
cursor = conn.cursor()
try:
    cursor.execute('ALTER TABLE indicadores ADD COLUMN estado TEXT')
    conn.commit()
    print('Columna estado agregada exitosamente')
except sqlite3.OperationalError as e:
    if 'duplicate column name' in str(e):
        print('La columna estado ya existe')
    else:
        print(f'Error: {e}')
conn.close()
