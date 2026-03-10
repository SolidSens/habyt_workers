import unittest
import re

def parse_email_body(body, alert_type='currency'):
    """Parses the email body to extract Template ID and optionally Currency."""
    # Clean HTML tags if present (simple regex approach)
    clean_body = re.sub(r'<[^>]+>', ' ', body)
    # Replace multiple spaces/newlines with a single space for easier regex matching
    clean_body = re.sub(r'\s+', ' ', clean_body).strip()
    
    # Regex for Template ID
    template_id_match = re.search(r"(?:Template ID|ID de Plantilla|ID):\s*([A-Za-z0-9]{10,50})", clean_body, re.IGNORECASE)
    
    currency = None
    if alert_type == 'currency':
        # Try to find the pattern "XXX → YYY" first
        arrow_match = re.search(r"\b[A-Z]{3}\b\s*[→→-]\s*\b([A-Z]{3})\b", clean_body)
        if arrow_match:
            currency = arrow_match.group(1)
        
        # Then try specific labels like "New Currency Selected"
        if not currency:
            new_sel_match = re.search(r"New Currency Selected:\s*\b([A-Z]{3})\b", clean_body, re.IGNORECASE)
            if new_sel_match:
                currency = new_sel_match.group(1)

        # Fallback to standard labels
        if not currency:
            label_match = re.search(r"(?:Currency|Moneda|Currency to reapply|Reason / Currency to reapply|Reapply currency):\s*\b([A-Z]{3})\b", clean_body, re.IGNORECASE)
            if label_match:
                currency = label_match.group(1)

    if template_id_match:
        template_id = template_id_match.group(1)
        if alert_type == 'icon':
            return {'template_id': template_id}
        elif alert_type == 'currency' and currency:
            return {'template_id': template_id, 'currency': currency}
    return None

class TestEmailParsing(unittest.TestCase):
    def test_parse_spanish_html_email(self):
        body = "<p>ID de Plantilla: 9ceed34b710db8a635cd16fba323bad217343c93</p><p>Moneda: MXN</p>"
        expected = {'template_id': '9ceed34b710db8a635cd16fba323bad217343c93', 'currency': 'MXN'}
        result = parse_email_body(body)
        self.assertEqual(result, expected)

    def test_parse_new_currency_selected(self):
        body = "Template ID: 9ceed34b710db8a635cd16fba323bad217343c93\nNew Currency Selected: MXN"
        expected = {'template_id': '9ceed34b710db8a635cd16fba323bad217343c93', 'currency': 'MXN'}
        result = parse_email_body(body)
        self.assertEqual(result, expected)

    def test_parse_nested_currency_labels(self):
        # This simulates the case where "Currency:" is followed by "New Currency Selected: MXN"
        body = "Template ID: 9ceed34b710db8a635cd16fba323bad217343c93\nCurrency: New Currency Selected: MXN"
        expected = {'template_id': '9ceed34b710db8a635cd16fba323bad217343c93', 'currency': 'MXN'}
        result = parse_email_body(body)
        self.assertEqual(result, expected)

    def test_parse_reapply_currency_format(self):
        # This simulates the "Alerta: Cambio de Balance Inicial" format
        body = """
        Template ID: 9ceed34b710db8a635cd16fba323bad217343c93
        Reason / Currency to reapply: Balance Inicial de Tarjeta changed. Wallet reverts to USD. Reapply currency: AUD
        """
        expected = {'template_id': '9ceed34b710db8a635cd16fba323bad217343c93', 'currency': 'AUD'}
        result = parse_email_body(body)
        self.assertEqual(result, expected)

    def test_parse_icon_alert(self):
        body = "Template ID: 9ceed34b710db8a635cd16fba323bad217343c93\nNew Icon Uploaded"
        expected = {'template_id': '9ceed34b710db8a635cd16fba323bad217343c93'}
        result = parse_email_body(body, alert_type='icon')
        self.assertEqual(result, expected)

    def test_parse_invalid_body(self):
        body = "This is a random email without the required fields."
        result = parse_email_body(body)
        self.assertIsNone(result)

if __name__ == "__main__":
    unittest.main()
