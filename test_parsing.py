import unittest
import re

def parse_email_body(body):
    """Parses the email body to extract Template ID and Currency. (Spanish/HTML support)"""
    clean_body = re.sub(r'<[^>]+>', ' ', body)
    clean_body = re.sub(r'\s+', ' ', clean_body).strip()
    
    template_id_match = re.search(r"(?:Template ID|ID de Plantilla|ID):\s*([A-Za-z0-9]+)", clean_body, re.IGNORECASE)
    currency_match = re.search(r"(?:Currency|Moneda|Currency to reapply):\s*([A-Z]{3})", clean_body, re.IGNORECASE)

    if template_id_match and currency_match:
        return {
            'template_id': template_id_match.group(1),
            'currency': currency_match.group(1)
        }
    return None

class TestEmailParsing(unittest.TestCase):
    def test_parse_spanish_html_email(self):
        body = """
        <div style="color: red;">
        ID de Plantilla: HABYT12345
        Moneda: MXN
        </div>
        """
        expected = {'template_id': 'HABYT12345', 'currency': 'MXN'}
        result = parse_email_body(body)
        self.assertEqual(result, expected)

    def test_parse_with_spaces_and_case(self):
        body = "ID:   ABC987\nMoneda: USD"
        expected = {'template_id': 'ABC987', 'currency': 'USD'}
        result = parse_email_body(body)
        self.assertEqual(result, expected)

    def test_parse_invalid_body(self):
        body = "This is a random email without the required fields."
        result = parse_email_body(body)
        self.assertIsNone(result)

if __name__ == "__main__":
    unittest.main()
