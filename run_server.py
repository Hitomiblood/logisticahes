"""
Script para ejecutar el servidor API de Logística HESEGO
"""
import uvicorn
from backend.config import API_HOST, API_PORT

if __name__ == "__main__":
    print("=" * 50)
    print("🚀 Iniciando API Logística HESEGO")
    print(f"   Servidor en: http://localhost:{API_PORT}")
    print("=" * 50)
    
    uvicorn.run(
        "backend.api:app",
        host=API_HOST,
        port=API_PORT,
        reload=True
    )
