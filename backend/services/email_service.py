
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from logger import logger

class EmailService:
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.sender_email = os.getenv("SMTP_SENDER", self.smtp_user)
        self.frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")

    def send_reset_email(self, to_email: str, token: str) -> bool:
        """
        Send password reset email
        """
        if not self.smtp_user or not self.smtp_password:
            logger.warning("SMTP credentials not set. Skipping email send.")
            # For dev: still logging the token
            print(f"============================================")
            print(f"PASSWORD RESET LINK: {self.frontend_url}/reset-password?token={token}")
            print(f"============================================")
            return True

        try:
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = to_email
            msg['Subject'] = "Reset Your Password - Purrfect Spots"

            reset_link = f"{self.frontend_url}/reset-password?token={token}"

            body = f"""
            <html>
              <body style="font-family: Arial, sans-serif; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #eee; border-radius: 10px;">
                    <h2 style="color: #7FB7A4;">Purrfect Spots</h2>
                    <p>Hello,</p>
                    <p>We received a request to reset your password. Click the button below to choose a new one:</p>
                    <a href="{reset_link}" style="display: inline-block; background-color: #7FB7A4; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin: 20px 0;">Reset Password</a>
                    <p style="font-size: 0.9em; color: #777;">If you didn't ask to reset your password, you can ignore this email.</p>
                    <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                    <p style="font-size: 0.8em; color: #999;">Or copy this link: {reset_link}</p>
                </div>
              </body>
            </html>
            """

            msg.attach(MIMEText(body, 'html'))

            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.smtp_user, self.smtp_password)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Reset password email sent to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False

email_service = EmailService()
