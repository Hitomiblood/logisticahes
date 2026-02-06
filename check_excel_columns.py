"""Ver las columnas del Excel"""
import pandas as pd

df = pd.read_excel('/app/data/ALMACENES/INDICADORES 2025.xlsx', sheet_name='OYMM', nrows=2)
print('Columnas disponibles en OYMM:')
for col in df.columns:
    print(f'  - {col}')
