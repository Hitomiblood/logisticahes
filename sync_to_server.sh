#!/bin/bash
# Script para sincronizar archivos de SharePoint al servidor Docker
# Se ejecuta desde tu máquina local con acceso a SharePoint

# Configuración
SERVIDOR="usuario@tu-servidor.com"
RUTA_REMOTA="/opt/logisticahes/data"
RUTA_LOCAL="./data"

echo "========================================"
echo "📤 SINCRONIZANDO DATOS AL SERVIDOR"
echo "========================================"
echo "Fecha: $(date)"
echo ""

# 1. Verificar que existen archivos locales
if [ ! -d "$RUTA_LOCAL" ]; then
    echo "❌ Error: No existe la carpeta $RUTA_LOCAL"
    echo "   Ejecuta primero: python sharepoint_downloader.py"
    exit 1
fi

# 2. Contar archivos
ARCHIVOS=$(find "$RUTA_LOCAL" -type f | wc -l)
echo "📁 Archivos a sincronizar: $ARCHIVOS"

# 3. Sincronizar al servidor
echo ""
echo "📡 Subiendo al servidor..."
rsync -avz --progress "$RUTA_LOCAL/" "$SERVIDOR:$RUTA_REMOTA/"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Sincronización completada"
    
    # 4. Reiniciar contenedor para refrescar datos (opcional)
    echo ""
    echo "🔄 Reiniciando contenedor Docker..."
    ssh "$SERVIDOR" "cd /opt/logisticahes && docker-compose restart logisticahesego"
    
    echo ""
    echo "✅ ¡Listo! Los datos están actualizados en el servidor."
else
    echo ""
    echo "❌ Error en la sincronización"
    exit 1
fi
