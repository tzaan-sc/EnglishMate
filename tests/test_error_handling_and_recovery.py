import time
import pytest
from flask import g
from app.extensions import db
from app.backend.admin.models import SupportTicket, SystemErrorLog, BackgroundTask
from app.backend.admin.error_recovery_service import (
    retry_with_backoff,
    CircuitBreaker,
    CircuitBreakerOpenException,
    run_system_recovery_diagnostics,
    recover_zombie_tasks,
    circuit_breaker_registry,
)
from app.backend.admin.error_monitoring_service import (
    get_error_patterns_analysis,
    lookup_error_by_trace_or_id,
    record_system_error,
)
from tests.conftest import login


def test_error_correlation_trace_id(client):
    """Mục 15.1: Kiểm tra gắn Request Trace ID và trả về header X-Request-ID."""
    # 1. Custom Request ID in headers
    custom_trace = "REQ-TEST-CUSTOM-12345"
    res = client.get("/support", headers={"X-Request-ID": custom_trace})
    assert res.status_code == 200
    assert res.headers.get("X-Request-ID") == custom_trace

    # 2. Auto-generated Request ID
    res2 = client.get("/support")
    assert res2.status_code == 200
    assert "X-Request-ID" in res2.headers
    assert res2.headers["X-Request-ID"].startswith("REQ-")


def test_error_patterns_analysis(app):
    """Mục 15.1: Kiểm tra gom nhóm và phân loại mẫu lỗi (Error Patterns)."""
    with app.app_context():
        # Record sample errors
        record_system_error(
            exc=TimeoutError("OperationalError: database table is locked or timeout"),
            status_code=500,
            severity="CRITICAL",
            route="/api/v1/lessons",
            custom_message="Database lock timeout"
        )
        record_system_error(
            exc=ValueError("Invalid parameter input data format"),
            status_code=400,
            severity="ERROR",
            route="/api/v1/auth/login",
            custom_message="Validation error"
        )

        patterns = get_error_patterns_analysis(days=1)
        assert len(patterns) >= 1
        pattern_codes = [p["code"] for p in patterns]
        assert any("DB" in c or "VALIDATION" in c or "RUNTIME" in c for c in pattern_codes)


def test_automatic_retry_decorator():
    """Mục 15.2: Kiểm tra cơ chế tự động gọi lại (Automatic Retry) với Exponential Backoff."""
    attempt_count = 0

    @retry_with_backoff(max_retries=3, base_delay=0.01, backoff_factor=1.5, jitter=False)
    def flappy_service():
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 3:
            raise ConnectionResetError("Mạng chập chờn")
        return "SUCCESS"

    result = flappy_service()
    assert result == "SUCCESS"
    assert attempt_count == 3

    # Test failure when retries exceeded
    fail_count = 0

    @retry_with_backoff(max_retries=2, base_delay=0.01, backoff_factor=1.2, jitter=False)
    def always_broken():
        nonlocal fail_count
        fail_count += 1
        raise TimeoutError("Dịch vụ chết hẳn")

    with pytest.raises(TimeoutError):
        always_broken()
    assert fail_count == 3  # 1 initial + 2 retries


def test_circuit_breaker_state_machine():
    """Mục 15.2: Kiểm tra Circuit Breaker (CLOSED -> OPEN -> HALF_OPEN / RESET)."""
    cb = CircuitBreaker(
        name="test_service",
        failure_threshold=3,
        recovery_timeout=0.1,  # 100ms for fast test
        description="Test breaker"
    )

    assert cb.state == CircuitBreaker.STATE_CLOSED

    def failing_call():
        raise RuntimeError("Service down")

    def success_call():
        return "OK"

    # Trip the breaker by failing 3 times
    for _ in range(3):
        with pytest.raises(RuntimeError):
            cb.call(failing_call)

    assert cb.state == CircuitBreaker.STATE_OPEN

    # While OPEN, calls fail fast with CircuitBreakerOpenException without invoking func
    with pytest.raises(CircuitBreakerOpenException) as exc_info:
        cb.call(success_call)
    assert "tạm thời bị ngắt mạch" in str(exc_info.value)

    # Wait for recovery timeout to transition to HALF_OPEN
    time.sleep(0.12)
    assert cb.state == CircuitBreaker.STATE_HALF_OPEN

    # Canary request succeeds -> resets to CLOSED
    cb.call(success_call)
    cb.call(success_call)
    assert cb.state == CircuitBreaker.STATE_CLOSED


def test_system_recovery_diagnostics(app):
    """Mục 15.2: Kiểm tra quy trình Tự chẩn đoán & Phục hồi Hệ thống."""
    with app.app_context():
        res = run_system_recovery_diagnostics(force_recovery=False)
        assert res["status"] in ("OPERATIONAL", "DEGRADED")
        assert res["database"]["status"] in ("HEALTHY", "RECOVERED")
        assert "circuit_breakers" in res
        assert isinstance(res["circuit_breakers"], list)


def test_support_hub_and_faq_routes(client):
    """Mục 15.3: Kiểm tra các trang Support, FAQ, Error Tutorials, Video Tutorials."""
    res_support = client.get("/support")
    assert res_support.status_code == 200
    assert "Trung tâm Hỗ trợ" in res_support.get_data(as_text=True)

    res_faq = client.get("/faq")
    assert res_faq.status_code == 200
    assert "Câu hỏi thường gặp" in res_faq.get_data(as_text=True)

    res_tut = client.get("/tutorials/errors")
    assert res_tut.status_code == 200
    assert "Microphone" in res_tut.get_data(as_text=True)

    res_vid = client.get("/tutorials/videos")
    assert res_vid.status_code == 200
    assert "Video Hướng dẫn" in res_vid.get_data(as_text=True)


def test_support_ticket_lifecycle(client, app):
    """Mục 15.3: Kiểm tra vòng đời gửi phiếu hỗ trợ, tra cứu và Admin phản hồi."""
    # 1. User submits ticket via API
    ticket_payload = {
        "title": "Lỗi không thu âm được mic khi luyện IPA",
        "description": "Tôi bấm nút thu âm nhưng trình duyệt không hiện sóng âm thanh.",
        "category": "TECHNICAL",
        "priority": "HIGH",
        "name": "Nguyen Van Test",
        "email": "student_test@example.com",
        "trace_id": "REQ-TEST-IPA-999"
    }
    res = client.post("/api/support/tickets", json=ticket_payload)
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    ticket_code = data["ticket_code"]
    assert ticket_code.startswith("TKT-")

    # 2. Lookup ticket by code
    res_lookup = client.get(f"/api/support/tickets/{ticket_code}")
    assert res_lookup.status_code == 200
    lookup_data = res_lookup.get_json()
    assert lookup_data["ticket"]["title"] == ticket_payload["title"]
    assert lookup_data["ticket"]["status"] == "OPEN"

    # 3. Admin views tickets and sends reply
    login(client, "admin@test.com", "admin123")
    res_admin = client.get("/admin/tickets")
    assert res_admin.status_code == 200
    assert ticket_code in res_admin.get_data(as_text=True)

    with app.app_context():
        ticket_obj = SupportTicket.query.filter_by(ticket_code=ticket_code).first()
        assert ticket_obj is not None

        # Admin replies
        res_reply = client.post(
            f"/admin/tickets/{ticket_obj.id}/reply",
            data={
                "admin_reply": "Bạn hãy mở Cài đặt trình duyệt và cho phép Micro theo hướng dẫn nhé.",
                "status": "RESOLVED"
            },
            follow_redirects=True
        )
        assert res_reply.status_code == 200

        # Verify status is RESOLVED
        updated_ticket = db.session.get(SupportTicket, ticket_obj.id)
        assert updated_ticket.status == "RESOLVED"
        assert updated_ticket.admin_reply is not None


def test_live_chat_assistant_api(client):
    """Mục 15.3: Kiểm tra Trợ lý Live Chat Assistant API."""
    res_mic = client.post("/api/support/chat", json={"message": "Tôi bị lỗi không nhận micro"})
    assert res_mic.status_code == 200
    data_mic = res_mic.get_json()
    assert data_mic["success"] is True
    assert "Microphone" in data_mic["reply"] or "micro" in data_mic["reply"].lower()

    res_otp = client.post("/api/support/chat", json={"message": "Không nhận được mã xác thực OTP"})
    assert res_otp.status_code == 200
    data_otp = res_otp.get_json()
    assert "OTP" in data_otp["reply"] or "Spam" in data_otp["reply"]


def test_admin_recovery_dashboard_and_breakers(client):
    """Mục 15.2: Kiểm tra Admin Recovery Dashboard và Reset / Trip Circuit Breaker."""
    login(client, "admin@test.com", "admin123")

    res = client.get("/admin/system/recovery")
    assert res.status_code == 200
    assert "Circuit Breakers" in res.get_data(as_text=True)

    # Test Trip breaker API
    res_trip = client.post("/admin/system/recovery/circuit-breakers/gemini_ai/trip", json={})
    assert res_trip.status_code == 200
    assert circuit_breaker_registry.get("gemini_ai").state == CircuitBreaker.STATE_OPEN

    # Test Reset breaker API
    res_reset = client.post("/admin/system/recovery/circuit-breakers/gemini_ai/reset", json={})
    assert res_reset.status_code == 200
    assert circuit_breaker_registry.get("gemini_ai").state == CircuitBreaker.STATE_CLOSED
