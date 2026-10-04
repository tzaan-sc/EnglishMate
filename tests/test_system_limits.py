import io
import time
from datetime import datetime, timezone
import pytest
from app.extensions import db
from app.backend.admin.models import SystemConfig, AuditLog
from app.backend.admin.system_limits import (
    get_system_limit,
    get_all_system_limits,
    get_grouped_system_limits,
    set_system_limit,
    bulk_update_system_limits,
    reset_system_limits,
    SYSTEM_LIMITS_METADATA,
)
from app.backend.auth.models import User
from tests.conftest import login


def test_system_config_typed_helpers(app):
    with app.app_context():
        # Defaults
        assert SystemConfig.get_int_config("NON_EXISTING_KEY", default=42) == 42
        assert SystemConfig.get_float_config("NON_EXISTING_FLOAT", default=3.14) == 3.14

        # Set config
        SystemConfig.set_config("TEST_LIMIT_KEY", 100, description="Test limit", category="LIMITS")
        assert SystemConfig.get_int_config("TEST_LIMIT_KEY") == 100
        assert SystemConfig.get_float_config("TEST_LIMIT_KEY") == 100.0

        # Update config
        SystemConfig.set_config("TEST_LIMIT_KEY", 250)
        assert SystemConfig.get_int_config("TEST_LIMIT_KEY") == 250


def test_get_all_and_grouped_system_limits(app):
    with app.app_context():
        limits = get_all_system_limits()
        assert len(limits) >= 5
        keys = [lim["key"] for lim in limits]
        assert "MAX_FAILED_LOGIN_ATTEMPTS" in keys
        assert "LOCKOUT_MINUTES" in keys
        assert "SESSION_TIMEOUT_MINUTES" in keys
        assert "MAX_AVATAR_SIZE_MB" in keys
        assert "MAX_UPLOAD_SIZE_MB" in keys

        grouped = get_grouped_system_limits()
        assert "SECURITY" in grouped
        assert "SESSION" in grouped
        assert "STORAGE" in grouped
        assert len(grouped["SECURITY"]["limits"]) >= 2


def test_set_and_validate_system_limits(app):
    with app.app_context():
        # Valid update
        res = set_system_limit("MAX_FAILED_LOGIN_ATTEMPTS", 8)
        assert res["success"] is True
        assert get_system_limit("MAX_FAILED_LOGIN_ATTEMPTS") == 8

        # Out of bounds (< min)
        res_low = set_system_limit("MAX_FAILED_LOGIN_ATTEMPTS", 1)
        assert res_low["success"] is False
        assert "phải nằm trong khoảng" in res_low["error"]

        # Out of bounds (> max)
        res_high = set_system_limit("MAX_FAILED_LOGIN_ATTEMPTS", 999)
        assert res_high["success"] is False
        assert "phải nằm trong khoảng" in res_high["error"]

        # Non-integer value
        res_invalid = set_system_limit("MAX_FAILED_LOGIN_ATTEMPTS", "invalid_number")
        assert res_invalid["success"] is False
        assert "không hợp lệ" in res_invalid["error"]

        # Unknown key
        res_unknown = set_system_limit("UNKNOWN_KEY_XYZ", 10)
        assert res_unknown["success"] is False


def test_bulk_update_and_reset_system_limits(app):
    with app.app_context():
        success, succ_msgs, err_msgs = bulk_update_system_limits({
            "MAX_FAILED_LOGIN_ATTEMPTS": 7,
            "LOCKOUT_MINUTES": 20,
            "SESSION_TIMEOUT_MINUTES": 60,
        })
        assert success is True
        assert len(succ_msgs) == 3
        assert len(err_msgs) == 0
        assert get_system_limit("MAX_FAILED_LOGIN_ATTEMPTS") == 7
        assert get_system_limit("LOCKOUT_MINUTES") == 20
        assert get_system_limit("SESSION_TIMEOUT_MINUTES") == 60

        # Reset all limits
        reset_res = reset_system_limits()
        assert reset_res["success"] is True
        assert get_system_limit("MAX_FAILED_LOGIN_ATTEMPTS") == 5
        assert get_system_limit("LOCKOUT_MINUTES") == 15
        assert get_system_limit("SESSION_TIMEOUT_MINUTES") == 30


def test_system_limits_regular_user_forbidden(client, app):
    login(client, email="student@test.com", password="user123")
    res_user = client.get("/admin/system/limits")
    assert res_user.status_code in (302, 403)


def test_admin_system_limits_routes(client, app):
    # Login as admin
    login(client, email="admin@test.com", password="admin123")

    # 1. GET page
    res = client.get("/admin/system/limits")
    assert res.status_code == 200
    assert "Cấu hình Giới hạn Hệ thống".encode("utf-8") in res.data
    assert "MAX_FAILED_LOGIN_ATTEMPTS".encode("utf-8") in res.data

    # Alias /admin/limits
    res_alias = client.get("/admin/limits")
    assert res_alias.status_code == 200

    # 2. POST single limit update via JSON
    res_single = client.post(
        "/admin/system/limits/MAX_FAILED_LOGIN_ATTEMPTS",
        json={"value": 6}
    )
    assert res_single.status_code == 200
    json_single = res_single.get_json()
    assert json_single["success"] is True
    assert json_single["value"] == 6

    # 3. POST bulk update via JSON
    res_bulk = client.post(
        "/admin/system/limits",
        json={"MAX_FAILED_LOGIN_ATTEMPTS": 10, "LOCKOUT_MINUTES": 30}
    )
    assert res_bulk.status_code == 200
    json_bulk = res_bulk.get_json()
    assert json_bulk["success"] is True

    with app.app_context():
        assert get_system_limit("MAX_FAILED_LOGIN_ATTEMPTS") == 10
        assert get_system_limit("LOCKOUT_MINUTES") == 30

    # 4. POST reset all limits
    res_reset = client.post("/admin/system/limits/reset", json={})
    assert res_reset.status_code == 200
    json_reset = res_reset.get_json()
    assert json_reset["success"] is True

    with app.app_context():
        assert get_system_limit("MAX_FAILED_LOGIN_ATTEMPTS") == 5



def test_dynamic_login_lockout_with_system_config(client, app):
    with app.app_context():
        # Set max failed attempts to 3 and lockout to 5 minutes
        set_system_limit("MAX_FAILED_LOGIN_ATTEMPTS", 3)
        set_system_limit("LOCKOUT_MINUTES", 5)

        user = User.query.filter_by(email="student@test.com").first()
        user.failed_login_attempts = 0
        user.lockout_until = None
        db.session.commit()

    # Attempt 1 failed login
    res1 = client.post("/auth/login", data={"email": "student@test.com", "password": "wrongpassword1"}, follow_redirects=True)
    assert res1.status_code == 200
    assert "Bạn còn 2 lần thử".encode("utf-8") in res1.data

    # Attempt 2 failed login
    res2 = client.post("/auth/login", data={"email": "student@test.com", "password": "wrongpassword2"}, follow_redirects=True)
    assert res2.status_code == 200
    assert "Bạn còn 1 lần thử".encode("utf-8") in res2.data

    # Attempt 3 failed login -> locked for 5 minutes
    res3 = client.post("/auth/login", data={"email": "student@test.com", "password": "wrongpassword3"}, follow_redirects=True)
    assert res3.status_code == 200
    assert "Tài khoản của bạn đã bị khóa 5 phút do nhập sai mật khẩu 3 lần".encode("utf-8") in res3.data

    # Cleanup: unlock user and reset limits
    with app.app_context():
        user = User.query.filter_by(email="student@test.com").first()
        user.failed_login_attempts = 0
        user.lockout_until = None
        db.session.commit()
        reset_system_limits()


def test_dynamic_avatar_size_limit(client, app):
    login(client, email="student@test.com", password="user123")

    with app.app_context():
        # Set avatar max size to 1 MB
        set_system_limit("MAX_AVATAR_SIZE_MB", 1)

    # 1. Upload valid avatar (< 1MB)
    small_file = (io.BytesIO(b"dummy image data" * 10), "avatar_small.png")
    res_valid = client.post("/profile/edit-info", data={"avatar": small_file, "full_name": "Test User"}, follow_redirects=True)
    assert res_valid.status_code == 200
    assert "Cập nhật thông tin cá nhân thành công".encode("utf-8") in res_valid.data

    # 2. Upload oversized avatar (> 1MB)
    oversized_data = b"X" * (2 * 1024 * 1024)  # 2MB
    large_file = (io.BytesIO(oversized_data), "avatar_large.png")
    res_large = client.post("/profile/edit-info", data={"avatar": large_file, "full_name": "Test User"}, follow_redirects=True)
    assert res_large.status_code == 200
    assert "vượt quá giới hạn cho phép (1MB)".encode("utf-8") in res_large.data

    # Cleanup
    with app.app_context():
        reset_system_limits()
