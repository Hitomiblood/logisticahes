# Script PowerShell para sincronizar datos al servidor Docker desde Windows
# Ejecutar desde tu máquina local después de descargar de SharePoint

param(
    [string]$Servidor = "usuario@tu-servidor.com",
    [string]$RutaRemota = "/opt/logisticahes/data",
    [string]$RutaLocal = ".\data"
)

Write-Host "========================================"  -ForegroundColor Cyan
Write-Host "📤 SINCRONIZANDO DATOS AL SERVIDOR"  -ForegroundColor Cyan
Write-Host "========================================"  -ForegroundColor Cyan
Write-Host "Fecha: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host ""

# 1. Verificar que existen archivos locales
if (-not (Test-Path $RutaLocal)) {
    Write-Host "❌ Error: No existe la carpeta $RutaLocal" -ForegroundColor Red
    Write-Host "   Ejecuta primero: python sharepoint_downloader.py"
    exit 1
}

# 2. Contar archivos
$Archivos = (Get-ChildItem -Path $RutaLocal -Recurse -File).Count
Write-Host "📁 Archivos a sincronizar: $Archivos" -ForegroundColor Green

# 3. Sincronizar al servidor usando SCP
Write-Host ""
Write-Host "📡 Subiendo al servidor..." -ForegroundColor Yellow

# Usar scp para subir (requiere OpenSSH instalado en Windows)
scp -r "$RutaLocal\*" "${Servidor}:${RutaRemota}/"

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ Sincronización completada" -ForegroundColor Green
    
    # 4. Reiniciar contenedor
    Write-Host ""
    Write-Host "🔄 Reiniciando contenedor Docker..." -ForegroundColor Yellow
    ssh $Servidor "cd /opt/logisticahes && docker-compose restart logisticahesego"
    
    Write-Host ""
    Write-Host "✅ ¡Listo! Los datos están actualizados en el servidor." -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "❌ Error en la sincronización" -ForegroundColor Red
    exit 1
}
