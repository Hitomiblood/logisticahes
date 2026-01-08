import urllib.request
import json

# Probar endpoint de KPIs
url = "http://localhost:8000/api/compras/kpis"
data = {
    "dateStart": "2025-06-13",
    "dateEnd": "2025-09-13",
    "processes": ["Comercial", "Gerencia de Proyectos"],
    "suppliers": []
}

print("Probando endpoint:", url)
print("Data:", data)

try:
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    with urllib.request.urlopen(req, timeout=60) as response:
        result = json.loads(response.read().decode())
        print("Status: 200")
        print("Response:", json.dumps(result, indent=2)[:800])
except urllib.error.HTTPError as e:
    print("HTTP Error:", e.code, e.reason)
    print("Body:", e.read().decode()[:500])
except Exception as e:
    print("Error:", e)
