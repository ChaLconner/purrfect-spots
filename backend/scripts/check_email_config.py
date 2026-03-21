"""
Quick diagnostic script to verify Resend SMTP configuration.

Usage:
    cd backend
    python scripts/check_email_config.py
"""

import os
import smtplib
import sys
from email.mime.text import MIMEText
from pathlib import Path

# Add backend root to path and load env
sys.path.insert(0, str(Path(__file__).parent.parent))
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")


def check_smtp() -> None:
    host = os.getenv("SMTP_SERVER", "smtp.resend.com")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER", "resend")
    password = os.getenv("SMTP_PASSWORD", "")
    sender = os.getenv("SMTP_SENDER", "")

    print("=" * 50)
    print("Resend SMTP Configuration Check")
    print("=" * 50)
    print(f"Host     : {host}:{port}")
    print(f"User     : {user}")
    print(f"Key set  : {'YES' if password else 'NO'}")
    print(f"Key valid: {'YES (starts with re_)' if password.startswith('re_') else 'NO (invalid format)'}")
    print(f"Key len  : {len(password)} chars")
    print(f"Sender   : {sender}")
    print()

    try:
        print("[1/3] Connecting to SMTP server...")
        smtp = smtplib.SMTP(host, port, timeout=10)
        smtp.ehlo()
        print("      OK")

        print("[2/3] Starting TLS...")
        smtp.starttls()
        smtp.ehlo()
        print("      OK")

        print(f"[3/3] Authenticating as '{user}'...")
        smtp.login(user, password)
        print("      OK — Authentication successful!\n")

        # Test send (optional, only if a recipient is passed)
        if len(sys.argv) > 1:
            recipient = sys.argv[1]
            print(f"[4/4] Sending test email to {recipient}...")
            msg = MIMEText("This is a test email from Purrfect Spots backend.")
            msg["Subject"] = "Test Email - Purrfect Spots"
            msg["From"] = sender or f"test@{host}"
            msg["To"] = recipient
            smtp.sendmail(msg["From"], [recipient], msg.as_string())
            print(f"      OK — Email sent to {recipient}")

        smtp.quit()
        print("\n[SUCCESS] SMTP configuration is WORKING correctly.")

    except smtplib.SMTPAuthenticationError as e:
        print(f"\n[FAIL] Authentication FAILED: {e}")
        print("\nFix: Regenerate your Resend API key at https://resend.com/api-keys")
        print("     Then update SMTP_PASSWORD in backend/.env")
    except smtplib.SMTPConnectError as e:
        print(f"\n[FAIL] Connection FAILED: {e}")
    except TimeoutError:
        print("\n[FAIL] Connection timed out -- check firewall or network")
    except Exception as e:
        print(f"\n[ERROR] {type(e).__name__}: {e}")

    print("\nNext steps:")
    print("  1. Go to https://resend.com/domains")
    print("  2. Add and verify: mail.purrfectspots.xyz")
    print("  3. Go to https://resend.com/api-keys")
    print("  4. Create a new API key with 'Sending access'")
    print("  5. Update SMTP_PASSWORD in backend/.env with the new key")


if __name__ == "__main__":
    check_smtp()
