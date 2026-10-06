import json
import re
import smtplib
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional, Tuple, Union

from flask import current_app
from sqlalchemy import func, text

from ...extensions import db
from .models import EmailLog, EmailTemplate, EmailBounce, SystemConfig
from .utils import log_audit_action

# Background worker thread pool for non-blocking asynchronous email delivery
_email_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="email_worker")

now_utc = lambda: datetime.now(timezone.utc)

# ---------------------------------------------------------------------------
# DEFAULT EMAIL TEMPLATES
# ---------------------------------------------------------------------------
DEFAULT_TEMPLATES = [
    {
        "key": "VERIFICATION_EMAIL",
        "name": "Mã xác thực tài khoản (OTP Verification)",
        "subject": "[EnglishMate] Mã xác thực tài khoản: {{ otp_code }}",
        "description": "Gửi mã OTP 6 số để xác thực địa chỉ email người dùng khi đăng ký hoặc đổi email.",
        "variables_json": json.dumps(["username", "otp_code", "expire_minutes"]),
        "html_content": """<div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 600px; margin: 0 auto; padding: 24px; background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px;">
  <div style="text-align: center; margin-bottom: 24px;">
    <h2 style="color: #4f46e5; margin: 0; font-size: 24px;">EnglishMate</h2>
    <p style="color: #64748b; font-size: 14px; margin: 4px 0 0;">Xác thực tài khoản người dùng</p>
  </div>
  <p style="font-size: 16px; color: #1e293b; line-height: 1.6;">Xin chào <strong>{{ username }}</strong>,</p>
  <p style="font-size: 15px; color: #475569; line-height: 1.6;">Bạn vừa thực hiện yêu cầu xác thực email trên EnglishMate. Vui lòng sử dụng mã xác thực bảo mật sau đây:</p>
  <div style="text-align: center; margin: 28px 0;">
    <div style="display: inline-block; background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%); color: #ffffff; padding: 14px 32px; font-size: 28px; font-weight: 700; letter-spacing: 6px; border-radius: 8px; box-shadow: 0 4px 6px -1px rgba(79, 70, 229, 0.2);">{{ otp_code }}</div>
    <p style="color: #94a3b8; font-size: 13px; margin-top: 10px;">Mã này có hiệu lực trong vòng {{ expire_minutes }} phút.</p>
  </div>
  <p style="font-size: 14px; color: #64748b; line-height: 1.5;">Nếu bạn không thực hiện yêu cầu này, vui lòng bỏ qua email này hoặc liên hệ bộ phận hỗ trợ.</p>
  <hr style="border: none; border-top: 1px solid #f1f5f9; margin: 24px 0;">
  <p style="text-align: center; color: #94a3b8; font-size: 12px; margin: 0;">© EnglishMate - Học tiếng Anh mỗi ngày.</p>
</div>"""
    },
    {
        "key": "RESET_PASSWORD_EMAIL",
        "name": "Khôi phục mật khẩu (Reset Password)",
        "subject": "[EnglishMate] Yêu cầu khôi phục mật khẩu tài khoản",
        "description": "Gửi link và mã OTP đặt lại mật khẩu cho tài khoản người dùng.",
        "variables_json": json.dumps(["username", "reset_url", "otp_code", "expire_minutes"]),
        "html_content": """<div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 600px; margin: 0 auto; padding: 24px; background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px;">
  <div style="text-align: center; margin-bottom: 24px;">
    <h2 style="color: #4f46e5; margin: 0; font-size: 24px;">EnglishMate</h2>
    <p style="color: #64748b; font-size: 14px; margin: 4px 0 0;">Yêu cầu đặt lại mật khẩu</p>
  </div>
  <p style="font-size: 16px; color: #1e293b; line-height: 1.6;">Xin chào <strong>{{ username }}</strong>,</p>
  <p style="font-size: 15px; color: #475569; line-height: 1.6;">Chúng tôi nhận được yêu cầu đặt lại mật khẩu cho tài khoản của bạn. Nhấn vào nút bên dưới để tiến hành tạo mật khẩu mới:</p>
  <div style="text-align: center; margin: 28px 0;">
    <a href="{{ reset_url }}" style="display: inline-block; background-color: #4f46e5; color: #ffffff; text-decoration: none; padding: 12px 28px; font-size: 16px; font-weight: 600; border-radius: 8px;">Đặt lại mật khẩu ngay</a>
    <p style="color: #64748b; font-size: 14px; margin-top: 14px;">Hoặc sử dụng mã xác nhận: <strong style="color: #4f46e5; font-size: 18px;">{{ otp_code }}</strong></p>
    <p style="color: #94a3b8; font-size: 13px; margin-top: 4px;">Liên kết có hiệu lực trong vòng {{ expire_minutes }} phút.</p>
  </div>
  <p style="font-size: 14px; color: #64748b; line-height: 1.5;">Nếu bạn không yêu cầu đặt lại mật khẩu, tài khoản của bạn vẫn được an toàn và bạn có thể yên tâm bỏ qua email này.</p>
  <hr style="border: none; border-top: 1px solid #f1f5f9; margin: 24px 0;">
  <p style="text-align: center; color: #94a3b8; font-size: 12px; margin: 0;">© EnglishMate - Nền tảng học tiếng Anh trực tuyến.</p>
</div>"""
    },
    {
        "key": "DAILY_GOAL_REMINDER",
        "name": "Nhắc nhở mục tiêu học tập (Daily Goal Reminder)",
        "subject": "🎯 {{ username }} ơi, đừng quên mục tiêu học tiếng Anh hôm nay nhé!",
        "description": "Nhắc nhở học viên hoàn thành mục tiêu học từ vựng và bài học trong ngày.",
        "variables_json": json.dumps(["username", "current_xp", "target_goal", "study_url"]),
        "html_content": """<div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 600px; margin: 0 auto; padding: 24px; background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px;">
  <div style="text-align: center; margin-bottom: 24px;">
    <h2 style="color: #f59e0b; margin: 0; font-size: 24px;">🔥 Giữ vững chuỗi Streak của bạn!</h2>
  </div>
  <p style="font-size: 16px; color: #1e293b; line-height: 1.6;">Chào <strong>{{ username }}</strong>,</p>
  <p style="font-size: 15px; color: #475569; line-height: 1.6;">Chỉ còn một chút nữa là bạn sẽ hoàn thành mục tiêu <strong>{{ target_goal }}</strong> của ngày hôm nay. Dành ra 5 phút để ôn tập từ vựng và tích lũy thêm XP nhé!</p>
  <div style="text-align: center; margin: 28px 0;">
    <a href="{{ study_url }}" style="display: inline-block; background-color: #f59e0b; color: #ffffff; text-decoration: none; padding: 12px 32px; font-size: 16px; font-weight: 700; border-radius: 8px;">Vào học ngay</a>
  </div>
  <p style="font-size: 14px; color: #64748b; line-height: 1.5;">Học đều đặn mỗi ngày là bí quyết nhanh nhất để làm chủ tiếng Anh.</p>
</div>"""
    },
    {
        "key": "WELCOME_EMAIL",
        "name": "Chào mừng thành viên mới (Welcome Email)",
        "subject": "🎉 Chào mừng {{ username }} gia nhập cộng đồng EnglishMate!",
        "description": "Email gửi tự động khi người dùng đăng ký tài khoản thành công.",
        "variables_json": json.dumps(["username", "dashboard_url"]),
        "html_content": """<div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 600px; margin: 0 auto; padding: 24px; background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px;">
  <div style="text-align: center; margin-bottom: 24px;">
    <h2 style="color: #4f46e5; margin: 0; font-size: 26px;">Chào mừng bạn đến với EnglishMate!</h2>
  </div>
  <p style="font-size: 16px; color: #1e293b; line-height: 1.6;">Xin chào <strong>{{ username }}</strong>,</p>
  <p style="font-size: 15px; color: #475569; line-height: 1.6;">Cảm ơn bạn đã lựa chọn EnglishMate đồng hành trên con đường chinh phục tiếng Anh. Bắt đầu ngay với bài thi đánh giá trình độ và lộ trình học cá nhân hóa!</p>
  <div style="text-align: center; margin: 28px 0;">
    <a href="{{ dashboard_url }}" style="display: inline-block; background-color: #4f46e5; color: #ffffff; text-decoration: none; padding: 12px 32px; font-size: 16px; font-weight: 700; border-radius: 8px;">Khám phá lộ trình học</a>
  </div>
</div>"""
    },
    {
        "key": "CUSTOM_NOTIFICATION",
        "name": "Thông báo chung từ Ban Quản trị",
        "subject": "[EnglishMate] {{ title }}",
        "description": "Gửi thông báo cập nhật tính năng, bảo trì hoặc sự kiện cho học viên.",
        "variables_json": json.dumps(["title", "message_content", "cta_text", "cta_url"]),
        "html_content": """<div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 600px; margin: 0 auto; padding: 24px; background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px;">
  <h3 style="color: #1e293b; margin-top: 0;">{{ title }}</h3>
  <div style="font-size: 15px; color: #475569; line-height: 1.6; margin: 16px 0;">
    {{ message_content }}
  </div>
  <div style="text-align: center; margin: 24px 0;">
    <a href="{{ cta_url }}" style="display: inline-block; background-color: #4f46e5; color: #ffffff; text-decoration: none; padding: 10px 24px; font-size: 15px; font-weight: 600; border-radius: 6px;">{{ cta_text }}</a>
  </div>
</div>"""
    }
]


def init_default_email_templates():
    """Khởi tạo các mẫu HTML email mặc định nếu chưa tồn tại trong cơ sở dữ liệu."""
    for tpl_data in DEFAULT_TEMPLATES:
        existing = EmailTemplate.query.filter_by(key=tpl_data["key"]).first()
        if not existing:
            new_tpl = EmailTemplate(
                key=tpl_data["key"],
                name=tpl_data["name"],
                subject=tpl_data["subject"],
                html_content=tpl_data["html_content"],
                variables_json=tpl_data["variables_json"],
                description=tpl_data["description"],
                is_active=True
            )
            db.session.add(new_tpl)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()


# ---------------------------------------------------------------------------
# EMAIL BOUNCE & VALIDATION
# ---------------------------------------------------------------------------

EMAIL_REGEX = re.compile(r"^[\w\.-]+@([\w\.-]+\.\w+)$")


def is_email_bounced(email: str) -> bool:
    """Kiểm tra xem địa chỉ email có nằm trong danh sách Bounce bị khóa hay không."""
    if not email:
        return True
    bounce = EmailBounce.query.filter_by(email=email.strip().lower(), is_blocked=True).first()
    return bounce is not None


def record_email_bounce(email: str, reason: str, bounce_type: str = "HARD_BOUNCE") -> EmailBounce:
    """Ghi nhận email bị lỗi bounce vào bảng EmailBounce và khóa gửi lại."""
    clean_email = email.strip().lower()
    bounce = EmailBounce.query.filter_by(email=clean_email).first()
    if not bounce:
        bounce = EmailBounce(
            email=clean_email,
            bounce_type=bounce_type,
            reason=reason,
            is_blocked=True,
            created_at=now_utc()
        )
        db.session.add(bounce)
    else:
        bounce.reason = reason
        bounce.bounce_type = bounce_type
        bounce.is_blocked = True
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
    return bounce


# ---------------------------------------------------------------------------
# EMAIL TRACKING INJECTION
# ---------------------------------------------------------------------------

def inject_tracking_pixel_and_links(html_content: str, tracking_id: str, base_url: str = "") -> str:
    """
    Chèn 1x1 Transparent Tracking Pixel và bọc các liên kết href để theo dõi Open Rate và Click Rate.
    """
    pixel_tag = f'<img src="{base_url}/email/track/open/{tracking_id}.png" width="1" height="1" style="display:none !important; width:1px !important; height:1px !important;" alt="" border="0" />'
    
    # Chèn pixel trước </body> hoặc cuối nội dung
    if "</body>" in html_content:
        modified_html = html_content.replace("</body>", f"{pixel_tag}</body>")
    else:
        modified_html = html_content + pixel_tag

    return modified_html


# ---------------------------------------------------------------------------
# CORE SENDING & WORKER
# ---------------------------------------------------------------------------

def _send_smtp_direct(
    to_email: str,
    subject: str,
    html_content: str,
    app_config: dict
) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Gửi email trực tiếp qua SMTP. Trả về (success, error_message, bounce_type).
    """
    server = app_config.get("MAIL_SERVER") or "smtp.gmail.com"
    port = int(app_config.get("MAIL_PORT") or 587)
    username = str(app_config.get("MAIL_USERNAME") or "").strip()
    password = str(app_config.get("MAIL_PASSWORD") or "").strip()
    sender = str(app_config.get("MAIL_DEFAULT_SENDER") or "").strip() or username or "EnglishMate <noreply@englishmate.com>"

    # Kiểm tra cú pháp email cơ bản
    if not EMAIL_REGEX.match(to_email):
        return False, "Địa chỉ email không đúng định dạng cú pháp RFC.", "SYNTAX_ERROR"

    if not (username and password):
        # Môi trường Dev/Test không cấu hình SMTP: Ghi log thành công mô phỏng
        return True, None, None

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

        return True, None, None

    except smtplib.SMTPRecipientsRefused as exc:
        return False, f"Hòm thư người nhận từ chối nhận (550 Recipient rejected): {exc}", "HARD_BOUNCE"
    except smtplib.SMTPSenderRefused as exc:
        return False, f"Lỗi người gửi SMTP: {exc}", "SENDER_ERROR"
    except smtplib.SMTPAuthenticationError as exc:
        return False, f"Lỗi xác thực tài khoản SMTP: {exc}", "AUTH_ERROR"
    except Exception as exc:
        return False, str(exc), "CONNECTION_ERROR"


def _worker_deliver_email(
    app_ctx_builder,
    email_log_id: int,
    app_config: dict
):
    """Worker chạy trong Background Thread để gửi email bất đồng bộ."""
    app = app_ctx_builder()
    with app.app_context():
        email_log = db.session.get(EmailLog, email_log_id)
        if not email_log:
            return

        email_log.status = "SENDING"
        db.session.commit()

        # Kiểm tra bounce blocklist
        if is_email_bounced(email_log.recipient):
            email_log.status = "BOUNCED"
            email_log.bounce_reason = "Email nằm trong danh sách chặn Bounce trước đó."
            db.session.commit()
            return

        success, err_msg, bounce_type = _send_smtp_direct(
            to_email=email_log.recipient,
            subject=email_log.subject,
            html_content=inject_tracking_pixel_and_links(email_log.error_message or "", email_log.tracking_id),
            app_config=app_config
        )

        now_d = now_utc()
        if success:
            email_log.status = "SENT"
            email_log.sent_at = now_d
            email_log.error_message = None
        else:
            if bounce_type in ("HARD_BOUNCE", "SYNTAX_ERROR"):
                email_log.status = "BOUNCED"
                email_log.bounce_reason = err_msg
                record_email_bounce(email_log.recipient, err_msg or "Recipient refused", bounce_type)
            else:
                email_log.status = "FAILED"
                email_log.error_message = err_msg

        db.session.commit()


# ---------------------------------------------------------------------------
# PUBLIC SERVICE API
# ---------------------------------------------------------------------------

def enqueue_email(
    to_email: str,
    subject: str,
    html_content: str,
    email_type: str = "NOTIFICATION",
    scheduled_at: Optional[datetime] = None,
    admin_id: Optional[int] = None,
    async_send: bool = True
) -> Dict[str, Any]:
    """
    Đưa email vào hàng đợi gửi (Email Queue) và lập tức trả về kết quả không gây đơ trang web.
    - Tạo bản ghi EmailLog với tracking_id riêng biệt.
    - Nếu có scheduled_at trong tương lai -> Lưu vào hàng đợi chờ scheduler.
    - Nếu gửi ngay -> Đẩy vào Background ThreadPoolExecutor.
    """
    clean_email = to_email.strip().lower()
    tracking_id = uuid.uuid4().hex

    # Kiểm tra bounce blocklist
    if is_email_bounced(clean_email):
        log_rec = EmailLog(
            tracking_id=tracking_id,
            recipient=clean_email,
            subject=subject,
            email_type=email_type,
            status="BOUNCED",
            bounce_reason="Email nằm trong danh sách chặn Bounce.",
            created_by_id=admin_id,
            created_at=now_utc()
        )
        db.session.add(log_rec)
        db.session.commit()
        return {
            "success": False,
            "error": "Email bị chặn do nằm trong danh sách Bounce.",
            "tracking_id": tracking_id,
            "status": "BOUNCED"
        }

    now_d = now_utc()
    is_scheduled = scheduled_at and scheduled_at > now_d

    log_rec = EmailLog(
        tracking_id=tracking_id,
        recipient=clean_email,
        subject=subject,
        email_type=email_type,
        status="QUEUED" if is_scheduled else "SENDING",
        error_message=html_content,  # Temporary store HTML body until sent
        scheduled_at=scheduled_at,
        created_by_id=admin_id,
        created_at=now_d
    )
    db.session.add(log_rec)
    db.session.commit()

    if not is_scheduled:
        app_obj = current_app._get_current_object()
        app_config = {
            "MAIL_SERVER": current_app.config.get("MAIL_SERVER"),
            "MAIL_PORT": current_app.config.get("MAIL_PORT"),
            "MAIL_USERNAME": current_app.config.get("MAIL_USERNAME"),
            "MAIL_PASSWORD": current_app.config.get("MAIL_PASSWORD"),
            "MAIL_DEFAULT_SENDER": current_app.config.get("MAIL_DEFAULT_SENDER"),
        }

        if async_send:
            _email_executor.submit(
                _worker_deliver_email,
                lambda: app_obj,
                log_rec.id,
                app_config
            )
        else:
            _worker_deliver_email(
                lambda: app_obj,
                log_rec.id,
                app_config
            )

    return {
        "success": True,
        "tracking_id": tracking_id,
        "email_log_id": log_rec.id,
        "status": "QUEUED" if is_scheduled else "SENT",
        "recipient": clean_email,
        "scheduled_at": scheduled_at.isoformat() if scheduled_at else None
    }


def send_templated_email(
    to_email: str,
    template_key: str,
    context: Dict[str, Any],
    scheduled_at: Optional[datetime] = None,
    admin_id: Optional[int] = None,
    async_send: bool = True
) -> Dict[str, Any]:
    """
    Gửi email sử dụng mẫu HTML EmailTemplate được lưu trong CSDL.
    """
    tpl = EmailTemplate.query.filter_by(key=template_key, is_active=True).first()
    if not tpl:
        # Fallback to default
        init_default_email_templates()
        tpl = EmailTemplate.query.filter_by(key=template_key).first()

    if tpl:
        subj, html_body, _ = tpl.render(context)
    else:
        subj = f"[EnglishMate] Thông báo"
        html_body = f"<p>{context.get('message', '')}</p>"

    return enqueue_email(
        to_email=to_email,
        subject=subj,
        html_content=html_body,
        email_type=template_key,
        scheduled_at=scheduled_at,
        admin_id=admin_id,
        async_send=async_send
    )


def process_scheduled_email_queue() -> int:
    """
    Quét và gửi tất cả các email hẹn giờ (Scheduled Emails) đến hạn gửi trong hàng đợi.
    """
    now_d = now_utc()
    pending = EmailLog.query.filter(
        EmailLog.status == "QUEUED",
        EmailLog.scheduled_at <= now_d
    ).all()

    processed_count = 0
    app_obj = current_app._get_current_object()
    app_config = {
        "MAIL_SERVER": current_app.config.get("MAIL_SERVER"),
        "MAIL_PORT": current_app.config.get("MAIL_PORT"),
        "MAIL_USERNAME": current_app.config.get("MAIL_USERNAME"),
        "MAIL_PASSWORD": current_app.config.get("MAIL_PASSWORD"),
        "MAIL_DEFAULT_SENDER": current_app.config.get("MAIL_DEFAULT_SENDER"),
    }

    for item in pending:
        _worker_deliver_email(lambda: app_obj, item.id, app_config)
        processed_count += 1

    return processed_count


# ---------------------------------------------------------------------------
# TRACKING HANDLERS
# ---------------------------------------------------------------------------

def track_email_open(tracking_id: str) -> bool:
    """Ghi nhận người dùng đã mở email."""
    if not tracking_id:
        return False
    item = EmailLog.query.filter_by(tracking_id=tracking_id).first()
    if item:
        item.open_count += 1
        if not item.opened_at:
            item.opened_at = now_utc()
        if item.status in ("SENT", "QUEUED", "SENDING"):
            item.status = "OPENED"
        try:
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
    return False


def track_email_click(tracking_id: str, target_url: Optional[str] = None) -> bool:
    """Ghi nhận người dùng đã click liên kết trong email."""
    if not tracking_id:
        return False
    item = EmailLog.query.filter_by(tracking_id=tracking_id).first()
    if item:
        item.click_count += 1
        if not item.clicked_at:
            item.clicked_at = now_utc()
        item.status = "CLICKED"
        try:
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
    return False


# ---------------------------------------------------------------------------
# ANALYTICS & REPORTING
# ---------------------------------------------------------------------------

def get_email_analytics(days: int = 30) -> Dict[str, Any]:
    """
    Tổng hợp dữ liệu phân tích hiệu suất email trong khoảng thời gian `days` ngày qua:
    - Tổng số gửi, mở, click, bounce, lỗi.
    - Tỷ lệ Open Rate %, Click Rate %, Bounce Rate %.
    - Biểu đồ thống kê số lượng gửi theo từng ngày.
    - Phân tích theo từng loại email (type breakdown).
    """
    since_dt = now_utc() - timedelta(days=days)
    logs = EmailLog.query.filter(EmailLog.created_at >= since_dt).all()

    total_count = len(logs)
    sent_count = sum(1 for l in logs if l.status in ("SENT", "OPENED", "CLICKED"))
    opened_count = sum(1 for l in logs if l.open_count > 0 or l.status == "OPENED" or l.status == "CLICKED")
    clicked_count = sum(1 for l in logs if l.click_count > 0 or l.status == "CLICKED")
    bounced_count = sum(1 for l in logs if l.status == "BOUNCED")
    failed_count = sum(1 for l in logs if l.status == "FAILED")
    queued_count = sum(1 for l in logs if l.status == "QUEUED")

    open_rate = round((opened_count / sent_count * 100), 1) if sent_count > 0 else 0.0
    click_rate = round((clicked_count / sent_count * 100), 1) if sent_count > 0 else 0.0
    bounce_rate = round((bounced_count / total_count * 100), 1) if total_count > 0 else 0.0

    # Group by date for line/bar chart
    daily_map: Dict[str, Dict[str, int]] = {}
    for i in range(days):
        d_str = (now_utc() - timedelta(days=(days - 1 - i))).strftime("%Y-%m-%d")
        daily_map[d_str] = {"sent": 0, "opened": 0, "bounced": 0}

    for l in logs:
        if l.created_at:
            d_str = l.created_at.strftime("%Y-%m-%d")
            if d_str in daily_map:
                if l.status in ("SENT", "OPENED", "CLICKED"):
                    daily_map[d_str]["sent"] += 1
                if l.open_count > 0 or l.status in ("OPENED", "CLICKED"):
                    daily_map[d_str]["opened"] += 1
                if l.status == "BOUNCED":
                    daily_map[d_str]["bounced"] += 1

    chart_labels = list(daily_map.keys())
    chart_sent = [daily_map[k]["sent"] for k in chart_labels]
    chart_opened = [daily_map[k]["opened"] for k in chart_labels]
    chart_bounced = [daily_map[k]["bounced"] for k in chart_labels]

    # Breakdown by email type
    type_stats: Dict[str, int] = {}
    for l in logs:
        type_stats[l.email_type] = type_stats.get(l.email_type, 0) + 1

    return {
        "days": days,
        "total_count": total_count,
        "sent_count": sent_count,
        "opened_count": opened_count,
        "clicked_count": clicked_count,
        "bounced_count": bounced_count,
        "failed_count": failed_count,
        "queued_count": queued_count,
        "open_rate": open_rate,
        "click_rate": click_rate,
        "bounce_rate": bounce_rate,
        "chart_labels": chart_labels,
        "chart_sent": chart_sent,
        "chart_opened": chart_opened,
        "chart_bounced": chart_bounced,
        "type_stats": type_stats
    }
