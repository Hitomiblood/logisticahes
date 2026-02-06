"""Ver valores de año en el Excel"""
import pandas as pd

df = pd.read_excel('/app/data/ALMACENES/INDICADORES 2025.xlsx', sheet_name='OYMM', nrows=10)
print('Primeras filas con columna AÑO:')
print(df[['AÑO', 'MES', 'SEDE']].head(10))
print('\nValores únicos de AÑO:', df['AÑO'].unique())
print('Tipo de dato de AÑO:', df['AÑO'].dtype)
