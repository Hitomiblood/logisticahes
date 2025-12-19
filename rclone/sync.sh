#!/bin/bash
# Script para sincronizar archivos de SharePoint usando Rclone

# Sincronizar el archivo de Operatividad de Transporte
rclone copy "sharepoint:Logstica/Shared Documents/BI L&A/TRANSPORTE/Operatividad diaria Transporte.xlsx" /data/transporte/ --config /config/rclone.conf

echo "$(date): Sincronización completada" >> /data/sync.log
