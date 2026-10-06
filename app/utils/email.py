import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional, Dict, Any

from flask import current_app


def send_email(to_email: str, subject: str, html_content: str, email_type: str = "NOTIFICATION", async_send: bool = True) -> bool:
    """
    Sends an HTML email to target recipient.
    Uses asynchronous background queue (ThreadPoolExecutor) with full open tracking and bounce handling.
    """
    try:
        from app.backend.admin.email_service import enqueue_email
        res = enqueue_email(
            to_email=to_email,
            subject=subject,
            html_content=html_content,
            email_type=email_type,
            async_send=async_send
        )
        return res.get("success", False)
    except Exception as exc:
        if current_app:
            current_app.logger.warning(f"Error in async email queue, falling back to direct SMTP: {exc}")
        # Direct SMTP fallback
        return _send_direct_smtp(to_email, subject, html_content)


def send_templated_email(to_email: str, template_key: str, context: Dict[str, Any], async_send: bool = True) -> bool:
    """
    Helper function to send email rendered from dynamic HTML EmailTemplate in database.
    """
    try:
        from app.backend.admin.email_service import send_templated_email as _svc_send
        res = _svc_send(
            to_email=to_email,
            template_key=template_key,
            context=context,
            async_send=async_send
        )
        return res.get("success", False)
    except Exception:
        return False


def _send_direct_smtp(to_email: str, subject: str, html_content: str) -> bool:
    """Direct synchronous fallback."""
    if not current_app:
        return False
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

            print(f"📧 [SMTP SUCCESS] Đã gửi email tới {to_email}", flush=True)
            return True
        except Exception as exc:
            print(f"⚠️ [SMTP ERROR] Không thể gửi email qua Gmail: {exc}", flush=True)
            return False
    return True
