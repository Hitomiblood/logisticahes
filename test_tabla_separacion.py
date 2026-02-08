"""Test de separación de tablas para Dashboard Operativo"""
import sys
from pathlib import Path

# Agregar backend al path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from backend.database import init_db, get_db
from backend.config import DATA_DIR, EXCEL_FILES, DB_TYPE

if __name__ == "__main__":
    print("=" * 80)
    print("TEST DE SEPARACIÓN DE TABLAS")
    print("=" * 80)
    print(f"Tipo de BD: {DB_TYPE}")
    print(f"DATA_DIR: {DATA_DIR}")
    print()
    
    # Inicializar BD (crea las tablas si no existen)
    print("🔧 Inicializando base de datos...")
    init_db()
    print("✅ Base de datos inicializada")
    print()
    
    # Verificar que las nuevas tablas existan
    with get_db() as conn:
        cursor = conn.cursor()
        
        print("📊 Verificando tablas existentes:")
        print()
        
        # Tablas de compras.html (original)
        print("🔹 TABLAS PARA COMPRAS.HTML (archivo único):")
        for table in ["traza_req_oc", "oc_descuentos", "base_oc_generadas"]:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"   ✅ {table}: {count:,} registros")
            except Exception as e:
                print(f"   ❌ {table}: Error - {e}")
        
        print()
        print("🔹 TABLAS PARA DASHBOARD_OPERATIVO.HTML (carpetas consolidadas):")
        for table in ["dashboard_traza_req_oc", "dashboard_oc_descuentos"]:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"   ✅ {table}: {count:,} registros")
            except Exception as e:
                print(f"   ❌ {table}: Error - {e}")
    
    print()
    print("=" * 80)
    print("✅ VERIFICACIÓN COMPLETADA")
    print("=" * 80)
    print()
    print("💡 NOTAS:")
    print("   - compras.html usa: traza_req_oc, oc_descuentos, base_oc_generadas")
    print("   - dashboard_operativo.html usa: dashboard_traza_req_oc, dashboard_oc_descuentos")
    print("   - Ambos dashboards pueden coexistir sin conflictos")
    print("=" * 80)
