import pandas as pd

# Leer el archivo Excel
df = pd.read_excel("/data/ALMACENES/INDICADORES 2025.xlsx", sheet_name="OYMM")

print("Columnas disponibles:")
print(list(df.columns))

print("\n" + "="*50)
print("Primeras 10 filas de la columna ESTADO:")
print(df["ESTADO"].head(10))

print("\n" + "="*50)
print("Valores únicos de ESTADO:")
estados_unicos = df["ESTADO"].dropna().unique()
print(f"Total valores únicos: {len(estados_unicos)}")
print(estados_unicos)

print("\n" + "="*50)
print(f"Total de filas: {len(df)}")
print(f"Filas con ESTADO no nulo: {df['ESTADO'].notna().sum()}")
print(f"Filas con ESTADO nulo: {df['ESTADO'].isna().sum()}")
