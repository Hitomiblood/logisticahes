#!/bin/bash
curl -s -X POST 'http://logistica-backend:8000/api/compras/kpis' \
  -H 'Content-Type: application/json' \
  -d '{"dateStart":"2024-01-01","dateEnd":"2024-12-31","processes":["BIENESTAR"],"suppliers":[]}'
