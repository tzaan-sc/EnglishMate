from tests.conftest import login
from app.backend.admin.models import SystemConfig
from app.backend.admin.security_headers import (
    get_security_headers_config,
    save_security_headers_config,
    apply_security_headers,
)


def test_default_security_headers_present_on_response(client):
    """Mỗi HTTP response đều được gắn đầy đủ các header bảo mật chuẩn quốc tế."""
    res = client.get("/")
    assert res.status_code == 200

    # 1. Anti-MIME sniffing
    assert res.headers.get("X-Content-Type-Options") == "nosniff"

    # 2. Anti-Clickjacking
    assert res.headers.get("X-Frame-Options") in ("SAMEORIGIN", "DENY")

    # 3. Reflected XSS Filter
    assert res.headers.get("X-XSS-Protection") == "1; mode=block"

    # 4. Referrer Policy
    assert res.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"

    # 5. Permissions Policy
    perm_policy = res.headers.get("Permissions-Policy", "")
    assert "microphone=(self)" in perm_policy

    # 6. Content Security Policy (CSP)
    csp = res.headers.get("Content-Security-Policy", "")
    assert "default-src 'self'" in csp
    assert "script-src" in csp


def test_hsts_header_on_https_request(client):
    """Khi truy cập qua HTTPS hoặc proxy HTTPS, header HSTS được tự động gắn."""
    res = client.get("/", headers={"X-Forwarded-Proto": "https"})
    assert res.status_code == 200
    hsts = res.headers.get("Strict-Transport-Security", "")
    assert "max-age=31536000" in hsts


def test_admin_security_headers_api_security(client):
    """Học viên bình thường không được phép chỉnh sửa Security Headers."""
    login(client, "student@test.com", "user123")
    res = client.get("/admin/system/security-headers")
    assert res.status_code == 403

    res_post = client.post("/admin/system/security-headers", json={"SECURITY_HEADERS_ENABLED": False})
    assert res_post.status_code == 403


def test_admin_get_and_update_security_headers(client, app):
    """Admin có thể truy vấn và tùy biến cấu hình Security Headers."""
    login(client, "admin@test.com", "admin123")

    # 1. Get config
    res_get = client.get("/admin/system/security-headers")
    assert res_get.status_code == 200
    data = res_get.get_json()
    assert data["success"] is True
    assert "config" in data

    # 2. Update Frame Options to DENY
    res_update = client.post("/admin/system/security-headers", json={
        "SECURITY_FRAME_OPTIONS": "DENY",
        "SECURITY_HSTS_ENABLED": True
    })
    assert res_update.status_code == 200
    assert res_update.get_json()["success"] is True

    # 3. Verify on subsequent response
    res_after = client.get("/")
    assert res_after.headers.get("X-Frame-Options") == "DENY"
    assert "max-age=31536000" in res_after.headers.get("Strict-Transport-Security", "")


def test_disable_security_headers_toggle(client, app):
    """Khi tắt SECURITY_HEADERS_ENABLED, các header tùy biến không được gắn."""
    login(client, "admin@test.com", "admin123")

    # Disable headers
    client.post("/admin/system/security-headers", json={"SECURITY_HEADERS_ENABLED": False})

    res = client.get("/")
    # Verify disabled
    assert res.headers.get("X-Content-Type-Options") is None
    assert res.headers.get("Content-Security-Policy") is None

    # Re-enable
    client.post("/admin/system/security-headers", json={"SECURITY_HEADERS_ENABLED": True})
    res_enabled = client.get("/")
    assert res_enabled.headers.get("X-Content-Type-Options") == "nosniff"
