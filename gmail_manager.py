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
        """Fetches unread emails using a broader query and logs details for debugging."""
        if not self.service:
            self.authenticate()

        # Debug: List all labels to verify names
        try:
            results = self.service.users().labels().list(userId='me').execute()
            labels = results.get('labels', [])
            label_names = [l['name'] for l in labels]
            logger.info("Available Gmail labels: {}".format(", ".join(label_names)))
        except Exception as e:
            logger.error("Could not list labels: {}".format(e))

        # Try a broader query that doesn't strictly depend on the label first
        # subject:"Alerta: Cambio" is the core filter
        # from:hello@solidsens.com is the core sender
        queries = [
            'label:"Alerts Habyt" is:unread subject:"Alerta: Cambio"',
            'from:hello@solidsens.com is:unread subject:"Alerta: Cambio"'
        ]
        
        all_messages = []
        for query in queries:
            try:
                logger.info("Searching with query: {}".format(query))
                results = self.service.users().messages().list(userId='me', q=query).execute()
                messages = results.get('messages', [])
                logger.info("Found {} messages with this query.".format(len(messages)))
                all_messages.extend(messages)
            except HttpError as error:
                logger.error("An error occurred during search: {}".format(error))

        # Remove duplicates based on ID
        unique_msg_ids = set()
        unique_messages = []
        for msg in all_messages:
            if msg['id'] not in unique_msg_ids:
                unique_msg_ids.add(msg['id'])
                unique_messages.append(msg)

        alert_data = []
        for msg in unique_messages:
            msg_id = msg['id']
            try:
                full_msg = self.service.users().messages().get(userId='me', id=msg_id).execute()
                
                payload = full_msg.get('payload', {})
                headers = payload.get('headers', [])
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), "No Subject")
                logger.info("Processing message ID: {}, Subject: {}".format(msg_id, subject))

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
                    logger.warning("Could not parse email body for message {}. Body snippet: {}".format(msg_id, body[:500].replace('\n', ' ')))
            except Exception as e:
                logger.error("Error retrieving full message {}: {}".format(msg_id, e))

        return alert_data

    def parse_email_body(self, body):
        """
        Parses the email body to extract Template ID and Currency.
        Supports both English and Spanish labels.
        Example labels: "Template ID", "ID de Plantilla", "Currency", "Moneda".
        """
        # Clean HTML tags if present (simple regex approach)
        clean_body = re.sub(r'<[^>]+>', ' ', body)
        # Replace multiple spaces/newlines with a single space for easier regex matching
        clean_body = re.sub(r'\s+', ' ', clean_body).strip()
        
        logger.info("CLEANED BODY FOR PARSING: {}".format(clean_body))

        # Regex for Template ID (English or Spanish)
        # Matches: "Template ID: XYZ", "ID de Plantilla: XYZ", etc.
        template_id_match = re.search(r"(?:Template ID|ID de Plantilla|ID):\s*([A-Za-z0-9]{10,50})", clean_body, re.IGNORECASE)
        
        # Regex for Currency (English or Spanish)
        # We look for exactly 3 letters (MXN, USD, etc) surrounded by boundaries or at the end
        # We avoid matching "Cur" from "Currency" by ensuring it's not the start of a longer word
        currency_match = re.search(r"(?:Currency|Moneda|Currency to reapply):\s*\b([A-Z]{3})\b", clean_body, re.IGNORECASE)

        if template_id_match and currency_match:
            return {
                'template_id': template_id_match.group(1),
                'currency': currency_match.group(1)
            }
        
        if not template_id_match:
            logger.warning("Regex failed to find Template ID in cleaned body.")
        if not currency_match:
            logger.warning("Regex failed to find Currency/Moneda in cleaned body.")
            
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
