import unittest
from run_telegram_bot_listener import load_telegram_credentials, send_telegram_reply

class TestTelegramListener(unittest.TestCase):

    def test_load_credentials(self):
        """Verifies Telegram Bot Token and Chat ID load from config.json or env."""
        token, chat_id = load_telegram_credentials()
        self.assertIsNotNone(token)
        self.assertIsNotNone(chat_id)
        self.assertTrue(len(token) > 10)

    def test_send_telegram_reply(self):
        """Verifies active sending of reply messages to Telegram."""
        token, chat_id = load_telegram_credentials()
        res = send_telegram_reply(token, chat_id, "🤖 *Market Mentor AI* 2-Way Interactive Bot Connected Successfully!")
        self.assertTrue(res)

if __name__ == '__main__':
    unittest.main()
