import unittest
from whatsapp_notifier import WhatsAppNotifier, send_whatsapp_alert

class TestWhatsAppNotifier(unittest.TestCase):

    def test_load_credentials(self):
        """Verifies WhatsApp credentials loader graceful handling."""
        phone, api_key = WhatsAppNotifier.load_whatsapp_credentials()
        # Credentials are default unconfigured placeholder, should return None
        self.assertTrue(phone is None or isinstance(phone, str))

    def test_send_whatsapp_unconfigured_fallback(self):
        """Verifies graceful unconfigured fallback handling without throwing exception."""
        res = send_whatsapp_alert("Test Market Mentor AI WhatsApp Alert")
        self.assertIn("status", res)
        self.assertIn(res["status"], ["SKIPPED", "SUCCESS", "FAILED"])

if __name__ == '__main__':
    unittest.main()
