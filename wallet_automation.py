import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.keys import Keys
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
            
            if self.debugger_address:
                logger.info("Successfully attached to existing Chrome at {}.".format(self.debugger_address))
            else:
                logger.info("Launched Chrome with profile: {}".format(self.profile_name))

        except Exception as e:
            if "user data directory is already in use" in str(e):
                logger.error("CHROME ERROR: The Chrome profile you specified is already open.")
                logger.error("FIX: Either close Chrome, or use the 'Remote Debugging' method (see walkthrough).")
            raise e

    def _robust_click(self, element, description="element"):
        """Tries to click an element, falls back to JS click if obstructed."""
        try:
            # Scroll into view
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(0.5)
            element.click()
            logger.info("Successfully clicked {}.".format(description))
        except Exception as e:
            logger.warning("Standard click failed for {}, trying JavaScript click. Error: {}".format(description, e))
            self.driver.execute_script("arguments[0].click();", element)
            logger.info("Successfully clicked {} via JavaScript.".format(description))

    def update_template(self, template_id, currency):
        """Perform the update flow for a specific template."""
        if not self.driver:
            self.start_browser()
        
        # Ensure wait is initialized (lint fix and safety)
        if self.driver and not self.wait:
            self.wait = WebDriverWait(self.driver, 20)

        try:
            url = "https://app.walletthat.com/platform/wallet/pass-templates.php"
            if self.driver.current_url != url:
                logger.info("Current URL is different, navigating to: {}".format(url))
                self.driver.get(url)
                time.sleep(2) # Give it time to load
            else:
                logger.info("Already on the templates page.")

            # 1. Filter by Template ID
            logger.info("Locating search input...")
            search_input = None
            for selector in [(By.ID, "searchtxt"), (By.CSS_SELECTOR, "input[type='search']")]:
                try:
                    search_input = self.wait.until(EC.visibility_of_element_located(selector))
                    logger.info("Search input found using selector: {}".format(selector))
                    break
                except:
                    continue
            
            if not search_input:
                raise Exception("Could not find search input using any known selector.")

            logger.info("Typing Template ID: {}".format(template_id))
            search_input.clear()
            search_input.send_keys(template_id)
            
            # Try to click search button if exists
            try:
                search_btn = self.driver.find_element(By.ID, "searchbtn")
                logger.info("Clicking search button (id='searchbtn')...")
                self._robust_click(search_btn, "search button")
            except:
                logger.info("Search button not found or not clickable, pressing ENTER on input...")
                search_input.send_keys(Keys.ENTER)
            
            time.sleep(3) # Give it extra time for the table to filter

            # 2. Click Actions -> Edit
            logger.info("Looking for Actions dropdown (id='actionDropdownMenu')...")
            actions_btn = self.wait.until(EC.element_to_be_clickable((By.ID, "actionDropdownMenu")))
            self._robust_click(actions_btn, "actions dropdown")

            logger.info("Waiting for Edit option in dropdown...")
            edit_link = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@class, 'dropdown-item') and contains(., 'Edit')]")))
            self._robust_click(edit_link, "edit link")

            logger.info("Waiting for first Continue button (id='step-1-button')...")
            continue_btn = self.wait.until(EC.element_to_be_clickable((By.ID, "step-1-button")))
            self._robust_click(continue_btn, "step-1 continue button")

            # 3. Navigate to "Universal Fields" tab
            logger.info("Clicking on 'Universal Fields' tab...")
            # Using the specific data-tab attribute provided by the user
            universal_tab = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a[data-tab='universal-fields-tab']")))
            self._robust_click(universal_tab, "universal fields tab")
            time.sleep(1)

            # 4. Data Update
            logger.info("Updating currency in 'Universal Fields'...")
            # Use the specific ID 's_currencystyle_1' provided by the user
            currency_dropdown = self.wait.until(EC.presence_of_element_located((By.ID, "s_currencystyle_1")))
            currency_select = Select(currency_dropdown)
            currency_select.select_by_value(currency)
            logger.info("Selected currency: {}".format(currency))

            # Check Card Balance Value (using specifically provided ID and logic)
            try:
                balance_field = self.wait.until(EC.presence_of_element_located((By.ID, "s_currency_1")))
                current_val = str(balance_field.get_attribute("value")).strip()
                logger.info("Current balance (s_currency_1) value: '{}'".format(current_val))
                if current_val == "0":
                    balance_field.clear()
                    logger.info("Cleared balance field because it was '0'.")
                else:
                    logger.info("Kept existing balance value: '{}'".format(current_val))
            except Exception as e:
                logger.warning("Could not handle balance field (s_currency_1): {}".format(e))

            # 5. Save Template
            logger.info("Searching for Save button (submit-form)...")
            save_btn = self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "submit-form")))
            logger.info("Save button found. Clicking robustly...")
            self._robust_click(save_btn, "save button")
            time.sleep(2)

            # 6. Final Modal Push
            try:
                logger.info("Waiting for final 'Update and Continue' modal button (id='add_pass_update')...")
                # Using the specific ID provided by the user for the modal button
                # We use presence instead of clickable first just in case it's covered by a fader
                update_push_btn = self.wait.until(EC.presence_of_element_located((By.ID, "add_pass_update")))
                self._robust_click(update_push_btn, "final modal update button")
            except Exception as e:
                logger.info("Final update button (id='add_pass_update') not found or not clickable: {}".format(e))
            
            logger.info("Template {} update completed successfully!".format(template_id))
            return True

        except Exception as e:
            logger.error("Automation flow failed at template {}: {}".format(template_id, e))
            try:
                curr_url = self.driver.current_url
                logger.error("Failure occurred at URL: {}".format(curr_url))
            except:
                pass
            return False

    def close(self):
        if self.driver:
            self.driver.quit()
            logger.info("Browser closed.")
