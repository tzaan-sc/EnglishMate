import pytest
from app.extensions import db
from app.backend.admin.models import SystemConfig, AuditLog
from app.backend.admin.performance_settings import (
    get_performance_setting,
    get_all_performance_settings,
    get_grouped_performance_settings,
    get_effective_page_size,
    set_performance_setting,
    bulk_update_performance_settings,
    reset_performance_settings,
    PERFORMANCE_SETTINGS_METADATA,
)
from tests.conftest import login


def test_performance_settings_service_helpers(app):
    with app.app_context():
        # Default fallbacks
        assert get_performance_setting("DEFAULT_PAGE_SIZE") == 20
        assert get_performance_setting("STATIC_CACHE_MAX_AGE_SECONDS") == 86400
        assert get_performance_setting("NON_EXISTING_SETTING", default=99) == 99

        # Effective page size with custom query param
        assert get_effective_page_size("DEFAULT_PAGE_SIZE", default=20, custom_arg=50) == 50
        assert get_effective_page_size("DEFAULT_PAGE_SIZE", default=20, custom_arg=None) == 20
        assert get_effective_page_size("DEFAULT_PAGE_SIZE", default=20, custom_arg="invalid") == 20


def test_get_all_and_grouped_performance_settings(app):
    with app.app_context():
        settings = get_all_performance_settings()
        assert len(settings) >= 5
        keys = [s["key"] for s in settings]
        assert "DEFAULT_PAGE_SIZE" in keys
        assert "ADMIN_AUDIT_LOG_PAGE_SIZE" in keys
        assert "ADMIN_IMPORT_HISTORY_PAGE_SIZE" in keys
        assert "STATIC_CACHE_MAX_AGE_SECONDS" in keys
        assert "API_RESPONSE_CACHE_SECONDS" in keys

        grouped = get_grouped_performance_settings()
        assert "PAGINATION" in grouped
        assert "CACHING" in grouped
        assert "DATABASE" in grouped
        assert len(grouped["PAGINATION"]["settings"]) >= 3


def test_set_and_validate_performance_settings(app):
    with app.app_context():
        # Valid update
        res = set_performance_setting("DEFAULT_PAGE_SIZE", 30)
        assert res["success"] is True
        assert get_performance_setting("DEFAULT_PAGE_SIZE") == 30

        # Out of bounds (< min)
        res_low = set_performance_setting("DEFAULT_PAGE_SIZE", 2)
        assert res_low["success"] is False
        assert "phải nằm trong khoảng" in res_low["error"]

        # Out of bounds (> max)
        res_high = set_performance_setting("DEFAULT_PAGE_SIZE", 500)
        assert res_high["success"] is False
        assert "phải nằm trong khoảng" in res_high["error"]

        # Non-integer value
        res_invalid = set_performance_setting("DEFAULT_PAGE_SIZE", "abc")
        assert res_invalid["success"] is False
        assert "không hợp lệ" in res_invalid["error"]

        # Unknown key
        res_unknown = set_performance_setting("UNKNOWN_KEY_ABC", 10)
        assert res_unknown["success"] is False


def test_bulk_update_and_reset_performance_settings(app):
    with app.app_context():
        success, succ_msgs, err_msgs = bulk_update_performance_settings({
            "DEFAULT_PAGE_SIZE": 25,
            "STATIC_CACHE_MAX_AGE_SECONDS": 43200,
            "API_RESPONSE_CACHE_SECONDS": 600,
        })
        assert success is True
        assert len(succ_msgs) == 3
        assert len(err_msgs) == 0
        assert get_performance_setting("DEFAULT_PAGE_SIZE") == 25
        assert get_performance_setting("STATIC_CACHE_MAX_AGE_SECONDS") == 43200
        assert get_performance_setting("API_RESPONSE_CACHE_SECONDS") == 600

        # Reset all settings
        reset_res = reset_performance_settings()
        assert reset_res["success"] is True
        assert get_performance_setting("DEFAULT_PAGE_SIZE") == 20
        assert get_performance_setting("STATIC_CACHE_MAX_AGE_SECONDS") == 86400
        assert get_performance_setting("API_RESPONSE_CACHE_SECONDS") == 300


def test_performance_settings_regular_user_forbidden(client, app):
    login(client, email="student@test.com", password="user123")
    res_user = client.get("/admin/system/performance")
    assert res_user.status_code in (302, 403)


def test_admin_performance_settings_routes(client, app):
    # Login as admin
    login(client, email="admin@test.com", password="admin123")

    # 1. GET page
    res = client.get("/admin/system/performance")
    assert res.status_code == 200
    assert "Cấu hình Thông số Hiệu năng".encode("utf-8") in res.data
    assert "DEFAULT_PAGE_SIZE".encode("utf-8") in res.data
    assert "STATIC_CACHE_MAX_AGE_SECONDS".encode("utf-8") in res.data

    # Alias /admin/performance
    res_alias = client.get("/admin/performance")
    assert res_alias.status_code == 200

    # 2. POST single setting update via JSON
    res_single = client.post(
        "/admin/system/performance/DEFAULT_PAGE_SIZE",
        json={"value": 35}
    )
    assert res_single.status_code == 200
    json_single = res_single.get_json()
    assert json_single["success"] is True
    assert json_single["value"] == 35

    # 3. POST bulk update via JSON
    res_bulk = client.post(
        "/admin/system/performance",
        json={"DEFAULT_PAGE_SIZE": 40, "STATIC_CACHE_MAX_AGE_SECONDS": 3600}
    )
    assert res_bulk.status_code == 200
    json_bulk = res_bulk.get_json()
    assert json_bulk["success"] is True

    with app.app_context():
        assert get_performance_setting("DEFAULT_PAGE_SIZE") == 40
        assert get_performance_setting("STATIC_CACHE_MAX_AGE_SECONDS") == 3600

    # 4. POST reset all settings
    res_reset = client.post("/admin/system/performance/reset", json={})
    assert res_reset.status_code == 200
    json_reset = res_reset.get_json()
    assert json_reset["success"] is True

    with app.app_context():
        assert get_performance_setting("DEFAULT_PAGE_SIZE") == 20


def test_dynamic_static_cache_max_age_header(client, app):
    with app.app_context():
        set_performance_setting("STATIC_CACHE_MAX_AGE_SECONDS", 7200)

    res = client.get("/static/css/app.css")
    # Response headers should include max-age=7200
    assert "Cache-Control" in res.headers
    assert "max-age=7200" in res.headers["Cache-Control"]

    # Cleanup
    with app.app_context():
        reset_performance_settings()


def test_dynamic_audit_logs_pagination(client, app):
    login(client, email="admin@test.com", password="admin123")

    with app.app_context():
        # Create 25 dummy audit logs
        for i in range(25):
            log = AuditLog(
                user_id=1,
                action=f"TEST_ACTION_{i}",
                details=f"Test audit log entry {i}"
            )
            db.session.add(log)
        db.session.commit()

        # Set page size to 10
        set_performance_setting("ADMIN_AUDIT_LOG_PAGE_SIZE", 10)

    # Fetch page 1
    res = client.get("/admin/audit-logs")
    assert res.status_code == 200

    # Cleanup
    with app.app_context():
        reset_performance_settings()
