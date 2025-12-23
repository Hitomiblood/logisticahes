import pandas as pd
from pathlib import Path

excel_path = Path("data/ALMACENES/INDICADORES 2025.xlsx")
df = pd.read_excel(excel_path, sheet_name="ERRORES ")

print("Columnas encontradas:")
for c in df.columns:
    print(f"  {repr(c)}")

print(f"\nTotal registros: {len(df)}")
print(f"\nZONAS únicas: {df['Zona'].unique() if 'Zona' in df.columns else 'No existe columna Zona'}")
print(f"\nMeses únicos: {df.columns[1:] if len(df.columns) > 1 else 'Verificar columnas'}")

print("\nPrimeras 5 filas:")
print(df.head())

print("\nInformación de columnas:")
print(df.info())
