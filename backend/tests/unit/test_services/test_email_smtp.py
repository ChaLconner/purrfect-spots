import os
import smtplib
import unittest
from unittest.mock import MagicMock, patch

# Mock the frontend URL and other envs for testing
os.environ["SMTP_SERVER"] = "smtp.resend.com"
os.environ["SMTP_PORT"] = "587"
os.environ["SMTP_USER"] = "resend"
os.environ["SMTP_PASSWORD"] = os.getenv("SMTP_PASSWORD", "test-only-not-a-real-key")  # nosonar
os.environ["SMTP_SENDER"] = "Purrfect Spots <onboarding@resend.dev>"

from services.email_service import EmailService


class TestEmailServiceSMTP(unittest.TestCase):
    def setUp(self):
        self.service = EmailService()
        self.test_email = "professional_fes@hotmail.com"

    @patch("smtplib.SMTP")
    def test_send_otp_email_success(self, mock_smtp) -> None:
        # Setup mock
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        # Test
        result = self.service.send_otp_email(self.test_email, "123456")

        # Assertions
        self.assertTrue(result)
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("resend", os.environ["SMTP_PASSWORD"])
        mock_server.send_message.assert_called_once()

    @patch("smtplib.SMTP")
    def test_send_otp_email_smtp_error(self, mock_smtp) -> None:
        # Setup mock to raise error
        mock_server = MagicMock()
        mock_server.login.side_effect = smtplib.SMTPAuthenticationError(535, "Authentication failed")
        mock_smtp.return_value.__enter__.return_value = mock_server

        # Test
        result = self.service.send_otp_email(self.test_email, "123456")

        # Assertions
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
