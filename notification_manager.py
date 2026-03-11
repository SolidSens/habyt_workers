import requests
import logging

logger = logging.getLogger(__name__)

class TelegramNotifier:
    def __init__(self, token=None, chat_id=None):
        self.token = token
        self.chat_id = chat_id
        self.base_url = "https://api.telegram.org/bot{}/sendMessage".format(token) if token else None

    def send_message(self, text):
        """Sends a telegram message."""
        if not self.token or not self.chat_id:
            logger.warning("Telegram configuration missing. Skipping notification.")
            return False

        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "HTML"
        }

        try:
            response = requests.post(self.base_url, json=payload, timeout=10)
            response.raise_for_status()
            logger.info("Telegram notification sent successfully.")
            return True
        except Exception as e:
            logger.error("Failed to send Telegram notification: {}".format(e))
            return False

    def notify_success(self, alert_type, template_id, extra_info=""):
        """Sends a success notification."""
        emoji = "✅" if alert_type != 'deletion' else "🗑️"
        message = "<b>{} Habyt Worker Success</b>\n\n".format(emoji)
        message += "<b>Type:</b> {}\n".format(alert_type.capitalize())
        message += "<b>Template ID:</b> <code>{}</code>\n".format(template_id)
        if extra_info:
            message += "<b>Info:</b> {}\n".format(extra_info)
        
        return self.send_message(message)

    def notify_failure(self, alert_type, template_id, error_msg=""):
        """Sends a failure notification."""
        message = "<b>❌ Habyt Worker FAILURE</b>\n\n"
        message += "<b>Type:</b> {}\n".format(alert_type.capitalize())
        message += "<b>Template ID:</b> <code>{}</code>\n".format(template_id)
        if error_msg:
            message += "<b>Error:</b> <i>{}</i>\n".format(error_msg)
        
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
