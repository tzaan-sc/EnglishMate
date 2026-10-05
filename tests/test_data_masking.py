import io
import csv
from tests.conftest import login
from app.backend.admin.data_masking import (
    mask_email,
    mask_ip_address,
    mask_phone,
    mask_text,
    mask_sensitive_dict,
    is_data_masking_enabled,
)


def test_mask_email():
    """Kiểm tra các trường hợp che giấu địa chỉ email."""
    # Standard email
    assert mask_email("user@gmail.com") == "u***r@gmail.com"
    assert mask_email("john.doe@domain.vn") == "j***e@domain.vn"
    assert mask_email("alexander@test.edu.vn") == "a***r@test.edu.vn"

    # Short username cases
    assert mask_email("a@gmail.com") == "a***@gmail.com"
    assert mask_email("ab@gmail.com") == "a***b@gmail.com"
    assert mask_email("abc@gmail.com") == "a***c@gmail.com"

    # Edge cases
    assert mask_email("") == ""
    assert mask_email(None) == ""
    assert mask_email("plain_text") == "p***t"


def test_mask_ip_address():
    """Kiểm tra che giấu địa chỉ IPv4 và IPv6."""
    # IPv4 medium (default)
    assert mask_ip_address("192.168.1.100") == "192.168.***.***"
    assert mask_ip_address("127.0.0.1") == "127.0.***.***"
    assert mask_ip_address("10.0.0.15") == "10.0.***.***"

    # IPv4 low
    assert mask_ip_address("192.168.1.100", mask_level="low") == "192.168.1.***"

    # IPv4 high
    assert mask_ip_address("192.168.1.100", mask_level="high") == "192.***.***.***"

    # IPv6
    ipv6 = "2001:0db8:85a3:0000:0000:8a2e:0370:7334"
    masked_v6 = mask_ip_address(ipv6)
    assert masked_v6.startswith("2001:0db8:")
    assert "****" in masked_v6

    # Edge cases
    assert mask_ip_address("") == ""
    assert mask_ip_address(None) == ""


def test_mask_phone():
    """Kiểm tra che giấu số điện thoại."""
    assert mask_phone("0912345678") == "0912***678"
    assert mask_phone("+84912345678") == "+849***678"
    assert mask_phone("1234") == "****"
    assert mask_phone("") == ""
    assert mask_phone(None) == ""


def test_mask_text():
    """Kiểm tra che giấu chuỗi văn bản tùy ý."""
    assert mask_text("12345678", visible_start=2, visible_end=2) == "12***78"
    assert mask_text("secret_key_value", visible_start=3, visible_end=3) == "sec***lue"
    assert mask_text("abc") == "***"
    assert mask_text("") == ""
    assert mask_text(None) == ""


def test_mask_sensitive_dict():
    """Kiểm tra che giấu đệ quy cho dict payload phức tạp."""
    payload = {
        "username": "learner01",
        "email": "learner@gmail.com",
        "password": "SuperSecretPassword123",
        "ip_address": "192.168.1.50",
        "metadata": {
            "access_token": "eyJhbGciOi...",
            "user_phone": "0987654321",
            "notes": "Public note",
        },
        "history": [
            {"login_ip": "10.0.0.1", "action": "LOGIN"},
            {"api_key": "SECRET123", "action": "CALL_API"}
        ]
    }

    masked = mask_sensitive_dict(payload)
    assert masked["username"] == "learner01"
    assert masked["email"] == "l***r@gmail.com"
    assert masked["password"] == "******"
    assert masked["ip_address"] == "192.168.***.***"
    assert masked["metadata"]["access_token"] == "******"
    assert masked["metadata"]["notes"] == "Public note"
    assert masked["history"][0]["login_ip"] == "10.0.***.***"
    assert masked["history"][1]["api_key"] == "******"


def test_jinja2_template_filters(app):
    """Kiểm tra các bộ lọc Jinja2 trong môi trường template Flask."""
    with app.app_context():
        from flask import render_template_string

        res_email = render_template_string("{{ 'student@domain.com' | mask_email }}")
        assert res_email == "s***t@domain.com"

        res_ip = render_template_string("{{ '192.168.5.20' | mask_ip }}")
        assert res_ip == "192.168.***.***"

        res_phone = render_template_string("{{ '0988776655' | mask_phone }}")
        assert res_phone == "0988***655"



def test_audit_logs_export_with_data_masking(client, app):
    """Kiểm tra tính năng export audit logs với cờ che giấu dữ liệu."""
    login(client, "admin@test.com", "admin123")

    # Export without mask
    res_normal = client.get("/admin/audit-logs/export")
    assert res_normal.status_code == 200

    # Export with mask=1
    res_masked = client.get("/admin/audit-logs/export?mask=1")
    assert res_masked.status_code == 200
    content = res_masked.data.decode("utf-8")
    assert "Mã Log" in content


def test_data_masking_admin_api_endpoints(client, app):
    """Admin có thể gọi API preview và API che giấu payload."""
    # 1. Non-admin forbidden
    login(client, "student@test.com", "user123")
    res_prev_non_admin = client.get("/admin/system/data-masking/preview")
    assert res_prev_non_admin.status_code == 403

    # Logout student
    client.post("/auth/logout")

    # 2. Admin preview
    login(client, "admin@test.com", "admin123")
    res_preview = client.get("/admin/system/data-masking/preview?email=alex@test.com&ip=10.1.2.3")
    assert res_preview.status_code == 200
    data = res_preview.get_json()
    assert data["success"] is True
    assert data["masked"]["email"] == "a***x@test.com"
    assert data["masked"]["ip_medium"] == "10.1.***.***"

    # 3. Admin mask payload
    res_mask = client.post("/admin/system/data-masking/mask", json={
        "email": "test@gmail.com",
        "password": "123",
        "ip": "1.2.3.4"
    })
    assert res_mask.status_code == 200
    mask_data = res_mask.get_json()
    assert mask_data["success"] is True
    assert mask_data["masked_data"]["password"] == "******"
    assert mask_data["masked_data"]["email"] == "t***t@gmail.com"
