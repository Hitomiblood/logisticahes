"""Verificar que se importó el campo año"""
import sqlite3

conn = sqlite3.connect('/app/backend/logistica.db')
cursor = conn.cursor()

cursor.execute('SELECT DISTINCT anio FROM indicadores WHERE anio IS NOT NULL ORDER BY anio')
anios = [row[0] for row in cursor.fetchall()]
print(f'✅ Años disponibles: {anios}')

cursor.execute('SELECT COUNT(*) FROM indicadores WHERE anio IS NOT NULL')
total = cursor.fetchone()[0]
print(f'✅ Total de registros con año: {total}')

conn.close()
