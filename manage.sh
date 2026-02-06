#!/bin/bash

# Script de gestión para Logística HESEGO
# Uso: ./manage.sh [comando]

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funciones helper
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Verificar requisitos
check_requirements() {
    print_header "Verificando requisitos"
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker no está instalado"
        exit 1
    fi
    print_success "Docker instalado"
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose no está instalado"
        exit 1
    fi
    print_success "Docker Compose instalado"
    
    # Verificar red web
    if ! docker network inspect web &> /dev/null; then
        print_warning "Red 'web' no existe, creando..."
        docker network create web
        print_success "Red 'web' creada"
    else
        print_success "Red 'web' existe"
    fi
    
    # Verificar archivo .env
    if [ ! -f .env ]; then
        print_warning "Archivo .env no existe, creando desde .env.example..."
        cp .env.example .env
        print_warning "Por favor, edita .env y configura las contraseñas"
        exit 1
    fi
    print_success "Archivo .env existe"
}

# Comandos
cmd_start() {
    print_header "Iniciando servicios"
    docker-compose up -d
    print_success "Servicios iniciados"
    cmd_status
}

cmd_stop() {
    print_header "Deteniendo servicios"
    docker-compose down
    print_success "Servicios detenidos"
}

cmd_restart() {
    print_header "Reiniciando servicios"
    docker-compose restart
    print_success "Servicios reiniciados"
}

cmd_build() {
    print_header "Construyendo imágenes"
    docker-compose build --no-cache
    print_success "Imágenes construidas"
}

cmd_rebuild() {
    print_header "Reconstruyendo e iniciando servicios"
    docker-compose down
    docker-compose build --no-cache
    docker-compose up -d
    print_success "Servicios reconstruidos e iniciados"
    cmd_status
}

cmd_logs() {
    SERVICE=${1:-}
    if [ -z "$SERVICE" ]; then
        docker-compose logs -f
    else
        docker-compose logs -f "$SERVICE"
    fi
}

cmd_status() {
    print_header "Estado de servicios"
    docker-compose ps
    
    echo ""
    print_info "URLs de acceso:"
    echo "  Frontend: http://164.68.118.86:8085 o http://localhost:8085"
    echo "  Backend API: http://localhost:8000/api/"
    echo "  API Docs: http://localhost:8000/api/docs"
    echo ""
}

cmd_shell() {
    SERVICE=${1:-backend}
    print_header "Shell en contenedor: $SERVICE"
    docker-compose exec "$SERVICE" bash
}

cmd_migrate() {
    print_header "Migrar datos SQLite → PostgreSQL"
    
    if [ ! -f backend/logistica.db ]; then
        print_error "No se encontró backend/logistica.db"
        exit 1
    fi
    
    print_info "Verificando que PostgreSQL esté corriendo..."
    if ! docker-compose ps postgres | grep -q "Up"; then
        print_error "PostgreSQL no está corriendo. Ejecuta: ./manage.sh start"
        exit 1
    fi
    
    python migrate_to_postgres.py
}

cmd_import() {
    print_header "Importar datos desde Excel"
    
    if ! docker-compose ps backend | grep -q "Up"; then
        print_error "Backend no está corriendo. Ejecuta: ./manage.sh start"
        exit 1
    fi
    
    docker-compose exec backend python -m backend.import_data
}

cmd_backup_db() {
    print_header "Crear backup de PostgreSQL"
    
    BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).sql"
    
    docker-compose exec postgres pg_dump -U logistica_user logistica_hesego > "$BACKUP_FILE"
    
    print_success "Backup creado: $BACKUP_FILE"
}

cmd_restore_db() {
    BACKUP_FILE=${1:-}
    
    if [ -z "$BACKUP_FILE" ]; then
        print_error "Uso: ./manage.sh restore <archivo_backup.sql>"
        exit 1
    fi
    
    if [ ! -f "$BACKUP_FILE" ]; then
        print_error "Archivo no encontrado: $BACKUP_FILE"
        exit 1
    fi
    
    print_header "Restaurar backup de PostgreSQL"
    print_warning "Esto sobrescribirá los datos actuales"
    read -p "¿Continuar? (s/n): " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[SsYy]$ ]]; then
        print_info "Operación cancelada"
        exit 0
    fi
    
    docker-compose exec -T postgres psql -U logistica_user -d logistica_hesego < "$BACKUP_FILE"
    print_success "Backup restaurado"
}

cmd_clear_cache() {
    print_header "Limpiar caché Redis"
    docker-compose exec redis redis-cli FLUSHALL
    print_success "Caché limpiado"
}

cmd_clean() {
    print_header "Limpieza completa"
    print_warning "Esto eliminará todos los contenedores y volúmenes"
    read -p "¿Continuar? (s/n): " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[SsYy]$ ]]; then
        print_info "Operación cancelada"
        exit 0
    fi
    
    docker-compose down -v
    print_success "Limpieza completada"
}

cmd_health() {
    print_header "Health Checks"
    
    print_info "Backend API:"
    curl -s http://localhost:8000/api/health | python -m json.tool || print_error "Backend no responde"
    
    echo ""
    print_info "Frontend:"
    curl -s -o /dev/null -w "%{http_code}" http://localhost:8085/health
    echo ""
    
    echo ""
    print_info "Estado de contenedores:"
    docker-compose ps
}

cmd_help() {
    cat << EOF
🚀 Gestión de Logística HESEGO

Uso: ./manage.sh [comando] [argumentos]

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
  ./manage.sh start
  ./manage.sh logs backend
  ./manage.sh shell postgres
  ./manage.sh backup
  ./manage.sh restore backup_20260206.sql

EOF
}

# Main
COMMAND=${1:-help}

case $COMMAND in
    start)
        check_requirements
        cmd_start
        ;;
    stop)
        cmd_stop
        ;;
    restart)
        cmd_restart
        ;;
    build)
        cmd_build
        ;;
    rebuild)
        check_requirements
        cmd_rebuild
        ;;
    logs)
        cmd_logs "${2:-}"
        ;;
    status)
        cmd_status
        ;;
    shell)
        cmd_shell "${2:-backend}"
        ;;
    migrate)
        cmd_migrate
        ;;
    import)
        cmd_import
        ;;
    backup)
        cmd_backup_db
        ;;
    restore)
        cmd_restore_db "${2:-}"
        ;;
    clear-cache)
        cmd_clear_cache
        ;;
    clean)
        cmd_clean
        ;;
    health)
        cmd_health
        ;;
    help|--help|-h)
        cmd_help
        ;;
    *)
        print_error "Comando desconocido: $COMMAND"
        echo ""
        cmd_help
        exit 1
        ;;
esac
