import os
import smtplib
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.logger import logger, sanitize_log_value

WARN_SMTP_NOT_SET = "SMTP credentials not set. Skipping email send."
DEBUG_SEPARATOR = "============================================"
_email_executor = ThreadPoolExecutor(max_workers=5)


class EmailService:
    def __init__(self) -> None:
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.sender_email = os.getenv("SMTP_SENDER") or self.smtp_user or "noreply@purrfectspots.com"
        self.frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")

    def _build_html_email(
        self,
        title: str,
        content_html: str,
        title_color: str = "#7FB7A4",
        border_color: str = "#eee",
        footer_note: str = "This is an automated notification.",
    ) -> str:
        """Construct a standardized HTML email template body."""
        return f"""
        <html>
          <body style="font-family: Arial, sans-serif; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid {border_color}; border-radius: 10px;">
                <h2 style="color: {title_color};">{title}</h2>
                <p>Hello,</p>
                {content_html}
                <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                <p style="font-size: 0.8em; color: #999;">{footer_note}</p>
            </div>
          </body>
        </html>
        """

    def send_reset_email(self, to_email: str, token: str) -> bool:
        """Send password reset email"""
        if not self.smtp_user or not self.smtp_password:
            logger.warning(WARN_SMTP_NOT_SET)
            logger.debug(DEBUG_SEPARATOR)
            logger.debug(f"PASSWORD RESET LINK: {token}")
            logger.debug(DEBUG_SEPARATOR)
            return True

        reset_link = token
        body = self._build_html_email(
            "Purrfect Spots",
            f"""
                <p>We received a request to reset your password. Click the button below to choose a new one:</p>
                <a href="{reset_link}" style="display: inline-block; background-color: #7FB7A4; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin: 20px 0;">Reset Password</a>
                <p style="font-size: 0.9em; color: #777;">If you didn't ask to reset your password, you can ignore this email.</p>
            """,
            footer_note=f"Or copy this link: {reset_link}",
        )
        return self._send_html_email(to_email, "Reset Your Password - Purrfect Spots", body, "reset email")

    def send_confirmation_email(self, to_email: str, confirmation_link: str) -> bool:
        """Send confirmation email for new signup"""
        if not self.smtp_user or not self.smtp_password:
            logger.warning(WARN_SMTP_NOT_SET)
            logger.debug(DEBUG_SEPARATOR)
            logger.debug(f"CONFIRMATION LINK: {confirmation_link}")
            logger.debug(DEBUG_SEPARATOR)
            return True

        body = self._build_html_email(
            "Welcome to Purrfect Spots!",
            f"""
                <p>Thank you for joining Purrfect Spots. We're excited to have you!</p>
                <p>Please confirm your email address by clicking the button below:</p>
                <a href="{confirmation_link}" style="display: inline-block; background-color: #7FB7A4; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin: 20px 0;">Confirm Email</a>
                <p style="font-size: 0.9em; color: #777;">If you did not sign up for this account, please ignore this email.</p>
            """,
            footer_note=f"Or copy this link: {confirmation_link}",
        )
        return self._send_html_email(
            to_email, "Welcome to Purrfect Spots! Please Confirm Your Email", body, "confirmation email"
        )

    def send_otp_email(self, to_email: str, otp_code: str, expires_minutes: int = 10) -> bool:
        """Send verification OTP code email"""
        if not self.smtp_user or not self.smtp_password:
            logger.warning(WARN_SMTP_NOT_SET)
            logger.debug(DEBUG_SEPARATOR)
            logger.debug(f"VERIFICATION OTP CODE: {otp_code}")
            logger.debug("For email: %s", sanitize_log_value(to_email))
            logger.debug(f"Expires in: {expires_minutes} minutes")
            logger.debug(DEBUG_SEPARATOR)
            return True

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
        return self._send_html_email(to_email, "Your Verification Code - Purrfect Spots", body, "OTP email")

    def _send_html_email(self, to_email: str, subject: str, body_html: str, action_label: str) -> bool:
        """Helper to construct and dispatch HTML email messages using thread pool."""
        if not self.smtp_user or not self.smtp_password:
            safe_action_label = sanitize_log_value(action_label)
            logger.warning("SMTP credentials not set. Skipping %s.", safe_action_label)
            logger.debug("%s to %s", safe_action_label.upper(), sanitize_log_value(to_email))
            return True

        try:
            msg = MIMEMultipart()
            msg["From"] = self.sender_email
            msg["To"] = to_email
            msg["Subject"] = subject
            msg.attach(MIMEText(body_html, "html"))
            future = _email_executor.submit(self._send, msg)
            return future.result(timeout=15)
        except Exception as e:
            logger.error("Failed to send %s: %s", sanitize_log_value(action_label), sanitize_log_value(str(e)))
            return False

    def send_ban_notification(self, to_email: str, reason: str) -> bool:
        """Send notification that user has been banned"""
        body = self._build_html_email(
            "Account Status Update",
            f"""
                <p>We are writing to inform you that your Purrfect Spots account has been suspended due to a violation of our Terms of Service.</p>
                <div style="background-color: #f2dede; padding: 15px; border-radius: 5px; margin: 20px 0; color: #a94442;">
                    <strong>Reason:</strong> {reason}
                </div>
                <p>As a result, you will no longer be able to log in or access your data. If you believe this was a mistake, please contact our support team.</p>
            """,
            title_color="#d9534f",
            footer_note="This is an automated security notification.",
        )
        return self._send_html_email(to_email, "Account Suspended - Purrfect Spots", body, "ban notification")

    def send_content_removal_notification(self, to_email: str, content_type: str, reason: str) -> bool:
        """Send notification that content has been removed"""
        body = self._build_html_email(
            "Moderation Notice",
            f"""
                <p>One of your {content_type} items has been removed by our moderation team for violating our community guidelines.</p>
                <div style="background-color: #fcf8e3; padding: 15px; border-radius: 5px; margin: 20px 0; color: #8a6d3b;">
                    <strong>Action taken:</strong> Content Removal<br>
                    <strong>Reason:</strong> {reason}
                </div>
                <p>Please review our guidelines to ensure future posts comply with our community standards.</p>
            """,
            title_color="#f0ad4e",
            footer_note="This is an automated notification.",
        )
        return self._send_html_email(
            to_email, "Content Removal Notice - Purrfect Spots", body, "content removal notification"
        )

    def send_account_deletion_notification(self, to_email: str, reason: str) -> bool:
        """Send notification that account has been permanently deleted"""
        body = self._build_html_email(
            "Account Deleted",
            f"""
                <p>We are writing to confirm that your Purrfect Spots account has been permanently deleted.</p>
                <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0; color: #666;">
                    <strong>Reason:</strong> {reason}
                </div>
                <p>All your data has been removed from our systems in accordance with our retention policy.</p>
            """,
            title_color="#666",
            footer_note="This is an automated notification.",
        )
        return self._send_html_email(
            to_email, "Account Deleted - Purrfect Spots", body, "account deletion notification"
        )

    def send_password_changed_email(self, to_email: str) -> bool:
        """Send notification that password has been changed"""
        body = self._build_html_email(
            "Security Update",
            """
                <p>This is a confirmation that the password for your Purrfect Spots account was recently changed.</p>
                <p>If you did this, you can safely ignore this email.</p>
                <div style="background-color: #d9edf7; padding: 15px; border-radius: 5px; margin: 20px 0; color: #31708f;">
                    <strong>Security Notice:</strong> If you did NOT change your password, please contact our support team immediately or use the password reset feature to secure your account.
                </div>
            """,
            title_color="#5bc0de",
            footer_note="This is an automated security notification.",
        )
        return self._send_html_email(
            to_email, "Your Password Has Been Changed - Purrfect Spots", body, "password change notification"
        )

    def send_admin_config_request(self, admin_email: str, requester_name: str, config_key: str) -> bool:
        """Send notification to admins when a config change requires approval."""
        formatted_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        subject = f"Approval Required: {config_key} - Purrfect Spots Admin"
        body = f"""
        <html>
          <body style="font-family: Arial, sans-serif; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #7FB7A4; border-radius: 10px;">
                <h2 style="color: #7FB7A4;">Configuration Approval Required</h2>
                <p>Hello Admin,</p>
                <p>An administrator has proposed a change to a protected system setting that requires your review.</p>
                <div style="background-color: #f7fcfb; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #7FB7A4;">
                    <strong>Setting:</strong> {config_key}<br>
                    <strong>Requested by:</strong> {requester_name}<br>
                    <strong>Time:</strong> {formatted_time}
                </div>
                <p>Please log in to the Admin Dashboard to review the proposed value and decide whether to approve or reject the change.</p>
                <a href="{self.frontend_url}/admin/settings" style="display: inline-block; background-color: #7FB7A4; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin: 20px 0;">Go to Settings</a>
            </div>
          </body>
        </html>
        """
        return self._send_html_email(admin_email, subject, body, "admin config request")

    def send_admin_config_result(
        self, requester_email: str, config_key: str, status: str, checker_name: str, reason: str = ""
    ) -> bool:
        """Notify the requester about the approval/rejection result."""
        color = "#5cb85c" if status == "approved" else "#d9534f"
        subject = f"Update: Your configuration request for {config_key} was {status}"
        reason_html = f"<p><strong>Reason:</strong> {reason}</p>" if reason else ""

        body = f"""
        <html>
          <body style="font-family: Arial, sans-serif; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid {color}; border-radius: 10px;">
                <h2 style="color: {color};">Config Request {status.capitalize()}</h2>
                <p>Your request to update <strong>{config_key}</strong> has been processed.</p>
                <div style="background-color: #f9f9f9; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <strong>Status:</strong> <span style="color: {color};">{status.upper()}</span><br>
                    <strong>Processed by:</strong> {checker_name}
                    {reason_html}
                </div>
                <p>If you have any questions, please coordinate with the authorizing administrator.</p>
            </div>
          </body>
        </html>
        """
        return self._send_html_email(requester_email, subject, body, "config result notification")

    def send_security_alert(self, to_email: str, alert_type: str, severity: str, details: str) -> bool:
        """Send a security alert email to administrators"""
        color = "#d9534f" if severity in ("high", "critical") else "#f0ad4e"
        formatted_title = alert_type.replace("_", " ").capitalize()
        formatted_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        subject = f"SECURITY ALERT [{severity.upper()}]: {formatted_title} - Purrfect Spots"
        body = f"""
        <html>
          <body style="font-family: Arial, sans-serif; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 2px solid {color}; border-radius: 10px;">
                <h2 style="color: {color};">Security Alert: {formatted_title}</h2>
                <p>Hello Admin,</p>
                <p>A security event has been detected that requires your attention.</p>
                <div style="background-color: #f9f9f9; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid {color};">
                    <strong>Severity:</strong> <span style="color: {color}; font-weight: bold;">{severity.upper()}</span><br>
                    <strong>Type:</strong> {alert_type}<br>
                    <strong>Time:</strong> {formatted_time}<br>
                    <strong>Details:</strong><br>
                    <pre style="white-space: pre-wrap; font-family: monospace; background: #eee; padding: 10px; margin-top: 10px;">{details}</pre>
                </div>
                <p>Please log in to the Security Dashboard to investigate this incident immediately.</p>
                <a href="{self.frontend_url}/admin/breach-summary" style="display: inline-block; background-color: {color}; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin: 20px 0;">Investigate Incident</a>
            </div>
          </body>
        </html>
        """
        return self._send_html_email(to_email, subject, body, "security alert")

    def _send(self, msg: MIMEMultipart) -> bool:
        """Helper to send SMTP message with proper resource management."""
        if not self.smtp_user or not self.smtp_password:
            raise ValueError("SMTP credentials not set")

        with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=10) as server:
            server.starttls()
            server.login(self.smtp_user, self.smtp_password)
            server.send_message(msg)
            # quit() is called automatically via __exit__ in smtplib.SMTP context manager
            return True


email_service = EmailService()
