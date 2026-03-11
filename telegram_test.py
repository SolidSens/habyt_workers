import requests
import json

# REEMPLAZA ESTOS DOS VALORES
TOKEN = "TU_TOKEN_AQUI"
CHAT_ID = "TU_ID_AQUI" 

url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
payload = {
    "chat_id": CHAT_ID,
    "text": "<b>Prueba Habyt</b>: Si lees esto, el sistema funciona.",
    "parse_mode": "HTML"
}

print("--- Iniciando prueba de conexión ---")

try:
    # Usamos json= para que requests maneje los tipos de datos correctamente
    r = requests.post(url, json=payload, timeout=10)
    
    print(f"Código de estado: {r.status_code}")
    
    # Esto nos dirá el error REAL que manda Telegram
    respuesta = r.json()
    print("Respuesta completa de Telegram:")
    print(json.dumps(respuesta, indent=4))

except Exception as e:
    print(f"Error de red o conexión: {e}")