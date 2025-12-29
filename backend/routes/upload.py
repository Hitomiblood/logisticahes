"""
Rutas para carga y gestión de archivos Excel
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import shutil
import os
from pathlib import Path
from datetime import datetime

from ..config import DATA_DIR, EXCEL_FILES
from ..database import init_db, get_db
from ..import_data import (
    import_costos_mensuales,
    import_operatividad_vehiculos,
    import_compras,
    import_indicadores_almacenes
)

router = APIRouter(prefix="/api/upload", tags=["upload"])


def get_file_info():
    """Obtener información de todos los archivos configurados"""
    files_info = []
    
    for key, config in EXCEL_FILES.items():
        file_path = config["path"]
        exists = file_path.exists()
        
        info = {
            "id": key,
            "name": file_path.name,
            "path": str(file_path.relative_to(DATA_DIR)),
            "exists": exists,
            "size": file_path.stat().st_size if exists else 0,
            "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat() if exists else None,
            "tablero": get_tablero_name(key)
        }
        files_info.append(info)
    
    return files_info


def get_tablero_name(key: str) -> str:
    """Obtener nombre del tablero según la key del archivo"""
    tableros = {
        "costos_mensuales": "Costos Mensuales",
        "operatividad_vehiculos": "Operatividad Vehículos",
        "compras": "Compras",
        "indicadores_almacenes": "Indicadores Almacenes"
    }
    return tableros.get(key, key)


def get_import_function(key: str):
    """Obtener la función de importación según la key"""
    functions = {
        "costos_mensuales": import_costos_mensuales,
        "operatividad_vehiculos": import_operatividad_vehiculos,
        "compras": import_compras,
        "indicadores_almacenes": import_indicadores_almacenes
    }
    return functions.get(key)


@router.get("/files")
async def list_files():
    """Listar todos los archivos configurados y su estado"""
    try:
        files = get_file_info()
        return {"files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/files/{file_id}")
async def get_file_status(file_id: str):
    """Obtener estado de un archivo específico"""
    if file_id not in EXCEL_FILES:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")
    
    config = EXCEL_FILES[file_id]
    file_path = config["path"]
    exists = file_path.exists()
    
    # Contar registros en las tablas asociadas
    records = {}
    with get_db() as conn:
        cursor = conn.cursor()
        
        if file_id == "costos_mensuales":
            try:
                cursor.execute("SELECT COUNT(*) FROM costos_mensuales")
                records["costos_mensuales"] = cursor.fetchone()[0]
            except:
                records["costos_mensuales"] = 0
                
        elif file_id == "operatividad_vehiculos":
            try:
                cursor.execute("SELECT COUNT(*) FROM operatividad_vehiculos")
                records["operatividad_vehiculos"] = cursor.fetchone()[0]
            except:
                records["operatividad_vehiculos"] = 0
                
        elif file_id == "compras":
            for table in ["traza_req_oc", "oc_descuentos", "base_oc_generadas"]:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    records[table] = cursor.fetchone()[0]
                except:
                    records[table] = 0
                    
        elif file_id == "indicadores_almacenes":
            for table in ["indicadores", "fiscal_ru", "brigadas", "errores", "programados_ejecutados", "gestion"]:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    records[table] = cursor.fetchone()[0]
                except:
                    records[table] = 0
    
    return {
        "id": file_id,
        "name": file_path.name,
        "exists": exists,
        "size": file_path.stat().st_size if exists else 0,
        "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat() if exists else None,
        "tablero": get_tablero_name(file_id),
        "records": records
    }


@router.post("/files/{file_id}")
async def upload_file(file_id: str, file: UploadFile = File(...)):
    """Subir y reemplazar un archivo Excel, luego reimportar datos"""
    if file_id not in EXCEL_FILES:
        raise HTTPException(status_code=404, detail="Tipo de archivo no válido")
    
    config = EXCEL_FILES[file_id]
    target_path = config["path"]
    
    # Validar extensión
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos Excel (.xlsx, .xls)")
    
    try:
        # Crear directorio si no existe
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Guardar el archivo
        with open(target_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Reimportar datos
        import_func = get_import_function(file_id)
        if import_func:
            try:
                import_func()
                import_status = "success"
                import_message = "Datos importados correctamente"
            except Exception as e:
                import_status = "error"
                import_message = f"Error al importar: {str(e)}"
        else:
            import_status = "skipped"
            import_message = "No hay función de importación definida"
        
        return {
            "success": True,
            "message": f"Archivo '{file.filename}' subido correctamente",
            "file_id": file_id,
            "tablero": get_tablero_name(file_id),
            "import_status": import_status,
            "import_message": import_message
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al guardar archivo: {str(e)}")


@router.post("/reimport/{file_id}")
async def reimport_data(file_id: str):
    """Reimportar datos de un archivo existente"""
    if file_id not in EXCEL_FILES:
        raise HTTPException(status_code=404, detail="Tipo de archivo no válido")
    
    config = EXCEL_FILES[file_id]
    file_path = config["path"]
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="El archivo no existe")
    
    import_func = get_import_function(file_id)
    if not import_func:
        raise HTTPException(status_code=400, detail="No hay función de importación definida")
    
    try:
        import_func()
        return {
            "success": True,
            "message": f"Datos reimportados correctamente para {get_tablero_name(file_id)}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al reimportar: {str(e)}")


@router.post("/reimport-all")
async def reimport_all():
    """Reimportar datos de todos los archivos"""
    results = {}
    
    for file_id in EXCEL_FILES.keys():
        config = EXCEL_FILES[file_id]
        file_path = config["path"]
        
        if not file_path.exists():
            results[file_id] = {"status": "skipped", "message": "Archivo no existe"}
            continue
        
        import_func = get_import_function(file_id)
        if not import_func:
            results[file_id] = {"status": "skipped", "message": "Sin función de importación"}
            continue
        
        try:
            import_func()
            results[file_id] = {"status": "success", "message": "Importado correctamente"}
        except Exception as e:
            results[file_id] = {"status": "error", "message": str(e)}
    
    return {"results": results}
