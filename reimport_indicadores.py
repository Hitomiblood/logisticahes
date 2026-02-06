from backend.import_data import import_indicadores_almacenes

print("Reimportando datos de indicadores almacenes...")
try:
    import_indicadores_almacenes()
    print("✅ Datos reimportados exitosamente")
except Exception as e:
    print(f"❌ Error: {e}")
