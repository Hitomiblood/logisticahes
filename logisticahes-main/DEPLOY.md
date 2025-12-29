# Despliegue de Logística HESEGO

## Archivos incluidos
- `index.html` - Portal de reportes
- `app.html` - Dashboard de operatividad de vehículos
- `img/logo.png` - Logo de HESEGO
- `Dockerfile` - Configuración de contenedor
- `docker-compose.yml` - Orquestación del contenedor
- `nginx.conf` - Configuración del servidor web

## Instrucciones de despliegue

### 1. Subir archivos al servidor
```bash
# Desde tu máquina local (PowerShell/CMD)
scp -r * usuario@164.68.118.86:/home/usuario/logisticahesego/
```

O usar FileZilla/WinSCP para copiar la carpeta completa.

### 2. En el servidor (SSH)
```bash
# Conectar al servidor
ssh usuario@164.68.118.86

# Ir a la carpeta del proyecto
cd /home/usuario/logisticahesego

# Crear red si no existe
docker network create web 2>/dev/null || true

# Construir y levantar el contenedor
docker-compose up -d --build

# Verificar que esté corriendo
docker ps | grep logisticahesego
```

### 3. Configurar Cloudflare

En el panel de Cloudflare para `logisticahesego.com`:

**DNS Records:**
| Tipo | Nombre | Contenido | Proxy |
|------|--------|-----------|-------|
| A | @ | 164.68.118.86 | Proxied ☁️ |
| A | www | 164.68.118.86 | Proxied ☁️ |

**SSL/TLS:**
- Modo: `Flexible` (si no tienes SSL en el servidor) o `Full` (si usas certificado)

### 4. Configurar Nginx Proxy (en el servidor)

Si tienes un nginx proxy principal en el servidor, agrega este bloque:

```nginx
# /etc/nginx/sites-available/logisticahesego.com
server {
    listen 80;
    server_name logisticahesego.com www.logisticahesego.com;

    location / {
        proxy_pass http://127.0.0.1:8085;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Luego:
```bash
sudo ln -s /etc/nginx/sites-available/logisticahesego.com /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 5. Verificar
- Abrir https://logisticahesego.com
- Debería mostrar el portal con los 3 dashboards

## Comandos útiles

```bash
# Ver logs del contenedor
docker logs logisticahesego

# Reiniciar contenedor
docker-compose restart

# Detener contenedor
docker-compose down

# Reconstruir después de cambios
docker-compose up -d --build
```

## Puerto asignado
- **Puerto interno:** 80
- **Puerto externo:** 8085

Si el puerto 8085 está ocupado, cambia en `docker-compose.yml`:
```yaml
ports:
  - "OTRO_PUERTO:80"
```
