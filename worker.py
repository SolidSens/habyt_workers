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
    
    if not chrome_data_dir:
        logger.error("CHROME_USER_DATA_DIR not set in .env file.")
        return

    # Initialize managers
    gmail = GmailManager(credentials_path=gmail_creds, token_path=gmail_token)
    wallet = WalletAutomation(
        user_data_dir=chrome_data_dir, 
        profile_name=chrome_profile,
        chrome_binary_path=chrome_binary if chrome_binary else None
    )

    try:
        logger.info("Starting Gmail-to-WalletThat Automation Worker...")
        
        # Step 1: Check for new alerts in Gmail
        alerts = gmail.get_unread_alerts()
        
        if not alerts:
            logger.info("No new alerts found.")
            return

        logger.info(f"Found {len(alerts)} new alert(s).")

        # Step 2: Open browser for automation
        wallet.start_browser()

        # Step 3: Process each alert
        for alert in alerts:
            template_id = alert['template_id']
            currency = alert['currency']
            msg_id = alert['id']
            
            logger.info(f"Processing Template ID: {template_id}, Currency: {currency}")
            
            success = wallet.update_template(template_id, currency)
            
            if success:
                # Step 4: Mark email as read only if update was successful
                gmail.mark_as_read(msg_id)
                logger.info(f"Successfully processed alert for message {msg_id}")
            else:
                logger.error(f"Failed to process alert for message {msg_id}")

    except Exception as e:
        logger.error(f"An error occurred during execution: {e}")
    finally:
        wallet.close()
        logger.info("Worker session ended.")

if __name__ == "__main__":
    main()
