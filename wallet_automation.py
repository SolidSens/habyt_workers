import os
import time
import logging
import random
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
            import traceback
            error_str = str(e).lower()
            
            # Log full traceback for debugging
            logger.error("Chrome browser initialization failed:")
            logger.error(traceback.format_exc())
            
            if "user data directory is already in use" in error_str:
                logger.error("CHROME ERROR: The Chrome profile you specified is already open.")
                logger.error("FIX: Either close Chrome, or use the 'Remote Debugging' method (see walkthrough).")
                raise Exception("Chrome profile is already in use. Close Chrome or use remote debugging mode.")
            
            elif "cannot connect to chrome" in error_str or "chrome not reachable" in error_str:
                if self.debugger_address:
                    logger.error("CHROME ERROR: Cannot connect to Chrome at {}".format(self.debugger_address))
                    logger.error("FIX: Start Chrome with remote debugging enabled:")
                    logger.error("  chrome --remote-debugging-port={}".format(self.debugger_address.split(':')[1]))
                    raise Exception("Cannot connect to Chrome at {}. Make sure Chrome is running with --remote-debugging-port enabled.".format(self.debugger_address))
                else:
                    logger.error("CHROME ERROR: Failed to launch Chrome browser.")
                    raise Exception("Failed to launch Chrome browser. Check your CHROME_USER_DATA_DIR and CHROME_BINARY_PATH settings.")
            
            else:
                # Re-raise other exceptions as-is
                raise e

    def _human_delay(self, min_seconds=1.0, max_seconds=3.0):
        """Introduces a randomized delay to mimic human behavior."""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)

    def _robust_click(self, element, description="element"):
        """Tries to click an element, falls back to JS click if obstructed."""
        if not self.driver:
            return
        
        self._human_delay(0.5, 1.5) # Wait before clicking
        try:
            # Scroll into view
            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
            self._human_delay(0.8, 1.2)
            element.click()
            logger.info("Successfully clicked {}.".format(description))
        except Exception as e:
            logger.warning("Standard click failed for {}, trying JavaScript click. Error: {}".format(description, e))
            self.driver.execute_script("arguments[0].click();", element)
            logger.info("Successfully clicked {} via JavaScript.".format(description))
        self._human_delay(0.5, 1.5) # Wait after clicking

    def _verify_success(self, template_id, action="update", timeout=15):
        """Wait until the URL contains 'success=' or 'message=' to verify the action completed."""
        if not self.driver:
            return False
            
        logger.info("Waiting for success redirect for Template ID: {} ({})...".format(template_id, action))
        start_time = time.time()
        while time.time() - start_time < timeout:
            current_url = self.driver.current_url
            if "success=" in current_url or "message=" in current_url:
                logger.info("Success! Redirect detected for {}: {}".format(template_id, current_url))
                return True
            time.sleep(1)
        
        final_url = self.driver.current_url
        logger.warning("Timed out waiting for success redirect for {}. Final URL: {}".format(template_id, final_url))
        # If we see the success string even after timeout (e.g. slow load), return True
        return "success=" in final_url or "message=" in final_url

    def ensure_logged_in(self):
        """Checks if logged out and performs login if necessary."""
        if not self.driver:
            self.start_browser()
        
        target_url = "https://app.walletthat.com/platform/wallet/pass-templates.php"
        
        # Check current URL or presence of login button
        login_btn_selector = (By.CSS_SELECTOR, "button[title='Click here to login'], button[aria-label='Click to login']")
        
        try:
            # First, check if login button exists on current page or login page
            login_buttons = self.driver.find_elements(*login_btn_selector)
            if login_buttons:
                logger.info("Login button detected. Session may have expired. Clicking Login...")
                self._robust_click(login_buttons[0], "login button")
                self._human_delay(2.0, 4.0)
                
                # After login click, check for obstructive modals
                close_btn_selector = (By.CSS_SELECTOR, "button.btn-close[data-bs-dismiss='modal'], .modal-footer button[data-bs-dismiss='modal']")
                try:
                    self._human_delay(1.0, 2.0)
                    close_buttons = self.driver.find_elements(*close_btn_selector)
                    for btn in close_buttons:
                        if btn.is_displayed():
                            logger.info("Closing obstructive modal...")
                            self._robust_click(btn, "modal close button")
                            self._human_delay(0.5, 1.0)
                except:
                    pass
            
            # Final check: are we on the target page?
            if target_url not in self.driver.current_url:
                logger.info("Not on templates page. Navigating to: {}".format(target_url))
                self.driver.get(target_url)
                self._human_delay(2.0, 4.0)
                
        except Exception as e:
            logger.error("Error during ensure_logged_in: {}".format(e))
            # Fallback re-navigation
            if self.driver:
                self.driver.get(target_url)
            self._human_delay(2.0, 4.0)

    def _search_template(self, template_id):
        """Searches for a template ID on the templates page."""
        self.ensure_logged_in()
        
        if not self.driver:
            return False
            
        if self.driver and not self.wait:
            self.wait = WebDriverWait(self.driver, 20)

        url = "https://app.walletthat.com/platform/wallet/pass-templates.php"
        if self.driver and self.driver.current_url != url:
            logger.info("Navigating to: {}".format(url))
            self.driver.get(url)
            self._human_delay(1.5, 3.0)
        
        logger.info("Searching for Template ID: {}".format(template_id))
        search_input = None
        for selector in [(By.ID, "searchtxt"), (By.CSS_SELECTOR, "input[type='search']")]:
            try:
                search_input = self.wait.until(EC.visibility_of_element_located(selector))
                break
            except:
                continue
        
        if not search_input:
            raise Exception("Could not find search input.")

        search_input.clear()
        search_input.send_keys(template_id)
        
        try:
            search_btn = self.driver.find_element(By.ID, "searchbtn")
            self._robust_click(search_btn, "search button")
        except:
            search_input.send_keys(Keys.ENTER)
        
        self._human_delay(2.0, 4.0)
        return True

    def _navigate_to_edit(self, template_id):
        """Common logic to navigate to the Edit page of a template."""
        self._search_template(template_id)

        # Click Actions -> Edit
        actions_btn = self.wait.until(EC.element_to_be_clickable((By.ID, "actionDropdownMenu")))
        self._robust_click(actions_btn, "actions dropdown")

        edit_link = self.wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Edit")))
        self._robust_click(edit_link, "edit link")
        
        # Step 1 Continue
        continue_btn = self.wait.until(EC.element_to_be_clickable((By.ID, "step-1-button")))
        self._robust_click(continue_btn, "step 1 continue button")
        time.sleep(2)
        return True

    def update_template(self, template_id, currency):
        """Perform the update flow for a specific template."""
        try:
            self._navigate_to_edit(template_id)

            # 3. Navigate to "Universal Fields" tab
            logger.info("Clicking on 'Universal Fields' tab...")
            universal_tab = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a[data-tab='universal-fields-tab']")))
            self._robust_click(universal_tab, "universal fields tab")
            time.sleep(1)

            # 4. Data Update
            logger.info("Updating currency in 'Universal Fields'...")
            currency_dropdown = self.wait.until(EC.presence_of_element_located((By.ID, "s_currencystyle_1")))
            currency_select = Select(currency_dropdown)
            currency_select.select_by_value(currency)
            logger.info("Selected currency: {}".format(currency))

            # Check Card Balance Value
            try:
                balance_field = self.wait.until(EC.presence_of_element_located((By.ID, "s_currency_1")))
                current_val = str(balance_field.get_attribute("value")).strip()
                if current_val == "0":
                    balance_field.clear()
                    logger.info("Cleared balance field because it was '0'.")
            except Exception as e:
                logger.warning("Could not handle balance field (s_currency_1): {}".format(e))

            # 5. Save Template
            save_btn = self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "submit-form")))
            self._robust_click(save_btn, "save button")
            time.sleep(2)

            # 6. Final Modal Push (Optional)
            try:
                temp_wait = WebDriverWait(self.driver, 5)
                update_push_btn = temp_wait.until(EC.presence_of_element_located((By.ID, "add_pass_update")))
                self._robust_click(update_push_btn, "final modal update button")
                time.sleep(2)
            except Exception:
                pass

            # 7. Final Success Verification
            return self._verify_success(template_id, action="currency update")

        except Exception as e:
            logger.error("Automation flow failed at template {}: {}".format(template_id, e))
            return False

    def update_icon(self, template_id, icon_path):
        """Updates the icon for a specific template."""
        try:
            logger.info("Starting icon update for Template ID: {}".format(template_id))
            self._navigate_to_edit(template_id)

            # 5. Click "Apple Wallet Fields" Tab
            apple_tab = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a[data-tab='apple-wallet-tab']")))
            self._robust_click(apple_tab, "Apple Wallet Fields tab")
            time.sleep(2)

            # 6. Delete Old Icon
            try:
                delete_btn = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'img[src*="delBtn.png"]')))
                self._robust_click(delete_btn, "delete icon button")
                logger.info("Deleted old icon.")
                time.sleep(1)
            except Exception as e:
                logger.info("Delete icon button not found or not needed.")

            # 7. Upload New PNG
            try:
                abs_icon_path = os.path.abspath(icon_path)
                logger.info("Uploading icon from: {}".format(abs_icon_path))
                file_input = self.driver.find_element(By.ID, "iconToUpload")
                file_input.send_keys(abs_icon_path)
                logger.info("Upload command sent successfully.")
                time.sleep(2)
            except Exception as e:
                logger.error("Failed to upload icon: {}".format(e))
                return False

            # 8. Click Save Pass Template
            save_btn = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.submit-form")))
            self._robust_click(save_btn, "save button")
            time.sleep(2)

            # 9. Final Modal Push (Optional)
            try:
                temp_wait = WebDriverWait(self.driver, 5)
                update_push_btn = temp_wait.until(EC.presence_of_element_located((By.ID, "add_pass_update")))
                self._robust_click(update_push_btn, "final modal update button")
                time.sleep(2)
            except Exception:
                pass

            # 10. Success Verification
            return self._verify_success(template_id, action="icon update")

        except Exception as e:
            logger.error("Icon update flow failed for template {}: {}".format(template_id, e))
            return False

    def delete_template(self, template_id):
        """Performs the deletion flow for a specific template."""
        try:
            logger.info("Starting deletion for Template ID: {}".format(template_id))
            self._search_template(template_id)

            # 2. Click Actions -> Delete
            actions_btn = self.wait.until(EC.element_to_be_clickable((By.ID, "actionDropdownMenu")))
            self._robust_click(actions_btn, "actions dropdown")

            delete_link = self.wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Delete")))
            self._robust_click(delete_link, "delete link")
            
            # 3. Handle Browser Confirmation Alert
            time.sleep(1)
            try:
                alert = self.driver.switch_to.alert
                logger.info("Alert text: {}".format(alert.text))
                alert.accept()
                logger.info("Accepted browser deletion alert.")
            except Exception as e:
                logger.warning("No browser alert found or failed to accept: {}".format(e))
            
            time.sleep(2)

            # 4. Success Verification
            return self._verify_success(template_id, action="deletion")

        except Exception as e:
            logger.error("Deletion flow failed for template {}: {}".format(template_id, e))
            return False

    def close(self):
        if self.driver:
            self.driver.quit()
            logger.info("Browser closed.")
