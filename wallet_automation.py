import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from webdriver_manager.chrome import ChromeDriverManager

logger = logging.getLogger(__name__)

class WalletAutomation:
    def __init__(self, user_data_dir=None, profile_name="Default", chrome_binary_path=None, debugger_address=None):
        self.user_data_dir = user_data_dir
        self.profile_name = profile_name
        self.chrome_binary_path = chrome_binary_path
        self.debugger_address = debugger_address
        self.driver = None
        self.wait = None

    def start_browser(self):
        """Initializes or connects to a Chrome browser."""
        chrome_options = Options()
        
        if self.debugger_address:
            # Connect to existing browser
            chrome_options.debugger_address = self.debugger_address
            logger.info("Connecting to existing Chrome at {}".format(self.debugger_address))
        else:
            # Launch new browser with profile
            if not self.user_data_dir:
                raise ValueError("user_data_dir must be provided if not using debugger_address")
                
            chrome_options.add_argument("--user-data-dir={}".format(self.user_data_dir))
            chrome_options.add_argument("--profile-directory={}".format(self.profile_name))
            
            if self.chrome_binary_path:
                chrome_options.binary_location = self.chrome_binary_path

            # Avoid basic bot detection
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option("useAutomationExtension", False)

        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.wait = WebDriverWait(self.driver, 20)
            if not self.debugger_address:
                logger.info("Launched Chrome with profile: {}".format(self.profile_name))
            else:
                logger.info("Successfully attached to existing Chrome instance.")
        except Exception as e:
            if "user data directory is already in use" in str(e):
                logger.error("CHROME ERROR: The Chrome profile you specified is already open.")
                logger.error("FIX: Either close Chrome, or use the 'Remote Debugging' method (see walkthrough).")
            raise e

    def update_template(self, template_id, currency):
        """Perform the update flow for a specific template."""
        if not self.driver:
            self.start_browser()

        try:
            url = "https://app.walletthat.com/platform/wallet/pass-templates.php"
            self.driver.get(url)
            logger.info("Navigated to: {}".format(url))

            # 1. Filter by Template ID
            search_input = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='search']")))
            search_input.clear()
            search_input.send_keys(template_id)
            time.sleep(1) # Allow for AJAX filtering

            actions_btn = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//td[contains(text(), '{}')]/following-sibling::td//button[contains(text(), 'Actions')]".format(template_id))))
            actions_btn.click()

            edit_link = self.wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Edit")))
            edit_link.click()

            continue_btn = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Continue')]")))
            continue_btn.click()

            # 3. Navigate until "Universal Fields" section is reached
            # This might involve multiple "Continue" clicks depending on the wizard steps
            # We'll look for the Currency Code field as a signal
            while True:
                try:
                    # Look for currency dropdown
                    currency_dropdown_el = self.driver.find_elements(By.ID, "currency_code")
                    if currency_dropdown_el and currency_dropdown_el[0].is_displayed():
                         break
                    
                    next_btn = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Continue')]")))
                    next_btn.click()
                    time.sleep(1)
                except Exception as e:
                    logger.error("Error while navigating to Universal Fields: {}".format(e))
                    break

            # 4. Data Update
            # Select Currency Code
            currency_select = Select(self.wait.until(EC.presence_of_element_located((By.ID, "currency_code"))))
            currency_select.select_by_value(currency)
            logger.info("Selected currency: {}".format(currency))

            # Check Card Balance Value
            balance_field = self.wait.until(EC.presence_of_element_located((By.ID, "card_balance_value")))
            current_val = balance_field.get_attribute("value")
            if current_val == "0":
                balance_field.clear()
                logger.info("Cleared balance field (was '0')")

            # 5. Save and Push
            save_btn = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Save Pass Template')]")))
            save_btn.click()

            update_push_btn = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Update and Continue')]")))
            update_push_btn.click()
            logger.info("Template {} update completed successfully.".format(template_id))

            return True

        except Exception as e:
            logger.error("Failed to update template {}: {}".format(template_id, e))
            return False

    def close(self):
        if self.driver:
            self.driver.quit()
            logger.info("Browser closed.")
