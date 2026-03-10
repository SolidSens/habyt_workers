import os
import logging
from dotenv import load_dotenv
from gmail_manager import GmailManager
from wallet_automation import WalletAutomation

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    # Load configuration
    load_dotenv()
    
    gmail_creds = os.getenv('GMAIL_CREDENTIALS_PATH', 'credentials.json')
    gmail_token = os.getenv('GMAIL_TOKEN_PATH', 'token.json')
    chrome_data_dir = os.getenv('CHROME_USER_DATA_DIR')
    chrome_profile = os.getenv('CHROME_PROFILE_NAME', 'Default')
    chrome_binary = os.getenv('CHROME_BINARY_PATH')
    # Use strip() to handle cases with trailing spaces in .env
    chrome_debug_port = os.getenv('CHROME_DEBUG_PORT', '').strip()
    
    # Initialize managers
    gmail = GmailManager(credentials_path=gmail_creds, token_path=gmail_token)
    
    if chrome_debug_port and chrome_debug_port != "":
        logger.info("CONFIGURATION: Mode=Remote Debugging, Port={}".format(chrome_debug_port))
    else:
        logger.info("CONFIGURATION: Mode=Local Profile, Dir={}".format(chrome_data_dir))

    wallet = WalletAutomation(
        user_data_dir=chrome_data_dir, 
        profile_name=chrome_profile,
        chrome_binary_path=chrome_binary if chrome_binary else None,
        debugger_address="127.0.0.1:{}".format(chrome_debug_port) if chrome_debug_port else None
    )

    try:
        logger.info("Starting Gmail-to-WalletThat Automation Worker...")
        
        # Step 1: Check for new alerts in Gmail
        alerts = gmail.get_unread_alerts()
        
        if not alerts:
            logger.info("No new alerts found.")
            return

        logger.info("Found {} new alert(s).".format(len(alerts)))

        # Step 2: Open browser for automation
        wallet.start_browser()

        # Step 3: Process each alert
        for alert in alerts:
            msg_id = alert['id']
            template_id = alert['template_id']
            alert_type = alert.get('alert_type', 'currency')
            
            logger.info("Processing {} alert for message {}".format(alert_type, msg_id))
            
            success = False
            if alert_type == 'currency':
                currency = alert['currency']
                logger.info("Updating Currency: Template ID: {}, Currency: {}".format(template_id, currency))
                success = wallet.update_template(template_id, currency)
            elif alert_type == 'icon':
                icon_path = alert.get('icon_path')
                logger.info("Updating Icon: Template ID: {}, Icon Path: {}".format(template_id, icon_path))
                success = wallet.update_icon(template_id, icon_path)
            
            if success:
                # Step 4: Mark email as read and STAR it only if update was successful
                gmail.mark_as_read(msg_id)
                gmail.star_message(msg_id)
                logger.info("Successfully processed alert for message {}".format(msg_id))
            else:
                logger.error("Failed to process alert for message {}".format(msg_id))

    except Exception as e:
        logger.error("An error occurred during execution: {}".format(e))
    finally:
        wallet.close()
        logger.info("Worker session ended.")

if __name__ == "__main__":
    main()
