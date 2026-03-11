import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get credentials from environment
TOKEN = os.getenv('HABYT_TELEGRAM_TOKEN', os.getenv('TELEGRAM_TOKEN', '')).strip(' "')
CHAT_ID = os.getenv('HABYT_TELEGRAM_CHAT_ID', os.getenv('TELEGRAM_CHAT_ID', '')).strip(' "')

if not TOKEN or not CHAT_ID:
    print("ERROR: TOKEN or CHAT_ID not found in environment variables!")
    print(f"TOKEN: {'Found' if TOKEN else 'Missing'}")
    print(f"CHAT_ID: {'Found' if CHAT_ID else 'Missing'}")
    exit(1)

print("--- Iniciando prueba de conexión ---")
print(f"Token: {TOKEN[:10]}...")
print(f"Chat ID (string): {CHAT_ID}")
print(f"Chat ID (int): {int(CHAT_ID) if CHAT_ID.isdigit() else 'N/A'}")

url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

# Test 1: With chat_id as string
print("\n=== Test 1: chat_id as string ===")
payload1 = {
    "chat_id": CHAT_ID,
    "text": "<b>Prueba Habyt</b>: Si lees esto, el sistema funciona.",
    "parse_mode": "HTML"
}

try:
    r = requests.post(url, json=payload1, timeout=10)
    print(f"Código de estado: {r.status_code}")
    
    respuesta = r.json()
    print("Respuesta completa de Telegram:")
    print(json.dumps(respuesta, indent=4))
    
    if r.status_code == 200:
        print("[SUCCESS] con chat_id como string!")
    else:
        print(f"[FAILED] con chat_id como string: {respuesta.get('description', 'Unknown error')}")
        
except Exception as e:
    print(f"[ERROR] Error de red o conexion: {e}")

# Test 2: With chat_id as integer (if it's numeric)
if CHAT_ID.isdigit():
    print("\n=== Test 2: chat_id as integer ===")
    payload2 = {
        "chat_id": int(CHAT_ID),
        "text": "<b>Prueba Habyt</b>: Si lees esto, el sistema funciona.",
        "parse_mode": "HTML"
    }
    
    try:
        r = requests.post(url, json=payload2, timeout=10)
        print(f"Código de estado: {r.status_code}")
        
        respuesta = r.json()
        print("Respuesta completa de Telegram:")
        print(json.dumps(respuesta, indent=4))
        
        if r.status_code == 200:
            print("[SUCCESS] con chat_id como integer!")
        else:
            print(f"[FAILED] con chat_id como integer: {respuesta.get('description', 'Unknown error')}")
            
    except Exception as e:
        print(f"[ERROR] Error de red o conexion: {e}")

# Test 3: Without HTML (plain text)
print("\n=== Test 3: Plain text (no HTML) ===")
payload3 = {
    "chat_id": int(CHAT_ID) if CHAT_ID.isdigit() else CHAT_ID,
    "text": "Prueba Habyt: Si lees esto, el sistema funciona."
}

try:
    r = requests.post(url, json=payload3, timeout=10)
    print(f"Código de estado: {r.status_code}")
    
    respuesta = r.json()
    print("Respuesta completa de Telegram:")
    print(json.dumps(respuesta, indent=4))
    
    if r.status_code == 200:
        print("[SUCCESS] con texto plano!")
    else:
        print(f"[FAILED] con texto plano: {respuesta.get('description', 'Unknown error')}")
        
except Exception as e:
    print(f"[ERROR] Error de red o conexion: {e}")