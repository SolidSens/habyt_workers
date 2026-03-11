"""
Helper script to get your Telegram chat_id.
This script will help you find the correct chat_id by getting updates from your bot.

Instructions:
1. Start a conversation with your bot on Telegram (search for your bot by username)
2. Send any message to your bot (e.g., "/start" or "Hello")
3. Run this script to get your chat_id
"""
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('HABYT_TELEGRAM_TOKEN', os.getenv('TELEGRAM_TOKEN', '')).strip(' "')
CURRENT_CHAT_ID = os.getenv('HABYT_TELEGRAM_CHAT_ID', os.getenv('TELEGRAM_CHAT_ID', '')).strip(' "')

if not TOKEN:
    print("ERROR: TOKEN not found in environment variables!")
    exit(1)

print("=" * 60)
print("Telegram Chat ID Finder")
print("=" * 60)
print(f"Token: {TOKEN[:15]}...")
if CURRENT_CHAT_ID:
    print(f"Current chat_id in .env: {CURRENT_CHAT_ID}")
print("\nChecking bot updates...")
print("(Make sure you've sent a message to your bot first!)\n")

# First, get bot info to show which bot to message
print("Getting bot information...")
try:
    bot_url = f"https://api.telegram.org/bot{TOKEN}/getMe"
    bot_response = requests.get(bot_url, timeout=10)
    bot_data = bot_response.json()
    
    if bot_data.get('ok'):
        bot = bot_data['result']
        bot_username = bot.get('username', 'N/A')
        bot_name = bot.get('first_name', 'N/A')
        print(f"Bot Name: {bot_name}")
        print(f"Bot Username: @{bot_username}")
        print(f"Bot Link: https://t.me/{bot_username}")
    else:
        print(f"[ERROR] Invalid bot token: {bot_data.get('description')}")
        exit(1)
except Exception as e:
    print(f"[WARNING] Could not get bot info: {e}")

print()

# Now get updates
url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"

try:
    response = requests.get(url, timeout=10)
    data = response.json()
    
    if not data.get('ok'):
        print(f"[ERROR] {data.get('description', 'Unknown error')}")
        exit(1)
    
    updates = data.get('result', [])
    
    if not updates:
        print("\nNo updates found!")
        print("Please:")
        print("1. Make sure you've sent a message to your bot")
        print("2. Wait a few seconds and try again")
        exit(1)
    
    print(f"\nFound {len(updates)} update(s):\n")
    
    chat_ids = set()
    for update in updates:
        message = update.get('message', {})
        chat = message.get('chat', {})
        chat_id = chat.get('id')
        chat_type = chat.get('type', 'unknown')
        username = chat.get('username', 'N/A')
        first_name = chat.get('first_name', 'N/A')
        
        if chat_id:
            chat_ids.add(chat_id)
            print(f"Chat ID: {chat_id}")
            print(f"  Type: {chat_type}")
            print(f"  Username: @{username}")
            print(f"  Name: {first_name}")
            print(f"  Message: {message.get('text', 'N/A')[:50]}...")
            print()
    
    if chat_ids:
        print(f"\nFound chat_id(s): {', '.join(map(str, chat_ids))}")
        recommended_id = list(chat_ids)[0]
        
        if CURRENT_CHAT_ID:
            if str(recommended_id) == CURRENT_CHAT_ID:
                print(f"\n[OK] Your current chat_id ({CURRENT_CHAT_ID}) matches!")
            else:
                print(f"\n[INFO] Your current chat_id ({CURRENT_CHAT_ID}) differs from bot's received messages.")
                print(f"[INFO] Recommended chat_id: {recommended_id}")
        else:
            print(f"\n[INFO] Recommended chat_id: {recommended_id}")
        
        print("\nTo update your .env file, use:")
        print(f'HABYT_TELEGRAM_CHAT_ID="{recommended_id}"')
    else:
        print("\n[WARNING] No chat IDs found in updates!")
        print("\nThis means:")
        print("  1. You haven't sent a message to your bot yet, OR")
        print("  2. The bot hasn't received any messages")
        print("\n[ACTION REQUIRED]:")
        print("  1. Open Telegram")
        print("  2. Search for your bot (from @botfather)")
        print("  3. Send any message (e.g., '/start' or 'Hello')")
        print("  4. Run this script again")
        
except Exception as e:
    print(f"Error: {e}")
