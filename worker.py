import os
import logging
from dotenv import load_dotenv
from gmail_manager import GmailManager
from wallet_automation import WalletAutomation
from notification_manager import TelegramNotifier

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_worker():
    # Load configuration
    from pathlib import Path
    import sys
    
    script_dir = Path(__file__).parent.absolute()
    env_path = script_dir / '.env'
    
    logger.info("--- WORKER BOOT ---")
    logger.info("Script Dir: {}".format(script_dir))
    logger.info("Loading .env from: {}".format(env_path))
    
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=True)
    else:
        logger.error(".env FILE NOT FOUND AT {}".format(env_path))
    
    # Telegram config
    tg_token = os.getenv('HABYT_TELEGRAM_TOKEN', os.getenv('TELEGRAM_TOKEN', '')).strip(' "')
    tg_chat_id = os.getenv('HABYT_TELEGRAM_CHAT_ID', os.getenv('TELEGRAM_CHAT_ID', '')).strip(' "')
    
    logger.info("HABYT_TELEGRAM_TOKEN: [FOUND]" if tg_token else "HABYT_TELEGRAM_TOKEN: [MISSING]")
    logger.info("HABYT_TELEGRAM_CHAT_ID: [FOUND]" if tg_chat_id else "HABYT_TELEGRAM_CHAT_ID: [MISSING]")
    
    notifier = TelegramNotifier(token=tg_token, chat_id=tg_chat_id)
    
    gmail_creds = os.getenv('GMAIL_CREDENTIALS_PATH', 'credentials.json')
    gmail_token = os.getenv('GMAIL_TOKEN_PATH', 'token.json')
    chrome_data_dir = os.getenv('CHROME_USER_DATA_DIR')
    chrome_profile = os.getenv('CHROME_PROFILE_NAME', 'Default')
    chrome_binary = os.getenv('CHROME_BINARY_PATH')
    chrome_debug_port = os.getenv('CHROME_DEBUG_PORT', '').strip()
    
    # Initialize managers
    gmail = GmailManager(
        credentials_path=os.path.join(script_dir, gmail_creds), 
        token_path=os.path.join(script_dir, gmail_token)
    )
    
    if chrome_debug_port:
        logger.info("MODE: Remote Debugging, Port={}".format(chrome_debug_port))
    else:
        logger.info("MODE: Local Profile, Dir={}".format(chrome_data_dir))

    wallet = WalletAutomation(
        user_data_dir=chrome_data_dir, 
        profile_name=chrome_profile,
        chrome_binary_path=chrome_binary if chrome_binary else None,
        debugger_address="127.0.0.1:{}".format(chrome_debug_port) if chrome_debug_port else None
    )

    success_count = 0
    failure_count = 0
    total_alerts = 0

    try:
        logger.info("Starting Gmail-to-WalletThat Automation Job...")
        
        # Step 1: Check for new alerts in Gmail
        alerts = gmail.get_unread_alerts()
        
        if not alerts:
            logger.info("No new alerts found.")
            return

        total_alerts = len(alerts)
        logger.info("Found {} new alert(s).".format(total_alerts))

        # Step 2: Open browser for automation
        wallet.start_browser()

        # Step 3: Process each alert
        for alert in alerts:
            msg_id = alert['id']
            alert_type = alert.get('alert_type', 'currency')
            template_id = alert.get('template_id', 'Unknown')
            
            logger.info("Processing {} alert for message {}".format(alert_type, msg_id))
            
            success = False
            error_detail = ""
            
            try:
                if alert_type == 'deletion':
                    template_ids = alert.get('template_ids', [])
                    template_id = ", ".join(template_ids) # For notification
                    logger.info("Processing deletion alert for message {}. IDs: {}".format(msg_id, template_ids))
                    failed_ids = []
                    for tid in template_ids:
                        if not wallet.delete_template(tid):
                            failed_ids.append(tid)
                    
                    if failed_ids:
                        error_detail = "Failed IDs: {}".format(failed_ids)
                        logger.error("Failed to delete some templates for message {}: {}".format(msg_id, failed_ids))
                        success = False
                    else:
                        success = True
                else:
                    template_id = alert.get('template_id', 'Unknown')
                    if alert_type == 'currency':
                        currency = alert['currency']
                        logger.info("Updating Currency: Template ID: {}, Currency: {}".format(template_id, currency))
                        success = wallet.update_template(template_id, currency)
                        if not success: error_detail = "Automation failed during currency update"
                    elif alert_type == 'icon':
                        icon_path = alert.get('icon_path')
                        logger.info("Updating Icon: Template ID: {}, Icon Path: {}".format(template_id, icon_path))
                        success = wallet.update_icon(template_id, icon_path)
                        if not success: error_detail = "Automation failed during icon update"
            except Exception as inner_e:
                logger.error("Error processing individual alert: {}".format(inner_e))
                success = False
                error_detail = str(inner_e)
            
            if success:
                # Step 4: Mark email as read and STAR it only if update was successful
                gmail.mark_as_read(msg_id)
                gmail.star_message(msg_id)
                logger.info("Successfully processed alert for message {}".format(msg_id))
                notifier.notify_success(alert_type, template_id)
                success_count += 1
            else:
                logger.error("Failed to process alert for message {}".format(msg_id))
                notifier.notify_failure(alert_type, template_id, error_detail)
                failure_count += 1

    except Exception as e:
        logger.error("An error occurred during execution: {}".format(e))
        import html
        safe_error = html.escape(str(e))
        notifier.send_message("<b>❌ CRITICAL ERROR in Habyt Worker Job</b>\n\n<code>{}</code>".format(safe_error))
    finally:
        wallet.close()
        logger.info("Job execution finished.")
        if total_alerts > 0:
            notifier.notify_job_summary(total_alerts, success_count, failure_count)

def main():
    import time
    interval_minutes = 10
    interval_seconds = interval_minutes * 60
    
    logger.info("Worker started. Will run every {} minutes.".format(interval_minutes))
    
    while True:
        try:
            total_alerts = 0
            run_worker()
        except Exception as e:
            logger.error("Fatal error in worker loop: {}".format(e))
        
        logger.info("Waiting {} minutes for next run...".format(interval_minutes))
        time.sleep(interval_seconds)

if __name__ == "__main__":
    main()
