import os
import base64
import re
import logging
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

logger = logging.getLogger(__name__)

class GmailManager:
    def __init__(self, credentials_path='credentials.json', token_path='token.json'):
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.service = None

    def authenticate(self):
        """Authenticates the user and returns the Gmail API service."""
        creds = None
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_path):
                    raise FileNotFoundError("Credentials file not found at {}".format(self.credentials_path))
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, SCOPES)
                creds = flow.run_local_server(port=0)
            
            with open(self.token_path, 'w') as token:
                token.write(creds.to_json())

        try:
            self.service = build('gmail', 'v1', credentials=creds)
            return self.service
        except HttpError as error:
            logger.error("An error occurred during Gmail authentication: {}".format(error))
            return None

    def get_unread_alerts(self):
        """Fetches unread emails with label 'Alerts Habyt' and specific subject."""
        if not self.service:
            self.authenticate()

        query = 'label:"Alerts Habyt" is:unread subject:"Alerta: Cambio de Balance Inicial"'
        try:
            results = self.service.users().messages().list(userId='me', q=query).execute()
            messages = results.get('messages', [])
            
            alert_data = []
            for msg in messages:
                msg_id = msg['id']
                full_msg = self.service.users().messages().get(userId='me', id=msg_id).execute()
                
                payload = full_msg.get('payload', {})
                body = ""
                
                if 'parts' in payload:
                    for part in payload['parts']:
                        if part['mimeType'] == 'text/plain':
                            body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                            break
                elif 'body' in payload:
                    body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')

                parsed = self.parse_email_body(body)
                if parsed:
                    parsed['id'] = msg_id
                    alert_data.append(parsed)
                else:
                    logger.warning("Could not parse email body for message {}".format(msg_id))

            return alert_data
        except HttpError as error:
            logger.error("An error occurred while fetching emails: {}".format(error))
            return []

    def parse_email_body(self, body):
        """
        Parses the email body to extract Template ID and Currency.
        Expected format includes strings like:
        "Template ID: XYZ123"
        "Reason / Currency to reapply: MXN"
        """
        # Adjusted regex based on prompt description
        template_id_match = re.search(r"Template ID:\s*([A-Za-z0-9]+)", body, re.IGNORECASE)
        currency_match = re.search(r"Reason / Currency to reapply:\s*([A-Z]{3})", body, re.IGNORECASE)

        if template_id_match and currency_match:
            return {
                'template_id': template_id_match.group(1),
                'currency': currency_match.group(1)
            }
        return None

    def mark_as_read(self, msg_id):
        """Marks the processed email as read by removing the UNREAD label."""
        try:
            self.service.users().messages().modify(
                userId='me', 
                id=msg_id, 
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            logger.info("Message {} marked as read.".format(msg_id))
        except HttpError as error:
            logger.error("An error occurred while linking message: {}".format(error))
