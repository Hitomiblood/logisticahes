# Configuración de Rclone para SharePoint

## Paso 1: Instalar Rclone en tu máquina local

### Windows
```powershell
# Con winget
winget install Rclone.Rclone

# O descargar desde https://rclone.org/downloads/
```

### Linux/Mac
```bash
curl https://rclone.org/install.sh | sudo bash
```

## Paso 2: Configurar conexión con SharePoint

Ejecuta el asistente de configuración:

```bash
rclone config
```

Sigue estos pasos:
1. Escribe `n` para nuevo remote
2. Nombre: `sharepoint`
3. Storage type: `onedrive` (número correspondiente)
4. Client ID: Dejar vacío (usa el de Microsoft)
5. Client Secret: Dejar vacío
6. Region: `global`
7. Edit advanced config: `n`
8. Use auto config: `y`

Se abrirá el navegador para autenticarte con tu cuenta de Microsoft corporativa.

9. Selecciona el tipo: `onedrive` o `sharepoint`
10. Si es SharePoint, selecciona el sitio: `Logstica` (o busca por URL)
11. Confirma y guarda

## Paso 3: Verificar la configuración

```bash
# Listar contenido del sitio de SharePoint
rclone ls sharepoint:

# Verificar que puedes acceder a la carpeta
rclone ls "sharepoint:Shared Documents/BI L&A/TRANSPORTE/"
```

## Paso 4: Copiar la configuración

El archivo de configuración se crea en:
- **Windows**: `%APPDATA%\rclone\rclone.conf`
- **Linux/Mac**: `~/.config/rclone/rclone.conf`

Copia este archivo a la carpeta `rclone/` del proyecto:

```bash
# Windows
copy %APPDATA%\rclone\rclone.conf .\rclone\rclone.conf

# Linux/Mac
cp ~/.config/rclone/rclone.conf ./rclone/rclone.conf
```

## Paso 5: Configurar el site ID correcto (si es necesario)

Si la ruta no funciona, puede que necesites obtener el site_id y drive_id correctos:

```bash
# Listar sites disponibles
rclone backend siteinfo sharepoint:

# Ver la estructura
rclone lsd sharepoint: --max-depth 2
```

## Paso 6: Probar sincronización local

```bash
# Crear carpeta de destino
mkdir -p ./data/transporte

# Sincronizar el archivo
rclone copy "sharepoint:Shared Documents/BI L&A/TRANSPORTE/Operatividad diaria Transporte.xlsx" ./data/transporte/
```

## Paso 7: Desplegar con Docker

Una vez que tengas `rclone.conf` configurado:

```bash
# Construir y ejecutar
docker-compose up -d --build

# Ver logs del sincronizador
docker logs -f rclone-sync
```

## Notas importantes

1. **Token de refresh**: El token de autenticación se renueva automáticamente, pero puede expirar después de 90 días de inactividad.

2. **Permisos**: Asegúrate de que la cuenta usada tenga permisos de lectura en el sitio de SharePoint.

3. **Ruta correcta**: Ajusta la ruta en `rclone/sync.sh` si es diferente:
   ```bash
   rclone copy "sharepoint:TU_RUTA_CORRECTA/Operatividad diaria Transporte.xlsx" /data/transporte/
   ```

4. **Frecuencia de sincronización**: Por defecto sincroniza cada 5 minutos. Puedes cambiar esto en `Dockerfile.rclone`:
   ```bash
   # Cada hora
   0 * * * * /scripts/sync.sh
   
   # Cada 15 minutos
   */15 * * * * /scripts/sync.sh
   ```

## Solución de problemas

### Error de autenticación
```bash
rclone config reconnect sharepoint:
```

### Ver logs detallados
```bash
rclone copy "sharepoint:..." /data/transporte/ -vv
```

### El archivo no aparece en el contenedor
```bash
# Verificar volumen
docker exec -it logisticahesego ls -la /usr/share/nginx/html/data/transporte/
```
