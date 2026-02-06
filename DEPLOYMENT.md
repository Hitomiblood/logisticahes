# 🚀 Guía de Despliegue - Logística HESEGO v2.0

## 📋 Pre-requisitos

- Docker y Docker Compose instalados
- Red Docker `web` creada: `docker network create web`
- Archivos Excel en carpeta `data/`
- Clonar repositorio y configurar variables de entorno

## ⚙️ Configuración Inicial

### 1. Variables de Entorno

Copiar el archivo de ejemplo y configurar:

```bash
cp .env.example .env
```

Editar `.env` y configurar:

```bash
# Base de datos PostgreSQL
POSTGRES_USER=logistica_user
POSTGRES_PASSWORD=TU_PASSWORD_SEGURO_AQUI
POSTGRES_DB=logistica_hesego

# Otros parámetros importantes
ENVIRONMENT=production
LOG_LEVEL=INFO
CACHE_TTL=300
```

**IMPORTANTE**: Cambiar `POSTGRES_PASSWORD` por un valor seguro.

### 2. Crear red Docker (si no existe)

```bash
docker network create web
```

## 🐳 Despliegue con Docker

### Opción 1: Despliegue Completo (Recomendado)

```bash
# Construir e iniciar todos los servicios
docker-compose up -d --build

# Ver logs
docker-compose logs -f

# Ver estado de servicios
docker-compose ps
```

### Opción 2: Servicios Individuales

```bash
# Solo base de datos y caché
docker-compose up -d postgres redis

# Backend API
docker-compose up -d backend

# Frontend
docker-compose up -d nginx
```

## 📊 Migración de Datos (Si tienes datos en SQLite)

Si ya tienes datos en SQLite y quieres migrarlos a PostgreSQL:

```bash
# 1. Asegurar que Docker esté corriendo
docker-compose ps

# 2. Ejecutar script de migración
python migrate_to_postgres.py
```

Esto copiará todos los datos de `backend/logistica.db` a PostgreSQL.

## 📥 Importar Datos desde Excel

```bash
# Importar datos (dentro del contenedor backend)
docker-compose exec backend python -m backend.import_data

# O ejecutar localmente (requiere Python y dependencias instaladas)
python backend/import_data.py
```

## 🔍 Verificación del Despliegue

### 1. Verificar que todos los servicios estén corriendo

```bash
docker-compose ps
```

Deberías ver:
- ✅ `logistica_postgres` - healthy
- ✅ `logistica_redis` - healthy
- ✅ `logistica_backend` - healthy
- ✅ `logistica_nginx` - running

### 2. Verificar endpoints

```bash
# Health check del backend
curl http://localhost:8000/api/health

# Health check del frontend
curl http://localhost:8085/health

# API Stats
curl http://localhost:8000/api/admin/stats
```

### 3. Probar en navegador

- Frontend: http://164.68.118.86:8085 o http://localhost:8085
- API Docs (desarrollo): http://localhost:8000/api/docs
- API Redoc (desarrollo): http://localhost:8000/api/redoc

## 🛠️ Comandos Útiles

### Logs

```bash
# Todos los servicios
docker-compose logs -f

# Solo backend
docker-compose logs -f backend

# Solo PostgreSQL
docker-compose logs -f postgres

# Últimas 100 líneas
docker-compose logs --tail=100 backend
```

### Reiniciar Servicios

```bash
# Reiniciar todo
docker-compose restart

# Reiniciar solo backend
docker-compose restart backend

# Reconstruir y reiniciar backend
docker-compose up -d --build backend
```

### Acceder a Contenedores

```bash
# Shell en backend
docker-compose exec backend bash

# Shell en PostgreSQL
docker-compose exec postgres psql -U logistica_user -d logistica_hesego

# Shell en Redis
docker-compose exec redis redis-cli
```

### Limpiar Caché

```bash
# Desde la API
curl -X POST http://localhost:8000/api/admin/cache/clear

# Directamente en Redis
docker-compose exec redis redis-cli FLUSHALL
```

## 🗄️ Gestión de Base de Datos

### Backup de PostgreSQL

```bash
# Crear backup
docker-compose exec postgres pg_dump -U logistica_user logistica_hesego > backup_$(date +%Y%m%d).sql

# Restaurar backup
docker-compose exec -T postgres psql -U logistica_user -d logistica_hesego < backup_20260206.sql
```

### Conectar a PostgreSQL desde el host

```bash
# Usando psql (requiere cliente PostgreSQL instalado)
psql -h localhost -p 5433 -U logistica_user -d logistica_hesego

# Password: logistica_password_2026 (o el que configuraste)
```

## 🔒 Seguridad

### 1. Cambiar Contraseñas

Editar `.env`:
```bash
POSTGRES_PASSWORD=nueva_password_segura
WEBHOOK_SECRET=nuevo_secreto_seguro
```

Luego recrear servicios:
```bash
docker-compose down
docker volume rm logistica_postgres_data  # ¡CUIDADO! Borra datos
docker-compose up -d
```

### 2. Firewall

Configurar firewall para permitir solo conexiones necesarias:

```bash
# Ejemplo con ufw (Ubuntu)
sudo ufw allow 8085/tcp  # Frontend
sudo ufw allow 5000/tcp  # Webhook

# NO exponer puertos internos (8000, 5432, 6379)
```

## 📈 Monitoreo

### Ver uso de recursos

```bash
# CPU, Memoria, Red
docker stats

# Solo servicios de logística
docker stats logistica_backend logistica_postgres logistica_redis
```

### Ver espacio usado por volúmenes

```bash
docker system df -v
```

## 🐛 Troubleshooting

### Backend no inicia

```bash
# Ver logs
docker-compose logs backend

# Verificar PostgreSQL está listo
docker-compose exec postgres pg_isready

# Reiniciar con rebuild
docker-compose up -d --build backend
```

### Error de conexión a PostgreSQL

```bash
# Verificar que PostgreSQL esté corriendo
docker-compose ps postgres

# Verificar variables de entorno
docker-compose exec backend env | grep POSTGRES

# Probar conexión manual
docker-compose exec backend python -c "from backend.database import get_connection; get_connection()"
```

### Error de memoria de Redis

```bash
# Ver uso de memoria
docker-compose exec redis redis-cli INFO memory

# Limpiar caché
docker-compose exec redis redis-cli FLUSHALL

# Aumentar límite en docker-compose.yml:
# command: redis-server --maxmemory 1gb
```

### Archivos Excel no se encuentran

```bash
# Verificar volumen data
docker-compose exec backend ls -la /app/data

# Verificar permisos
docker-compose exec backend ls -la /app/data/TRANSPORTE/
```

## 🔄 Actualización de la Aplicación

```bash
# 1. Detener servicios
docker-compose down

# 2. Actualizar código (git pull o copiar archivos)

# 3. Reconstruir imágenes
docker-compose build --no-cache

# 4. Iniciar servicios
docker-compose up -d

# 5. Verificar logs
docker-compose logs -f backend
```

## 📞 Soporte

Para problemas o preguntas:
- Revisar logs: `docker-compose logs`
- Verificar health checks: `docker-compose ps`
- Contactar al administrador del sistema
