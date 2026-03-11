import requests
import logging
import html
import re

logger = logging.getLogger(__name__)

class TelegramNotifier:
    def __init__(self, token=None, chat_id=None):
        self.token = token
        # Convert chat_id to int if it's a numeric string (Telegram API prefers int)
        if chat_id:
            try:
                self.chat_id = int(chat_id) if str(chat_id).isdigit() else chat_id
            except (ValueError, TypeError):
                self.chat_id = chat_id
        else:
            self.chat_id = None
        self.base_url = "https://api.telegram.org/bot{}/sendMessage".format(token) if token else None

    def send_message(self, text):
        if not self.token or not self.chat_id:
            logger.warning("Telegram configuration missing.")
            return False

        # Ensure text is not empty and not too long (Telegram limit is 4096 characters)
        if not text:
            logger.warning("Cannot send empty message.")
            return False
        
        if len(text) > 4096:
            logger.warning(f"Message too long ({len(text)} chars), truncating to 4096.")
            text = text[:4093] + "..."

        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML"
        }

        response = None
        try:
            # First attempt with HTML formatting
            response = requests.post(self.base_url, json=payload, timeout=10)
            
            # If we get a 400 error, try to get more details and retry without HTML
            if response.status_code == 400:
                try:
                    error_data = response.json()
                    error_description = error_data.get('description', 'Unknown error')
                    logger.warning(f"Telegram API 400 error: {error_description}")
                    
                    # If it's an HTML parsing error, retry without HTML
                    if 'parse' in error_description.lower() or 'html' in error_description.lower():
                        logger.warning("HTML parsing error detected. Retrying with plain text...")
                        plain_text = re.sub(r'<[^>]+>', '', text)
                        # Also decode HTML entities
                        plain_text = html.unescape(plain_text)
                        payload["text"] = plain_text
                        del payload["parse_mode"]
                        response = requests.post(self.base_url, json=payload, timeout=10)
                    else:
                        # Log the full error for other types of 400 errors
                        logger.error(f"Telegram API error response: {error_data}")
                        return False
                except (ValueError, KeyError):
                    # If we can't parse the error response, log the raw text
                    logger.error(f"Telegram API 400 error (unparseable): {response.text}")
                    # Try retry without HTML anyway
                    plain_text = re.sub(r'<[^>]+>', '', text)
                    plain_text = html.unescape(plain_text)
                    payload["text"] = plain_text
                    if "parse_mode" in payload:
                        del payload["parse_mode"]
                    response = requests.post(self.base_url, json=payload, timeout=10)

            response.raise_for_status()
            logger.info("Notificación enviada con éxito.")
            return True
        except requests.exceptions.RequestException as e:
            # Network or HTTP errors
            if response is not None:
                try:
                    error_data = response.json()
                    error_description = error_data.get('description', response.text)
                    logger.error(f"Telegram API error: {error_description} (Status: {response.status_code})")
                except (ValueError, AttributeError):
                    logger.error(f"Telegram request failed: {response.text if response else str(e)}")
            else:
                logger.error(f"Telegram request failed (no response): {str(e)}")
            return False
        except Exception as e:
            # Unexpected errors
            logger.error(f"Unexpected error sending Telegram message: {str(e)}")
            return False
    
    def notify_success(self, alert_type, template_id, extra_info=""):
        """Sends a success notification."""
        emoji = "✅" if alert_type != 'deletion' else "🗑️"
        message = "<b>{} Habyt Worker Success</b>\n\n".format(emoji)
        message += "<b>Type:</b> {}\n".format(html.escape(str(alert_type).capitalize()))
        message += "<b>Template ID:</b> <code>{}</code>\n".format(html.escape(str(template_id)))
        if extra_info:
            message += "<b>Info:</b> {}\n".format(html.escape(str(extra_info)))
        
        return self.send_message(message)

    def notify_failure(self, alert_type, template_id, error_msg=""):
        """Sends a failure notification."""
        message = "<b>❌ Habyt Worker FAILURE</b>\n\n"
        message += "<b>Type:</b> {}\n".format(html.escape(str(alert_type).capitalize()))
        message += "<b>Template ID:</b> <code>{}</code>\n".format(html.escape(str(template_id)))
        if error_msg:
            # Shorten and escape error message
            safe_error = html.escape(str(error_msg))[:200]
            message += "<b>Error:</b> <i>{}</i>\n".format(safe_error)
        
        return self.send_message(message)

    def notify_job_summary(self, total, success_count, failure_count):
        """Sends a job summary notification."""
        message = "<b>📊 Habyt Worker Job Summary</b>\n\n"
        message += "<b>Total Processed:</b> {}\n".format(total)
        message += "<b>Success:</b> {}\n".format(success_count)
        message += "<b>Failures:</b> {}\n".format(failure_count)
        
        if failure_count > 0:
            message += "\n⚠️ Some alerts failed to process. Check logs for details."
            
        return self.send_message(message)
