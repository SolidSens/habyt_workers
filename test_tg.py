import os
import logging
from dotenv import load_dotenv
from notification_manager import TelegramNotifier

logging.basicConfig(level=logging.INFO)

def test_tg():
    load_dotenv()
    token = os.getenv('HABYT_TELEGRAM_TOKEN', os.getenv('TELEGRAM_TOKEN'))
    chat_id = os.getenv('HABYT_TELEGRAM_CHAT_ID', os.getenv('TELEGRAM_CHAT_ID'))
    
    print(f"Testing with Token: {token[:5]}... and ChatID: {chat_id}")
    notifier = TelegramNotifier(token=token, chat_id=chat_id)
    
    # Test HTML
    print("Testing HTML message...")
    notifier.send_message("<b>Test Message</b> from Habyt Worker (HTML)")
    
    # Test Success Notification
    print("\nTesting Success notification...")
    notifier.notify_success("test_type", "TEST_ID_123")

if __name__ == "__main__":
    test_tg()
