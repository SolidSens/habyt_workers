import unittest
import re

def parse_email_body(body):
    """Parses the email body to extract Template ID and Currency. (Spanish/HTML support)"""
    # Clean HTML tags if present (simple regex approach)
    clean_body = re.sub(r'<[^>]+>', ' ', body)
    # Replace multiple spaces/newlines with a single space for easier regex matching
    clean_body = re.sub(r'\s+', ' ', clean_body).strip()
    
    # Regex for Template ID
    template_id_match = re.search(r"(?:Template ID|ID de Plantilla|ID):\s*([A-Za-z0-9]{10,50})", clean_body, re.IGNORECASE)
    
    currency = None
    # Try to find the pattern "XXX → YYY" first
    arrow_match = re.search(r"\b[A-Z]{3}\b\s*[→→-]\s*\b([A-Z]{3})\b", clean_body)
    if arrow_match:
        currency = arrow_match.group(1)
    else:
        # Fallback to standard labels
        label_match = re.search(r"(?:Currency|Moneda|Currency to reapply|New Currency Selected):\s*\b([A-Z]{3})\b", clean_body, re.IGNORECASE)
        if label_match:
            currency = label_match.group(1)

    if template_id_match and currency:
        return {
            'template_id': template_id_match.group(1),
            'currency': currency
        }
    return None

class TestEmailParsing(unittest.TestCase):
    def test_parse_spanish_html_email(self):
        body = """
        <div style="color: red;">
        ID de Plantilla: 9ceed34b710db8a635cd16fba323bad217343c93
        Moneda: MXN
        </div>
        """
        expected = {'template_id': '9ceed34b710db8a635cd16fba323bad217343c93', 'currency': 'MXN'}
        result = parse_email_body(body)
        self.assertEqual(result, expected)

    def test_parse_new_currency_selected(self):
        body = "Template ID: 9ceed34b710db8a635cd16fba323bad217343c93\nNew Currency Selected: EUR"
        expected = {'template_id': '9ceed34b710db8a635cd16fba323bad217343c93', 'currency': 'EUR'}
        result = parse_email_body(body)
        self.assertEqual(result, expected)

    def test_parse_arrow_format(self):
        body = "ID: 9ceed34b710db8a635cd16fba323bad217343c93 Currency Changed: USD → MXN"
        expected = {'template_id': '9ceed34b710db8a635cd16fba323bad217343c93', 'currency': 'MXN'}
        result = parse_email_body(body)
        self.assertEqual(result, expected)

    def test_parse_invalid_body(self):
        body = "This is a random email without the required fields."
        result = parse_email_body(body)
        self.assertIsNone(result)

if __name__ == "__main__":
    unittest.main()
