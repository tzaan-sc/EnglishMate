import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from flask import current_app


def send_email(to_email, subject, html_content):
    """
    Sends an HTML email to target recipient using Gmail SMTP if credentials exist in .env.
    Always prints formatted Dev logs to terminal output.
    """
    server = current_app.config.get("MAIL_SERVER", "smtp.gmail.com")
    port = current_app.config.get("MAIL_PORT", 587)
    username = current_app.config.get("MAIL_USERNAME", "").strip()
    password = current_app.config.get("MAIL_PASSWORD", "").strip()
    sender = current_app.config.get("MAIL_DEFAULT_SENDER", "").strip() or username or "EnglishMate <noreply@englishmate.com>"

    if username and password:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = sender
            msg["To"] = to_email

            part = MIMEText(html_content, "html", "utf-8")
            msg.attach(part)

            with smtplib.SMTP(server, port, timeout=10) as mail_server:
                mail_server.starttls()
                mail_server.login(username, password)
                mail_server.sendmail(sender, [to_email], msg.as_string())

            print(f"📧 [SMTP SUCCESS] Đã gửi email thật tới {to_email}", flush=True)
            return True
        except Exception as exc:
            print(f"⚠️ [SMTP ERROR] Không thể gửi email qua Gmail: {exc}", flush=True)
            return False
    return False
