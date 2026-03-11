import os
import base64
import re
import logging
import requests
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

        # We search for unread emails from specific senders or with specific labels
        queries = [
            'label:"Alerts Habyt" is:unread',
            'from:hello@solidsens.com is:unread',
            'from:"Habyt Internal Alerts" is:unread'
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

                # Determine Alert Type
                alert_type = 'currency'
                if 'Icono' in subject:
                    alert_type = 'icon'
                elif 'Cuenta Eliminada' in subject:
                    alert_type = 'deletion'

                plain_body = ""
                html_body = ""
                if 'parts' in payload:
                    for part in payload['parts']:
                        if part['mimeType'] == 'text/plain':
                            plain_body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                        elif part['mimeType'] == 'text/html':
                            html_body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                elif 'body' in payload:
                    if payload.get('mimeType') == 'text/html':
                        html_body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
                    else:
                        plain_body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')

                body_for_parsing = html_body if alert_type == 'deletion' else (plain_body if plain_body else html_body)
                parsed = self.parse_email_body(body_for_parsing, alert_type)

                if parsed:
                    parsed['id'] = msg_id
                    parsed['alert_type'] = alert_type
                    
                    # If it's an icon update, download the icon
                    if alert_type == 'icon':
                        # Pass HTML body to download_icon so it can search for <img> tags
                        icon_path = self.download_icon(full_msg, parsed['template_id'], body=html_body)
                        if icon_path:
                            parsed['icon_path'] = icon_path
                        else:
                            logger.error("Failed to download or find icon for Template ID: {}".format(parsed['template_id']))
                            continue # Skip if icon missing or failed
                    
                    alert_data.append(parsed)
                else:
                    snippet = body_for_parsing[:500].replace('\n', ' ') if body_for_parsing else "Empty body"
                    logger.warning("Could not parse email body for message {}. Body snippet: {}".format(msg_id, snippet))
            except Exception as e:
                logger.error("Error retrieving full message {}: {}".format(msg_id, e))

        return alert_data

    def download_icon(self, message, template_id, body="", target_dir='icons'):
        """
        Downloads the image from the message. 
        Checks attachments, inline parts, and HTML body for URLs.
        """
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)

        msg_id = message.get('id')
        payload = message.get('payload', {})
        
        # Helper to process a part
        def process_part(part):
            mime_type = part.get('mimeType', '')
            body_data = part.get('body', {})
            
            if 'image/' in mime_type:
                data = None
                if 'attachmentId' in body_data:
                    attachment_id = body_data['attachmentId']
                    try:
                        attachment = self.service.users().messages().attachments().get(
                            userId='me', messageId=msg_id, id=attachment_id
                        ).execute()
                        data = base64.urlsafe_b64decode(attachment['data'])
                    except Exception as e:
                        logger.error("Error downloading attachment {}: {}".format(attachment_id, e))
                elif 'data' in body_data:
                    data = base64.urlsafe_b64decode(body_data['data'])
                
                if data:
                    filename = "{}.png".format(template_id)
                    filepath = os.path.join(target_dir, filename)
                    with open(filepath, 'wb') as f:
                        f.write(data)
                    logger.info("Downloaded icon (from part) to: {}".format(filepath))
                    return filepath
            
            if 'parts' in part:
                for subpart in part['parts']:
                    res = process_part(subpart)
                    if res: return res
            return None

        # 1. Try parts first
        result = process_part(payload)
        if result: return result

        # 2. Try searching the body for images if no attachment found
        if body:
            # Look for <img> tags
            img_matches = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', body, re.IGNORECASE)
            for src in img_matches:
                # Handle data:image URIs
                if src.startswith('data:image'):
                    try:
                        header, encoded = src.split(",", 1)
                        data = base64.b64decode(encoded)
                        filename = "{}.png".format(template_id)
                        filepath = os.path.join(target_dir, filename)
                        with open(filepath, 'wb') as f:
                            f.write(data)
                        logger.info("Downloaded icon (from data-URI) to: {}".format(filepath))
                        return filepath
                    except Exception as e:
                        logger.error("Failed to decode data-URI icon: {}".format(e))
                
                # Handle remote URLs
                elif src.startswith('http'):
                    # Skip tracking pixels or common icons if necessary, but here we take the first one found in "New Icon Uploaded" context
                    try:
                        resp = requests.get(src, timeout=10)
                        if resp.status_code == 200 and 'image' in resp.headers.get('Content-Type', ''):
                            filename = "{}.png".format(template_id)
                            filepath = os.path.join(target_dir, filename)
                            with open(filepath, 'wb') as f:
                                f.write(resp.content)
                            logger.info("Downloaded icon (from URL: {}) to: {}".format(src, filepath))
                            return filepath
                    except Exception as e:
                        logger.error("Failed to download remote icon from {}: {}".format(src, e))

        return None

    def parse_email_body(self, body, alert_type='currency'):
        """
        Parses the email body to extract Template ID and optionally Currency.
        Supports both English and Spanish labels.
        """
        # Clean HTML tags if present (simple regex approach)
        clean_body = re.sub(r'<[^>]+>', ' ', body)
        # Replace multiple spaces/newlines with a single space for easier regex matching
        clean_body = re.sub(r'\s+', ' ', clean_body).strip()
        
        logger.info("CLEANED BODY FOR PARSING: {}".format(clean_body))

        # Regex for Template ID (English or Spanish)
        template_id_match = re.search(r"(?:Template ID|ID de Plantilla|ID):\s*([A-Za-z0-9]{10,50})", clean_body, re.IGNORECASE)
        
        currency = None
        if alert_type == 'currency':
            # Try to find the pattern "XXX → YYY" first
            arrow_match = re.search(r"\b[A-Z]{3}\b\s*[→→-]\s*\b([A-Z]{3})\b", clean_body)
            if arrow_match:
                currency = arrow_match.group(1)
                logger.info("Found currency via arrow pattern: {}".format(currency))
            
            # Then try specific labels like "New Currency Selected"
            if not currency:
                new_sel_match = re.search(r"New Currency Selected:\s*\b([A-Z]{3})\b", clean_body, re.IGNORECASE)
                if new_sel_match:
                    currency = new_sel_match.group(1)
                    logger.info("Found currency via 'New Currency Selected' pattern: {}".format(currency))

            # Fallback to standard labels
            if not currency:
                label_match = re.search(r"(?:Currency|Moneda|Currency to reapply|Reason / Currency to reapply|Reapply currency):\s*\b([A-Z]{3})\b", clean_body, re.IGNORECASE)
                if label_match:
                    currency = label_match.group(1)
                    logger.info("Found currency via generic label pattern: {}".format(currency))

        if alert_type == 'deletion':
            # Extract Template IDs (usually 40-char hex)
            # Strategy 1: Look for them specifically inside <td> tags if it's HTML
            td_ids = re.findall(r'<td[^>]*>\s*([A-Za-z0-9]{30,64})\s*</td>', body, re.IGNORECASE)
            
            # Strategy 2: Look for them following "ID WalletThat" or "ID" in cleaned body
            # This is a fallback or for plain text
            marker_ids = re.findall(r'(?:ID WalletThat|ID de Plantilla|ID):\s*([A-Za-z0-9]{30,64})', clean_body, re.IGNORECASE)
            
            # Strategy 3: General hex-like strings (40 chars) as a last resort, but filtered
            # We only accept them if they look like the others found or if we found none
            all_found = list(set(td_ids + marker_ids))
            
            if not all_found:
                # Last resort: find anything that looks like a 40-char hex string
                hex_ids = re.findall(r'\b([a-fA-F0-9]{40})\b', clean_body)
                all_found = list(set(hex_ids))

            if all_found:
                logger.info("Found {} IDs in deletion alert: {}".format(len(all_found), all_found))
                return {'template_ids': all_found}
            return None

        if template_id_match:
            template_id = template_id_match.group(1)
            if alert_type == 'icon':
                return {'template_id': template_id}
            elif alert_type == 'currency' and currency:
                return {'template_id': template_id, 'currency': currency}
        
        if not template_id_match:
            logger.warning("Regex failed to find Template ID in cleaned body.")
        if alert_type == 'currency' and not currency:
            logger.warning("Regex failed to find Currency in cleaned body for currency alert.")
            
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
            logger.error("An error occurred while marking message as read: {}".format(error))

    def star_message(self, msg_id):
        """Adds a STAR to the processed email."""
        try:
            self.service.users().messages().modify(
                userId='me', 
                id=msg_id, 
                body={'addLabelIds': ['STARRED']}
            ).execute()
            logger.info("Message {} starred successfully.".format(msg_id))
        except HttpError as error:
            logger.error("An error occurred while starring message: {}".format(error))
