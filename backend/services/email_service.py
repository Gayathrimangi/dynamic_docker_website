import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from flask import current_app

logger = logging.getLogger(__name__)

class EmailDeliveryError(Exception):
    """Raised when an email cannot be dispatched via SMTP."""
    pass

class EmailService:
    @staticmethod
    def _render_email_html(name: str, otp: str, expiry_minutes: int = 5) -> str:
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Your Verification Code</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      background-color: #0f172a;
      color: #e2e8f0;
      margin: 0;
      padding: 24px;
    }}
    .container {{
      max-width: 540px;
      margin: 0 auto;
      background-color: #1e293b;
      border-radius: 12px;
      padding: 36px 32px;
      border: 1px solid #334155;
      box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.4);
    }}
    .header {{
      text-align: center;
      padding-bottom: 24px;
      border-bottom: 1px solid #334155;
    }}
    .header h1 {{
      font-size: 24px;
      color: #38bdf8;
      margin: 0;
      font-weight: 700;
    }}
    .content {{
      padding: 28px 0;
    }}
    .greeting {{
      font-size: 16px;
      color: #cbd5e1;
      margin-bottom: 16px;
    }}
    .otp-box {{
      text-align: center;
      margin: 28px 0;
      padding: 20px;
      background: linear-gradient(135deg, #1e1b4b 0%, #0f172a 100%);
      border: 1px solid #6366f1;
      border-radius: 10px;
    }}
    .otp-code {{
      font-size: 38px;
      letter-spacing: 10px;
      font-weight: 800;
      color: #818cf8;
      font-family: 'Courier New', monospace;
      display: inline-block;
    }}
    .expiry {{
      font-size: 13px;
      color: #94a3b8;
      margin-top: 10px;
    }}
    .warning {{
      font-size: 13px;
      color: #f59e0b;
      background-color: rgba(245, 158, 11, 0.1);
      border-left: 3px solid #f59e0b;
      padding: 10px 14px;
      border-radius: 4px;
      margin: 20px 0;
    }}
    .footer {{
      border-top: 1px solid #334155;
      padding-top: 20px;
      text-align: center;
      font-size: 12px;
      color: #64748b;
    }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>Secure Auth Service</h1>
    </div>
    <div class="content">
      <p class="greeting">Hello {name},</p>
      <p>Thank you for registering. Please use the following One-Time Password (OTP) to complete your verification:</p>
      <div class="otp-box">
        <div class="otp-code">{otp}</div>
        <div class="expiry">Valid for {expiry_minutes} minutes only.</div>
      </div>
      <div class="warning">
        Security notice: Never share this OTP with anyone. Our team will never ask for your verification code.
      </div>
      <p style="font-size: 14px; color: #94a3b8;">If you did not initiate this registration, please disregard this email.</p>
    </div>
    <div class="footer">
      &copy; Secure Auth System. All rights reserved.
    </div>
  </div>
</body>
</html>"""

    @classmethod
    def send_otp_email(cls, to_email: str, name: str, otp: str, expiry_minutes: int = 5) -> bool:
        """
        Sends OTP verification email via SMTP.
        Raises EmailDeliveryError if sending fails.
        """
        config = current_app.config

        smtp_host = config.get("SMTP_HOST", "smtp.gmail.com")
        smtp_port = int(config.get("SMTP_PORT", 587))
        smtp_user = config.get("SMTP_USER", "")
        smtp_password = config.get("SMTP_PASSWORD", "")
        smtp_from = config.get("SMTP_FROM_EMAIL") or smtp_user
        use_tls = config.get("SMTP_USE_TLS", True)
        use_ssl = config.get("SMTP_USE_SSL", False)
        dev_mode = config.get("SMTP_DEV_MODE", False)

        # In dev mode, if SMTP is not configured, simulate successful email delivery
        if dev_mode or not smtp_user or not smtp_password:
            logger.info("SMTP_DEV_MODE enabled or credentials missing. Simulated OTP dispatch for %s", to_email)
            return True

        message = MIMEMultipart("alternative")
        message["Subject"] = f"{otp} is your verification code"
        message["From"] = smtp_from
        message["To"] = to_email

        plain_text = (
            f"Hello {name},\n\n"
            f"Your one-time verification code is: {otp}\n\n"
            f"This code will expire in {expiry_minutes} minutes.\n"
            f"If you did not request this, please ignore this email.\n"
        )
        html_text = cls._render_email_html(name, otp, expiry_minutes)

        message.attach(MIMEText(plain_text, "plain"))
        message.attach(MIMEText(html_text, "html"))

        try:
            if use_ssl:
                with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=15) as server:
                    server.login(smtp_user, smtp_password)
                    server.send_message(message)
            else:
                with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
                    if use_tls:
                        server.starttls()
                    server.login(smtp_user, smtp_password)
                    server.send_message(message)

            logger.info("Verification OTP email successfully dispatched to %s", to_email)
            return True

        except smtplib.SMTPAuthenticationError as e:
            logger.error("SMTP Authentication failed for %s", smtp_user)
            raise EmailDeliveryError("SMTP authentication failed. Verify SMTP username and App Password.") from e
        except smtplib.SMTPException as e:
            logger.error("SMTP delivery failure: %s", type(e).__name__)
            raise EmailDeliveryError(f"Email service error: {type(e).__name__}") from e
        except Exception as e:
            logger.error("Unexpected error connecting to SMTP host: %s", type(e).__name__)
            raise EmailDeliveryError("Failed to reach email server. Please try again later.") from e
