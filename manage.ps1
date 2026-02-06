# Script de gestión para Logística HESEGO (PowerShell)
# Uso: .\manage.ps1 [comando]

param(
    [Parameter(Position=0)]
    [string]$Command = "help",
    
    [Parameter(Position=1)]
    [string]$Arg1 = "",
    
    [Parameter(Position=2)]
    [string]$Arg2 = ""
)

# Funciones de colores
function Print-Header {
    param([string]$Message)
    Write-Host "`n========================================" -ForegroundColor Blue
    Write-Host $Message -ForegroundColor Blue
    Write-Host "========================================`n" -ForegroundColor Blue
}

function Print-Success {
    param([string]$Message)
    Write-Host "✅ $Message" -ForegroundColor Green
}

function Print-Error {
    param([string]$Message)
    Write-Host "❌ $Message" -ForegroundColor Red
}

function Print-Warning {
    param([string]$Message)
    Write-Host "⚠️  $Message" -ForegroundColor Yellow
}

function Print-Info {
    param([string]$Message)
    Write-Host "ℹ️  $Message" -ForegroundColor Cyan
}

# Verificar requisitos
function Check-Requirements {
    Print-Header "Verificando requisitos"
    
    # Verificar Docker
    if (!(Get-Command docker -ErrorAction SilentlyContinue)) {
        Print-Error "Docker no está instalado"
        exit 1
    }
    Print-Success "Docker instalado"
    
    # Verificar Docker Compose
    if (!(Get-Command docker-compose -ErrorAction SilentlyContinue)) {
        Print-Error "Docker Compose no está instalado"
        exit 1
    }
    Print-Success "Docker Compose instalado"
    
    # Verificar red web
    $networkExists = docker network ls --filter name=web --format "{{.Name}}" 2>$null
    if (!$networkExists) {
        Print-Warning "Red 'web' no existe, creando..."
        docker network create web
        Print-Success "Red 'web' creada"
    } else {
        Print-Success "Red 'web' existe"
    }
    
    # Verificar archivo .env
    if (!(Test-Path .env)) {
        Print-Warning "Archivo .env no existe, creando desde .env.example..."
        Copy-Item .env.example .env
        Print-Warning "Por favor, edita .env y configura las contraseñas"
        exit 1
    }
    Print-Success "Archivo .env existe"
}

# Comandos
function Start-Services {
    Print-Header "Iniciando servicios"
    docker-compose up -d
    Print-Success "Servicios iniciados"
    Show-Status
}

function Stop-Services {
    Print-Header "Deteniendo servicios"
    docker-compose down
    Print-Success "Servicios detenidos"
}

function Restart-Services {
    Print-Header "Reiniciando servicios"
    docker-compose restart
    Print-Success "Servicios reiniciados"
}

function Build-Images {
    Print-Header "Construyendo imágenes"
    docker-compose build --no-cache
    Print-Success "Imágenes construidas"
}

function Rebuild-All {
    Print-Header "Reconstruyendo e iniciando servicios"
    docker-compose down
    docker-compose build --no-cache
    docker-compose up -d
    Print-Success "Servicios reconstruidos e iniciados"
    Show-Status
}

function Show-Logs {
    param([string]$Service = "")
    
    if ($Service) {
        docker-compose logs -f $Service
    } else {
        docker-compose logs -f
    }
}

function Show-Status {
    Print-Header "Estado de servicios"
    docker-compose ps
    
    Write-Host ""
    Print-Info "URLs de acceso:"
    Write-Host "  Frontend: http://164.68.118.86:8085 o http://localhost:8085"
    Write-Host "  Backend API: http://localhost:8000/api/"
    Write-Host "  API Docs: http://localhost:8000/api/docs"
    Write-Host ""
}

function Open-Shell {
    param([string]$Service = "backend")
    
    Print-Header "Shell en contenedor: $Service"
    docker-compose exec $Service bash
}

function Migrate-Data {
    Print-Header "Migrar datos SQLite → PostgreSQL"
    
    if (!(Test-Path "backend\logistica.db")) {
        Print-Error "No se encontró backend\logistica.db"
        exit 1
    }
    
    Print-Info "Verificando que PostgreSQL esté corriendo..."
    $pgStatus = docker-compose ps postgres | Select-String "Up"
    if (!$pgStatus) {
        Print-Error "PostgreSQL no está corriendo. Ejecuta: .\manage.ps1 start"
        exit 1
    }
    
    python migrate_to_postgres.py
}

function Import-Data {
    Print-Header "Importar datos desde Excel"
    
    $backendStatus = docker-compose ps backend | Select-String "Up"
    if (!$backendStatus) {
        Print-Error "Backend no está corriendo. Ejecuta: .\manage.ps1 start"
        exit 1
    }
    
    docker-compose exec backend python -m backend.import_data
}

function Backup-Database {
    Print-Header "Crear backup de PostgreSQL"
    
    $backupFile = "backup_$(Get-Date -Format 'yyyyMMdd_HHmmss').sql"
    
    docker-compose exec postgres pg_dump -U logistica_user logistica_hesego | Out-File -FilePath $backupFile -Encoding UTF8
    
    Print-Success "Backup creado: $backupFile"
}

function Restore-Database {
    param([string]$BackupFile)
    
    if (!$BackupFile) {
        Print-Error "Uso: .\manage.ps1 restore <archivo_backup.sql>"
        exit 1
    }
    
    if (!(Test-Path $BackupFile)) {
        Print-Error "Archivo no encontrado: $BackupFile"
        exit 1
    }
    
    Print-Header "Restaurar backup de PostgreSQL"
    Print-Warning "Esto sobrescribirá los datos actuales"
    
    $response = Read-Host "¿Continuar? (s/n)"
    if ($response -notmatch "^[SsYy]$") {
        Print-Info "Operación cancelada"
        exit 0
    }
    
    Get-Content $BackupFile | docker-compose exec -T postgres psql -U logistica_user -d logistica_hesego
    Print-Success "Backup restaurado"
}

function Clear-Cache {
    Print-Header "Limpiar caché Redis"
    docker-compose exec redis redis-cli FLUSHALL
    Print-Success "Caché limpiado"
}

function Clean-All {
    Print-Header "Limpieza completa"
    Print-Warning "Esto eliminará todos los contenedores y volúmenes"
    
    $response = Read-Host "¿Continuar? (s/n)"
    if ($response -notmatch "^[SsYy]$") {
        Print-Info "Operación cancelada"
        exit 0
    }
    
    docker-compose down -v
    Print-Success "Limpieza completada"
}

function Check-Health {
    Print-Header "Health Checks"
    
    Print-Info "Backend API:"
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:8000/api/health"
        $response | ConvertTo-Json
    } catch {
        Print-Error "Backend no responde"
    }
    
    Write-Host ""
    Print-Info "Frontend:"
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8085/health" -UseBasicParsing
        Write-Host "Status: $($response.StatusCode)"
    } catch {
        Print-Error "Frontend no responde"
    }
    
    Write-Host ""
    Print-Info "Estado de contenedores:"
    docker-compose ps
}

function Show-Help {
    @"
🚀 Gestión de Logística HESEGO

Uso: .\manage.ps1 [comando] [argumentos]

Comandos disponibles:

  Gestión de servicios:
    start              Iniciar todos los servicios
    stop               Detener todos los servicios
    restart            Reiniciar todos los servicios
    status             Ver estado de servicios
    build              Construir imágenes Docker
    rebuild            Reconstruir e iniciar servicios

  Logs y debugging:
    logs [servicio]    Ver logs (todos o de un servicio específico)
    shell [servicio]   Abrir shell en contenedor (default: backend)
    health             Verificar health checks

  Base de datos:
    migrate            Migrar datos de SQLite a PostgreSQL
    import             Importar datos desde archivos Excel
    backup             Crear backup de PostgreSQL
    restore <archivo>  Restaurar backup de PostgreSQL

  Mantenimiento:
    clear-cache        Limpiar caché Redis
    clean              Limpieza completa (elimina volúmenes)

  Ayuda:
    help               Mostrar esta ayuda

Ejemplos:
  .\manage.ps1 start
  .\manage.ps1 logs backend
  .\manage.ps1 shell postgres
  .\manage.ps1 backup
  .\manage.ps1 restore backup_20260206.sql

"@
}

# Main
switch ($Command.ToLower()) {
    "start" {
        Check-Requirements
        Start-Services
    }
    "stop" {
        Stop-Services
    }
    "restart" {
        Restart-Services
    }
    "build" {
        Build-Images
    }
    "rebuild" {
        Check-Requirements
        Rebuild-All
    }
    "logs" {
        Show-Logs -Service $Arg1
    }
    "status" {
        Show-Status
    }
    "shell" {
        $service = if ($Arg1) { $Arg1 } else { "backend" }
        Open-Shell -Service $service
    }
    "migrate" {
        Migrate-Data
    }
    "import" {
        Import-Data
    }
    "backup" {
        Backup-Database
    }
    "restore" {
        Restore-Database -BackupFile $Arg1
    }
    "clear-cache" {
        Clear-Cache
    }
    "clean" {
        Clean-All
    }
    "health" {
        Check-Health
    }
    "help" {
        Show-Help
    }
    default {
        Print-Error "Comando desconocido: $Command"
        Write-Host ""
        Show-Help
        exit 1
    }
}
