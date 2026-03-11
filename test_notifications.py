"""
Comprehensive test script to verify all Telegram notification types
that the worker sends. This simulates all notification scenarios.
"""
import os
import logging
from dotenv import load_dotenv
from notification_manager import TelegramNotifier

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_all_notifications():
    """Test all notification types that the worker sends."""
    load_dotenv()
    
    token = os.getenv('HABYT_TELEGRAM_TOKEN', os.getenv('TELEGRAM_TOKEN', '')).strip(' "')
    chat_id = os.getenv('HABYT_TELEGRAM_CHAT_ID', os.getenv('TELEGRAM_CHAT_ID', '')).strip(' "')
    
    if not token or not chat_id:
        print("ERROR: Telegram token or chat_id not found in .env file!")
        print(f"Token: {'Found' if token else 'Missing'}")
        print(f"Chat ID: {'Found' if chat_id else 'Missing'}")
        return False
    
    print("=" * 70)
    print("Telegram Notification Test Suite")
    print("=" * 70)
    print(f"Token: {token[:15]}...")
    print(f"Chat ID: {chat_id}")
    print()
    
    notifier = TelegramNotifier(token=token, chat_id=chat_id)
    
    # Test 1: Success notification (currency update)
    print("[Test 1/5] Testing Success Notification (Currency Update)...")
    success1 = notifier.notify_success("currency", "TEMPLATE_123", "USD")
    print(f"  Result: {'✓ PASSED' if success1 else '✗ FAILED'}")
    print()
    
    # Test 2: Success notification (icon update)
    print("[Test 2/5] Testing Success Notification (Icon Update)...")
    success2 = notifier.notify_success("icon", "TEMPLATE_456", "icon_path.png")
    print(f"  Result: {'✓ PASSED' if success2 else '✗ FAILED'}")
    print()
    
    # Test 3: Success notification (deletion)
    print("[Test 3/5] Testing Success Notification (Deletion)...")
    success3 = notifier.notify_success("deletion", "TEMPLATE_789, TEMPLATE_012")
    print(f"  Result: {'✓ PASSED' if success3 else '✗ FAILED'}")
    print()
    
    # Test 4: Failure notification
    print("[Test 4/5] Testing Failure Notification...")
    error_msg = "Automation failed during currency update"
    success4 = notifier.notify_failure("currency", "TEMPLATE_999", error_msg)
    print(f"  Result: {'✓ PASSED' if success4 else '✗ FAILED'}")
    print()
    
    # Test 5: Job Summary notification
    print("[Test 5/5] Testing Job Summary Notification...")
    success5 = notifier.notify_job_summary(total=5, success_count=3, failure_count=2)
    print(f"  Result: {'✓ PASSED' if success5 else '✗ FAILED'}")
    print()
    
    # Test 6: Critical Error notification (simulating worker.py line 144)
    print("[Test 6/6] Testing Critical Error Notification...")
    import html
    test_error = "Test error: Something went wrong during execution"
    safe_error = html.escape(str(test_error))
    critical_msg = "<b>❌ CRITICAL ERROR in Habyt Worker Job</b>\n\n<code>{}</code>".format(safe_error)
    success6 = notifier.send_message(critical_msg)
    print(f"  Result: {'✓ PASSED' if success6 else '✗ FAILED'}")
    print()
    
    # Summary
    print("=" * 70)
    results = [success1, success2, success3, success4, success5, success6]
    passed = sum(results)
    total = len(results)
    print(f"Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("✓ All notifications sent successfully!")
        print("\nCheck your Telegram bot (@habytaltersbot) to verify the messages.")
    else:
        print("✗ Some notifications failed. Check the logs above for details.")
        print("\nCommon issues:")
        print("  1. Make sure you've sent a message to @habytaltersbot first")
        print("  2. Verify your chat_id is correct (run: python get_chat_id.py)")
        print("  3. Check that your bot token is valid")
    
    print("=" * 70)
    return passed == total

if __name__ == "__main__":
    test_all_notifications()
