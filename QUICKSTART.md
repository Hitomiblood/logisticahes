# 🚀 QUICK START - Logística HESEGO

## Inicio Rápido (5 minutos)

### Windows PowerShell

```powershell
# 1. Configurar variables de entorno
Copy-Item .env.example .env
# Editar .env y cambiar las contraseñas

# 2. Iniciar servicios
.\manage.ps1 start

# 3. Ver estado
.\manage.ps1 status

# 4. Ver logs
.\manage.ps1 logs
```

### Linux/macOS

```bash
# 1. Dar permisos de ejecución
chmod +x manage.sh

# 2. Configurar variables de entorno
cp .env.example .env
# Editar .env y cambiar las contraseñas

# 3. Iniciar servicios
./manage.sh start

# 4. Ver estado
./manage.sh status

# 5. Ver logs
./manage.sh logs
```

## URLs de Acceso

- **Frontend**: http://164.68.118.86:8085 o http://localhost:8085
- **API**: http://localhost:8000/api/
- **API Docs**: http://localhost:8000/api/docs (solo desarrollo)
- **Webhook**: http://localhost:5000

## Comandos Esenciales

### Gestión Diaria

```powershell
# Windows
.\manage.ps1 start       # Iniciar
.\manage.ps1 stop        # Detener
.\manage.ps1 restart     # Reiniciar
.\manage.ps1 logs        # Ver logs
.\manage.ps1 status      # Ver estado
.\manage.ps1 health      # Health checks
```

```bash
# Linux/macOS
./manage.sh start        # Iniciar
./manage.sh stop         # Detener
./manage.sh restart      # Reiniciar
./manage.sh logs         # Ver logs
./manage.sh status       # Ver estado
./manage.sh health       # Health checks
```

### Importar Datos

```powershell
# Windows
.\manage.ps1 import      # Importar desde Excel

# Linux/macOS
./manage.sh import       # Importar desde Excel
```

### Backups

```powershell
# Windows
.\manage.ps1 backup                    # Crear backup
.\manage.ps1 restore backup_file.sql   # Restaurar backup

# Linux/macOS
./manage.sh backup                     # Crear backup
./manage.sh restore backup_file.sql    # Restaurar backup
```

## Migrar de SQLite a PostgreSQL

Si tienes datos existentes en SQLite:

```powershell
# 1. Asegurar que Docker esté corriendo
.\manage.ps1 status

# 2. Ejecutar migración
python migrate_to_postgres.py
```

## Troubleshooting Rápido

### Los servicios no inician

```powershell
# Ver qué está fallando
.\manage.ps1 status
.\manage.ps1 logs backend

# Verificar que la red existe
docker network ls | Select-String "web"

# Si no existe, crear:
docker network create web
```

### Error de conexión a PostgreSQL

```powershell
# Verificar que PostgreSQL está corriendo
docker-compose ps postgres

# Ver logs de PostgreSQL
.\manage.ps1 logs postgres

# Reiniciar PostgreSQL
docker-compose restart postgres
```

### Limpiar todo y empezar de nuevo

```powershell
# ⚠️ CUIDADO: Esto borra todos los datos
.\manage.ps1 clean
.\manage.ps1 start
```

## Archivos Importantes

- `.env` - Configuración (crear desde `.env.example`)
- `docker-compose.yml` - Orquestación de servicios
- `DEPLOYMENT.md` - Guía completa de despliegue
- `CHANGELOG.md` - Resumen de cambios

## Necesitas Ayuda?

```powershell
# Ver todos los comandos disponibles
.\manage.ps1 help
```

Ver documentación completa en [DEPLOYMENT.md](DEPLOYMENT.md)
