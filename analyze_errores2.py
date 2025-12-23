import pandas as pd
from pathlib import Path

excel_path = Path("data/ALMACENES/INDICADORES 2025.xlsx")
df = pd.read_excel(excel_path, sheet_name="ERRORES ")

# Extraer mes de la fecha
df['mes'] = df['Fecha'].dt.strftime('%b').str.lower()  # jun, jul, etc
df['mes_nombre'] = df['Fecha'].dt.month_name()  # June, July

print("Meses extraídos (abreviado):", df['mes'].unique())
print("Meses extraídos (nombre completo):", df['mes_nombre'].unique())

# Verificar Errores únicos
print("\nErrores únicos:", df['Error'].unique())

# Verificar Zonas (en minúsculas)
print("\nZonas en datos:", df['Zona'].unique())

# Conversión a mayúsculas
df['sede'] = df['Zona'].str.upper()
print("\nSedes transformadas:", df['sede'].unique())

# Contar por Error
print("\nConteo por Error:")
print(df['Error'].value_counts())

# Contar por mes
print("\nConteo por mes:")
print(df['mes'].value_counts())
