# 📊 Sistema de Logística HESEGO v2.0

Sistema de dashboards interactivos para la gestión logística de HESEGO, construido con FastAPI, PostgreSQL, Redis y Nginx.

## 🌟 Características

- ✅ **Backend API REST** con FastAPI
- ✅ **Base de datos PostgreSQL** para producción
- ✅ **Caché Redis** para optimización de consultas
- ✅ **Frontend SPA** con dashboards interactivos
- ✅ **Nginx** como reverse proxy
- ✅ **Docker** para despliegue consistente
- ✅ **Logging estructurado** en JSON
- ✅ **Manejo de errores robusto**
- ✅ **Health checks** para monitoreo

## 📁 Estructura del Proyecto

```
Logisticahes/
├── backend/                    # API Backend (FastAPI)
│   ├── routes/                # Endpoints organizados por módulo
│   ├── api.py                 # Aplicación principal
│   ├── database.py            # Gestión de PostgreSQL/SQLite
│   ├── config.py              # Configuración centralizada
│   ├── cache.py               # Sistema de caché Redis
│   ├── logging_middleware.py # Logging y manejo de errores
│   └── import_data.py         # Importación de datos Excel
├── frontend/                  # Frontend HTML/JS
│   ├── index.html
│   ├── costos_mensuales.html
│   ├── operatividad_vehiculos.html
│   ├── compras.html
│   └── indicadores.html
├── data/                      # Datos Excel (no versionado)
│   ├── TRANSPORTE/
│   ├── COMPRAS/
│   └── ALMACENES/
├── docker-compose.yml         # Orquestación de servicios
├── Dockerfile.backend         # Imagen del backend
├── Dockerfile                 # Imagen del frontend (Nginx)
├── nginx.conf                 # Configuración Nginx
├── migrate_to_postgres.py     # Script de migración de datos
├── .env.example               # Plantilla de variables de entorno
└── DEPLOYMENT.md              # Guía de despliegue

```

## 🚀 Quick Start

### 1. Prerrequisitos

- Docker 20.10+
- Docker Compose 2.0+
- Red Docker `web`: `docker network create web`

### 2. Configuración

```bash
# Copiar configuración de ejemplo
cp .env.example .env

# Editar .env y configurar passwords
nano .env
```

### 3. Despliegue

```bash
# Iniciar todos los servicios
docker-compose up -d

# Ver logs
docker-compose logs -f

# Verificar estado
docker-compose ps
```

### 4. Acceder

- **Frontend**: http://164.68.118.86:8085
- **API**: http://164.68.118.86:8000/api/
- **API Docs**: http://localhost:8000/api/docs (solo desarrollo)

## 📊 Módulos Disponibles

### 🚚 Transporte
- **Costos Mensuales**: Análisis de costos de vehículos
- **Operatividad**: Estado diario de la flota

### 🛒 Compras
- **Trazabilidad**: Seguimiento de requisiciones a órdenes de compra
- **Descuentos**: Gestión de descuentos en compras
- **Órdenes Generadas**: Análisis de órdenes de compra

### 📦 Almacenes
- **Indicadores OYMM**: Inventarios y diferencias
- **Fiscal RU**: Control fiscal
- **Brigadas**: Inventarios de brigadas
- **Errores**: Registro de errores en movimientos
- **Programados vs Ejecutados**: Cumplimiento de inventarios
- **Gestión**: Tiempos de ejecución de inventarios

## 🔧 Desarrollo Local

### Configuración para desarrollo

```bash
# Usar SQLite en lugar de PostgreSQL
export DB_TYPE=sqlite
export ENVIRONMENT=development

# Instalar dependencias
pip install -r backend/requirements.txt

# Ejecutar servidor de desarrollo
python run_server.py
```

### Importar datos Excel

```bash
# Desde Docker
docker-compose exec backend python -m backend.import_data

# Local
python backend/import_data.py
```

## 🗄️ Base de Datos

### PostgreSQL (Producción)

```yaml
Host: localhost
Port: 5433 (mapeado desde contenedor)
User: logistica_user
Database: logistica_hesego
```

### Migrar de SQLite a PostgreSQL

```bash
python migrate_to_postgres.py
```

## 📈 Monitoreo

### Health Checks

```bash
# Backend
curl http://localhost:8000/api/health

# Frontend
curl http://localhost:8085/health
```

### Estadísticas de caché

```bash
curl http://localhost:8000/api/admin/cache/stats
```

### Limpiar caché

```bash
curl -X POST http://localhost:8000/api/admin/cache/clear
```

## 🛡️ Seguridad

- ✅ Contraseñas configurables via variables de entorno
- ✅ Usuarios no-root en contenedores
- ✅ Logs sin información sensible en producción
- ✅ CORS configurable
- ✅ Healthchecks para monitoring

## 📝 API Endpoints

### Administración
- `GET /api/health` - Health check
- `GET /api/admin/stats` - Estadísticas de BD
- `GET /api/admin/cache/stats` - Estadísticas de caché
- `POST /api/admin/cache/clear` - Limpiar caché

### Costos
- `GET /api/costos/datos` - Datos de costos
- `GET /api/costos/filtros` - Filtros disponibles
- `GET /api/costos/kpis` - KPIs de costos

### Operatividad
- `GET /api/operatividad/datos` - Datos de operatividad
- `GET /api/operatividad/kpis` - KPIs de operatividad
- `GET /api/operatividad/diaria` - Operatividad diaria

### Indicadores
- `GET /api/indicadores/datos` - Datos de indicadores
- `GET /api/indicadores/kpis` - KPIs de inventarios
- `GET /api/indicadores/por-sede` - Análisis por sede

Ver documentación completa en `/api/docs` (desarrollo)

## 🐛 Troubleshooting

Ver [DEPLOYMENT.md](DEPLOYMENT.md) para guía detallada de resolución de problemas.

## 📞 Contacto

Sistema desarrollado para HESEGO
- URL: http://164.68.118.86/
- Versión: 2.0.0

## 📄 Licencia

Uso interno de HESEGO
