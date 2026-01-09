#!/usr/bin/env python3
import requests

# Usar nombre del contenedor Docker en la red interna
url = "http://logistica-backend:8000/api/compras/kpis"
payload = {
    "dateStart": "2024-01-01",
    "dateEnd": "2024-12-31",
    "processes": ["BIENESTAR"],
    "suppliers": []
}

try:
    r = requests.post(url, json=payload, timeout=30)
    print(f"Status: {r.status_code}")
    print(f"Response: {r.text[:500]}")
except Exception as e:
    print(f"Error: {e}")
