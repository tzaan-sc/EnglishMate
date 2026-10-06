import json
import time
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

import pytest

from app.extensions import db
from app.backend.admin.models import EmailLog, EmailTemplate, EmailBounce
from app.backend.auth.models import User
from app.backend.admin.email_service import (
    enqueue_email,
    send_templated_email,
    init_default_email_templates,
    get_email_analytics,
    track_email_open,
    track_email_click,
    record_email_bounce,
    is_email_bounced,
    process_scheduled_email_queue,
)
from app.utils.email import send_email


def _login_admin(client):
    return client.post("/auth/login", data={"email": "admin@test.com", "password": "admin123"}, follow_redirects=True)


# ===========================================================================
# 1. EMAIL QUEUE & ASYNC SENDING
# ===========================================================================

def test_enqueue_email_async(app):
    """Test đưa email vào hàng đợi gửi bất đồng bộ thành công."""
    with app.app_context():
        res = enqueue_email(
            to_email="student@example.com",
            subject="Chào mừng bạn đến với EnglishMate",
            html_content="<p>Nội dung kiểm tra hàng đợi</p>",
            email_type="WELCOME",
            async_send=False
        )

        assert res["success"] is True
        assert res["status"] in ("SENT", "QUEUED")
        assert "tracking_id" in res

        # Verify database record
        log = EmailLog.query.filter_by(tracking_id=res["tracking_id"]).first()
        assert log is not None
        assert log.recipient == "student@example.com"
        assert log.subject == "Chào mừng bạn đến với EnglishMate"


def test_send_email_utils_wrapper(app):
    """Test hàm wrapper send_email trong app/utils/email.py."""
    with app.app_context():
        success = send_email(
            to_email="test_user@example.com",
            subject="Test Subject Wrapper",
            html_content="<p>Test Body</p>",
            email_type="NOTIFICATION",
            async_send=False
        )
        assert success is True


# ===========================================================================
# 2. EMAIL TRACKING (OPEN PIXEL & CLICK TRACKING)
# ===========================================================================

def test_email_open_and_click_tracking(app, client):
    """Test theo dõi lượt mở pixel và lượt click liên kết trong email."""
    with app.app_context():
        res = enqueue_email(
            to_email="learner@example.com",
            subject="Bài học hôm nay",
            html_content="<p>Click <a href='https://englishmate.vn'>vào đây</a></p>",
            async_send=False
        )
        tracking_id = res["tracking_id"]

    # 1. Simulate user opening the email (Tracking Pixel GET request)
    pixel_resp = client.get(f"/email/track/open/{tracking_id}.png")
    assert pixel_resp.status_code == 200
    assert pixel_resp.mimetype == "image/png"

    with app.app_context():
        log = EmailLog.query.filter_by(tracking_id=tracking_id).first()
        assert log.open_count == 1
        assert log.opened_at is not None
        assert log.status in ("OPENED", "SENT")

    # 2. Simulate user clicking a link in email
    click_resp = client.get(f"/email/track/click/{tracking_id}?url=https://englishmate.vn/dashboard")
    assert click_resp.status_code == 302
    assert "https://englishmate.vn/dashboard" in click_resp.headers["Location"]

    with app.app_context():
        log = EmailLog.query.filter_by(tracking_id=tracking_id).first()
        assert log.click_count == 1
        assert log.clicked_at is not None
        assert log.status == "CLICKED"


# ===========================================================================
# 3. EMAIL BOUNCE HANDLING
# ===========================================================================

def test_email_bounce_recording_and_blocking(app):
    """Test ghi nhận email bounce và chặn các lần gửi tiếp theo."""
    with app.app_context():
        bad_email = "nonexistent_mailbox_999@domain-does-not-exist.xyz"

        # Record bounce
        bounce = record_email_bounce(bad_email, "550 User unknown", "HARD_BOUNCE")
        assert bounce is not None
        assert is_email_bounced(bad_email) is True

        # Try to send to bounced email -> Should be rejected immediately
        res = enqueue_email(
            to_email=bad_email,
            subject="Test sending to bounced",
            html_content="<p>Test</p>",
            async_send=False
        )
        assert res["success"] is False
        assert res["status"] == "BOUNCED"


# ===========================================================================
# 4. EMAIL ANALYTICS
# ===========================================================================

def test_email_analytics_metrics(app):
    """Test tính toán thống kê Analytics (Open rate %, Click rate %, Bounce count)."""
    with app.app_context():
        # Clean/seed some logs
        enqueue_email("user1@test.com", "Subj 1", "<p>Body 1</p>", email_type="VERIFICATION", async_send=False)
        res2 = enqueue_email("user2@test.com", "Subj 2", "<p>Body 2</p>", email_type="RESET_PASSWORD", async_send=False)
        track_email_open(res2["tracking_id"])

        analytics = get_email_analytics(days=7)
        assert analytics["total_count"] >= 2
        assert "open_rate" in analytics
        assert "click_rate" in analytics
        assert "chart_labels" in analytics
        assert len(analytics["chart_sent"]) == 7


# ===========================================================================
# 5. EMAIL SCHEDULING
# ===========================================================================

def test_email_scheduling_and_processing(app):
    """Test tính năng hẹn giờ gửi email và quét hàng đợi."""
    with app.app_context():
        # 1. Schedule email in future
        future_time = datetime.now(timezone.utc) + timedelta(hours=2)
        res = enqueue_email(
            to_email="scheduled_user@test.com",
            subject="Scheduled Announcement",
            html_content="<p>Nội dung hẹn giờ</p>",
            scheduled_at=future_time,
            async_send=False
        )
        assert res["success"] is True
        assert res["status"] == "QUEUED"

        # 2. Simulate time reaching due by moving scheduled_at to past
        log = EmailLog.query.filter_by(tracking_id=res["tracking_id"]).first()
        log.scheduled_at = datetime.now(timezone.utc) - timedelta(seconds=10)
        db.session.commit()

        # 3. Process queue
        processed = process_scheduled_email_queue()
        assert processed >= 1

        db.session.refresh(log)
        assert log.status in ("SENT", "SENDING")


# ===========================================================================
# 6. EMAIL TEMPLATES MANAGEMENT
# ===========================================================================

def test_email_templates_initialization_and_rendering(app):
    """Test khởi tạo và render mẫu HTML EmailTemplate với dynamic context."""
    with app.app_context():
        init_default_email_templates()

        tpl = EmailTemplate.query.filter_by(key="VERIFICATION_EMAIL").first()
        assert tpl is not None
        assert "{{ otp_code }}" in tpl.subject or "{{ otp_code }}" in tpl.html_content

        # Test render
        subj, html, text_body = tpl.render({"username": "Minh Anh", "otp_code": "123456", "expire_minutes": "10"})
        assert "123456" in subj or "123456" in html
        assert "Minh Anh" in html


def test_admin_email_dashboard_and_templates_api(client):
    """Test các API Admin quản trị Email (Dashboard, Update Template, Send Test, Process Queue)."""
    _login_admin(client)

    # 1. Access Dashboard
    dash_resp = client.get("/admin/system/email")
    assert dash_resp.status_code == 200
    assert "Quản lý Hệ thống Email".encode("utf-8") in dash_resp.data

    # 2. Get Analytics API
    ana_resp = client.get("/admin/system/email/analytics?days=7")
    assert ana_resp.status_code == 200
    ana_json = ana_resp.get_json()
    assert ana_json["success"] is True

    # 3. Preview Template API
    prev_resp = client.post(
        "/admin/system/email/templates/preview",
        json={
            "subject": "Chào {{ username }}",
            "html_content": "<p>OTP của bạn là: {{ otp_code }}</p>",
            "variables": {"username": "Hoàng", "otp_code": "999888"}
        },
        headers={"Content-Type": "application/json"}
    )
    assert prev_resp.status_code == 200
    prev_json = prev_resp.get_json()
    assert "Hoàng" in prev_json["subject"]
    assert "999888" in prev_json["html_content"]

    # 4. Send Test Email API
    send_resp = client.post(
        "/admin/system/email/send-test",
        json={
            "recipient": "admin_test_receiver@example.com",
            "template_key": "VERIFICATION_EMAIL"
        },
        headers={"Content-Type": "application/json"}
    )
    assert send_resp.status_code == 200
    send_json = send_resp.get_json()
    assert send_json["success"] is True

    # 5. Process Queue API
    proc_resp = client.post("/admin/system/email/process-queue", headers={"Content-Type": "application/json"})
    assert proc_resp.status_code == 200
    assert proc_resp.get_json()["success"] is True
