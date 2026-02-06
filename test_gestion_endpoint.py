import requests
import json

try:
    response = requests.get("http://localhost:8000/api/gestion/grafico/por-sede", timeout=5)
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
except Exception as e:
    print(f"Error: {e}")
