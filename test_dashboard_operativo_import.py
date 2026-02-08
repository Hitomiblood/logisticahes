"""Test de importación de datos del Dashboard Operativo"""
import sys
from pathlib import Path

# Agregar backend al path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from config import DATA_DIR, EXCEL_FILES
from import_data import import_dashboard_operativo

if __name__ == "__main__":
    print("=" * 80)
    print("TEST DE IMPORTACIÓN - DASHBOARD OPERATIVO")
    print("=" * 80)
    print(f"DATA_DIR: {DATA_DIR}")
    print(f"OC_DESCUENTOS: {EXCEL_FILES['dashboard_operativo']['oc_descuentos_folder']}")
    print(f"TRAZA_RQ_OC: {EXCEL_FILES['dashboard_operativo']['traza_rq_oc_folder']}")
    print("=" * 80)
    
    try:
        total = import_dashboard_operativo()
        print("\n" + "=" * 80)
        print(f"✅ IMPORTACIÓN COMPLETADA: {total:,} registros totales")
        print("=" * 80)
    except Exception as e:
        print("\n" + "=" * 80)
        print(f"❌ ERROR EN LA IMPORTACIÓN: {e}")
        print("=" * 80)
        import traceback
        traceback.print_exc()
        sys.exit(1)
