import unittest
import re

def parse_email_body(body):
    """Parses the email body to extract Template ID and Currency."""
    template_id_match = re.search(r"Template ID:\s*([A-Za-z0-9]+)", body, re.IGNORECASE)
    currency_match = re.search(r"Reason / Currency to reapply:\s*([A-Z]{3})", body, re.IGNORECASE)

    if template_id_match and currency_match:
        return {
            'template_id': template_id_match.group(1),
            'currency': currency_match.group(1)
        }
    return None

class TestEmailParsing(unittest.TestCase):
    def test_parse_standard_email(self):
        body = """
        Hola Habyt,
        Se ha detectado un cambio.
        Template ID: HABYT12345
        Reason / Currency to reapply: MXN
        Por favor procede con la actualización.
        """
        expected = {'template_id': 'HABYT12345', 'currency': 'MXN'}
        result = parse_email_body(body)
        self.assertEqual(result, expected)

    def test_parse_with_spaces_and_case(self):
        body = "template id:   ABC987\nreason / currency to reapply: USD"
        expected = {'template_id': 'ABC987', 'currency': 'USD'}
        result = parse_email_body(body)
        self.assertEqual(result, expected)

    def test_parse_invalid_body(self):
        body = "This is a random email without the required fields."
        result = parse_email_body(body)
        self.assertIsNone(result)

if __name__ == "__main__":
    unittest.main()
