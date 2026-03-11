import requests
TOKEN = "TU_TOKEN"
ID = "TU_ID"
msg = "<b>Prueba Habyt</b>"
r = requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                 json={"chat_id": ID, "text": msg, "parse_mode": "HTML"})
print(r.status_code)
print(r.text)