#!/bin/bash

echo "Iniciando sincronización inicial..."
/scripts/sync.sh

echo "Iniciando cron daemon..."
crond -f -l 2
