import unittest
import re

def parse_email_body(body, alert_type='currency'):
    """Parses the email body to extract Template ID and optionally Currency."""
    # Clean HTML tags if present (simple regex approach)
    clean_body = re.sub(r'<[^>]+>', ' ', body)
    # Replace multiple spaces/newlines with a single space for easier regex matching
    clean_body = re.sub(r'\s+', ' ', clean_body).strip()
    
    # Regex for Template ID (English or Spanish)
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

    if alert_type == 'deletion':
        # Extract all template IDs from the table (hex pattern)
        ids = re.findall(r'\b([A-Za-z0-9]{30,64})\b', clean_body)
        unique_ids = list(set(ids))
        if unique_ids:
            return {'template_ids': unique_ids}
        return None

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

    def test_parse_reapply_currency_format(self):
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

    def test_parse_deletion_alert_multiple_ids(self):
        body = """
        <html>
        <body>
            <h3>Listado de Templates Eliminados</h3>
            <table>
                <tr><th>ID WalletThat</th><th>Nombre</th></tr>
                <tr><td>5b48bf2afbbe333452a19858f7f1604bd3d9e6fa</td><td>Template 1</td></tr>
                <tr><td>8eb2f7a9d0c1b2e3f4a5b6c7d8e9f0a1b2c3d4e5</td><td>Template 2</td></tr>
            </table>
        </body>
        </html>
        """
        result = parse_email_body(body, alert_type='deletion')
        self.assertIsNotNone(result)
        self.assertIn('template_ids', result)
        self.assertEqual(len(result['template_ids']), 2)
        self.assertIn('5b48bf2afbbe333452a19858f7f1604bd3d9e6fa', result['template_ids'])
        self.assertIn('8eb2f7a9d0c1b2e3f4a5b6c7d8e9f0a1b2c3d4e5', result['template_ids'])

    def test_parse_reduction_alert_multiple_ids(self):
        body = """
        <html>
        <body>
            <h3>Alerta: Reducción de Plan</h3>
            <p>Listado de Templates Eliminados</p>
            <table>
                <tr><td>ID WalletThat</td></tr>
                <tr><td>abcd1234efgh5678ijkl9012mnop3456qrst5678</td></tr>
            </table>
        </body>
        </html>
        """
        result = parse_email_body(body, alert_type='deletion')
        self.assertIsNotNone(result)
        self.assertEqual(len(result['template_ids']), 1)
        self.assertEqual(result['template_ids'][0], 'abcd1234efgh5678ijkl9012mnop3456qrst5678')

    def test_parse_invalid_body(self):
        body = "This is a random email without the required fields."
        result = parse_email_body(body)
        self.assertIsNone(result)

if __name__ == "__main__":
    unittest.main()
