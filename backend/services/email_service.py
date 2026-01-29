import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from logger import logger


class EmailService:
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.sender_email = os.getenv("SMTP_SENDER") or self.smtp_user or "noreply@purrfectspots.com"
        self.frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")

    def send_reset_email(self, to_email: str, token: str) -> bool:
        """
        Send password reset email
        """
        if not self.smtp_user or not self.smtp_password:
            logger.warning("SMTP credentials not set. Skipping email send.")
            # For dev: log the token at debug level
            logger.debug("============================================")
            logger.debug(f"PASSWORD RESET LINK: {token}")
            logger.debug("============================================")
            return True

        try:
            msg = MIMEMultipart()
            msg["From"] = self.sender_email
            msg["To"] = to_email
            msg["Subject"] = "Reset Your Password - Purrfect Spots"

            # The token is the full Action Link from Supabase (including redirect_to)
            reset_link = token

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

            msg.attach(MIMEText(body, "html"))

            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.smtp_user, self.smtp_password)
            server.send_message(msg)
            server.quit()

            logger.info(f"Reset password email sent to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {e!s}")
            return False

    def send_confirmation_email(self, to_email: str, confirmation_link: str) -> bool:
        """
        Send confirmation email for new signup
        """
        if not self.smtp_user or not self.smtp_password:
            logger.warning("SMTP credentials not set. Skipping email send.")
            logger.debug("============================================")
            logger.debug(f"CONFIRMATION LINK: {confirmation_link}")
            logger.debug("============================================")
            return True

        try:
            msg = MIMEMultipart()
            msg["From"] = self.sender_email
            msg["To"] = to_email
            msg["Subject"] = "Welcome to Purrfect Spots! Please Confirm Your Email"

            body = f"""
            <html>
              <body style="font-family: Arial, sans-serif; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #eee; border-radius: 10px;">
                    <h2 style="color: #7FB7A4;">Welcome to Purrfect Spots!</h2>
                    <p>Hello,</p>
                    <p>Thank you for joining Purrfect Spots. We're excited to have you!</p>
                    <p>Please confirm your email address by clicking the button below:</p>
                    <a href="{confirmation_link}" style="display: inline-block; background-color: #7FB7A4; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin: 20px 0;">Confirm Email</a>
                    <p style="font-size: 0.9em; color: #777;">If you did not sign up for this account, please ignore this email.</p>
                    <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                    <p style="font-size: 0.8em; color: #999;">Or copy this link: {confirmation_link}</p>
                </div>
              </body>
            </html>
            """

            msg.attach(MIMEText(body, "html"))

            # Add timeout to prevent hanging
            server = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=10)
            server.starttls()
            server.login(self.smtp_user, self.smtp_password)
            server.send_message(msg)
            server.quit()

            logger.info(f"Confirmation email sent to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send confirmation email: {e!s}")
            logger.debug(f"EMAIL SEND FAILED - CONFIRMATION LINK: {confirmation_link}")
            return False

    def send_otp_email(self, to_email: str, otp_code: str, expires_minutes: int = 10) -> bool:
        """
        Send verification OTP code email
        """
        if not self.smtp_user or not self.smtp_password:
            logger.warning("SMTP credentials not set. Skipping email send.")
            logger.debug("============================================")
            logger.debug(f"VERIFICATION OTP CODE: {otp_code}")
            logger.debug(f"For email: {to_email}")
            logger.debug(f"Expires in: {expires_minutes} minutes")
            logger.debug("============================================")
            return True

        try:
            msg = MIMEMultipart()
            msg["From"] = self.sender_email
            msg["To"] = to_email
            msg["Subject"] = "Your Verification Code - Purrfect Spots"

            # Format OTP with spaces for readability
            formatted_otp = " ".join(otp_code)

            body = f"""
            <html>
              <body style="font-family: Arial, sans-serif; color: #333; margin: 0; padding: 0; background-color: #f5f5f5;">
                <div style="max-width: 600px; margin: 40px auto; padding: 0;">
                    <div style="background: linear-gradient(135deg, #7FB7A4 0%, #6da491 100%); padding: 30px; border-radius: 10px 10px 0 0; text-align: center;">
                        <h1 style="color: white; margin: 0; font-size: 28px;">🐱 Purrfect Spots</h1>
                    </div>
                    <div style="background: white; padding: 40px; border-radius: 0 0 10px 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                        <h2 style="color: #5a4632; text-align: center; margin-top: 0;">Verify Your Email</h2>
                        <p style="text-align: center; color: #666; font-size: 16px;">
                            Enter this code to complete your registration:
                        </p>
                        <div style="background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); border: 2px dashed #7FB7A4; border-radius: 12px; padding: 25px; margin: 30px 0; text-align: center;">
                            <span style="font-family: 'Courier New', monospace; font-size: 36px; font-weight: bold; letter-spacing: 8px; color: #5a4632;">
                                {formatted_otp}
                            </span>
                        </div>
                        <p style="text-align: center; color: #888; font-size: 14px;">
                            ⏱️ This code expires in <strong>{expires_minutes} minutes</strong>
                        </p>
                        <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                        <div style="background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; border-radius: 4px; margin-top: 20px;">
                            <p style="margin: 0; color: #856404; font-size: 13px;">
                                ⚠️ <strong>Security Notice:</strong> Never share this code with anyone. Our team will never ask for your verification code.
                            </p>
                        </div>
                        <p style="text-align: center; color: #999; font-size: 12px; margin-top: 30px;">
                            If you didn't create an account with Purrfect Spots, you can safely ignore this email.
                        </p>
                    </div>
                </div>
              </body>
            </html>
            """

            msg.attach(MIMEText(body, "html"))

            server = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=10)
            server.starttls()
            server.login(self.smtp_user, self.smtp_password)
            server.send_message(msg)
            server.quit()

            logger.info(f"OTP email sent to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send OTP email: {e!s}")
            logger.debug(f"EMAIL SEND FAILED - OTP CODE: {otp_code} for {to_email}")
            return False

    def send_password_changed_email(self, to_email: str) -> bool:
        """
        Send notification that password has been changed
        """
        if not self.smtp_user or not self.smtp_password:
            logger.warning("SMTP credentials not set. Skipping password change notification.")
            return True

        try:
            msg = MIMEMultipart()
            msg["From"] = self.sender_email
            msg["To"] = to_email
            msg["Subject"] = "Your Password Has Been Changed - Purrfect Spots"

            body = """
            <html>
              <body style="font-family: Arial, sans-serif; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #eee; border-radius: 10px;">
                    <h2 style="color: #7FB7A4;">Purrfect Spots</h2>
                    <p>Hello,</p>
                    <p>This is a confirmation that the password for your Purrfect Spots account has been successfully changed.</p>
                    <p><b>If you did not make this change, please contact our support team immediately or reset your password.</b></p>
                    <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                    <p style="font-size: 0.8em; color: #999;">This is an automated security notification.</p>
                </div>
              </body>
            </html>
            """

            msg.attach(MIMEText(body, "html"))

            server = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=10)
            server.starttls()
            server.login(self.smtp_user, self.smtp_password)
            server.send_message(msg)
            server.quit()

            logger.info(f"Password change notification sent to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send password change notification: {e!s}")
            return False


email_service = EmailService()
