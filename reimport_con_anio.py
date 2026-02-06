"""Reimportar datos para incluir el campo AÑO"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from backend.import_data import import_indicadores_almacenes

if __name__ == "__main__":
    print("🔄 Reimportando datos de indicadores con AÑO...")
    total = import_indicadores_almacenes()
    print(f"✅ Datos reimportados exitosamente: {total} registros totales")
