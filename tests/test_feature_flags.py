import pytest
from app.extensions import db
from app.backend.admin.models import SystemConfig, AuditLog
from app.backend.admin.feature_flags import (
    is_feature_enabled,
    get_all_feature_flags,
    set_feature_flag,
    feature_flag_required
)
from tests.conftest import login


def test_system_config_model_and_helper(app):
    with app.app_context():
        # Default fallback
        assert is_feature_enabled("ARCADE_GAMES") is True
        assert is_feature_enabled("NON_EXISTENT_FEATURE", default=False) is False

        # Set feature status
        SystemConfig.set_feature_status("TEST_FLAG_1", is_active=False, description="Test description", category="GENERAL")
        assert is_feature_enabled("TEST_FLAG_1") is False

        SystemConfig.set_feature_status("TEST_FLAG_1", is_active=True)
        assert is_feature_enabled("TEST_FLAG_1") is True


def test_get_all_feature_flags(app):
    with app.app_context():
        flags = get_all_feature_flags()
        assert len(flags) >= 5
        keys = [f["key"] for f in flags]
        assert "ARCADE_GAMES" in keys
        assert "AI_GRADING" in keys
        assert "USER_REGISTRATION" in keys
        assert "BADGE_SHARING" in keys


def test_set_feature_flag_with_audit_log(app):
    with app.app_context():
        res = set_feature_flag("ARCADE_GAMES", is_active=False)
        assert res["success"] is True
        assert res["is_active"] is False
        assert is_feature_enabled("ARCADE_GAMES") is False

        # Re-enable
        res_enable = set_feature_flag("ARCADE_GAMES", is_active=True)
        assert res_enable["success"] is True
        assert res_enable["is_active"] is True
        assert is_feature_enabled("ARCADE_GAMES") is True


def test_admin_feature_flags_page_and_api(client, app):
    login(client, email="admin@test.com", password="admin123")

    # 1. GET admin feature flags page
    res = client.get("/admin/system/feature-flags")
    assert res.status_code == 200
    assert "Quản lý Tính năng Hệ thống".encode("utf-8") in res.data
    assert "ARCADE_GAMES".encode("utf-8") in res.data
    assert "AI_GRADING".encode("utf-8") in res.data

    # Alias /admin/feature-flags
    res_alias = client.get("/admin/feature-flags")
    assert res_alias.status_code == 200

    # 2. POST toggle flag
    toggle_res = client.post(
        "/admin/system/feature-flags/ARCADE_GAMES/toggle",
        json={"is_active": False}
    )
    assert toggle_res.status_code == 200
    toggle_json = toggle_res.get_json()
    assert toggle_json["success"] is True
    assert toggle_json["is_active"] is False

    with app.app_context():
        assert is_feature_enabled("ARCADE_GAMES") is False

    # 3. POST bulk update
    bulk_res = client.post(
        "/admin/system/feature-flags/bulk",
        json={"flags": {"ARCADE_GAMES": True, "AI_GRADING": False}}
    )
    assert bulk_res.status_code == 200
    bulk_json = bulk_res.get_json()
    assert bulk_json["success"] is True
    assert bulk_json["updated_count"] == 2

    with app.app_context():
        assert is_feature_enabled("ARCADE_GAMES") is True
        assert is_feature_enabled("AI_GRADING") is False
        # Reset AI_GRADING to True
        set_feature_flag("AI_GRADING", True)


def test_feature_flag_blocks_registration_when_disabled(client, app):
    # Disable USER_REGISTRATION
    with app.app_context():
        set_feature_flag("USER_REGISTRATION", False)

    # Attempt to access register page as guest
    res = client.get("/auth/register", follow_redirects=False)
    assert res.status_code == 302
    assert "/auth/login" in res.headers["Location"]

    # Re-enable USER_REGISTRATION
    with app.app_context():
        set_feature_flag("USER_REGISTRATION", True)

    res_enabled = client.get("/auth/register")
    assert res_enabled.status_code == 200
    assert "Đăng ký".encode("utf-8") in res_enabled.data


def test_feature_flag_blocks_arcade_games_when_disabled(client, app):
    # Login as student
    login(client, email="student@test.com", password="user123")

    # Disable ARCADE_GAMES
    with app.app_context():
        set_feature_flag("ARCADE_GAMES", False)

    # Attempt to access game lobby
    res = client.get("/games/lobby", follow_redirects=False)
    assert res.status_code == 302
    assert "/lessons" in res.headers["Location"]

    # Re-enable ARCADE_GAMES
    with app.app_context():
        set_feature_flag("ARCADE_GAMES", True)

    res_enabled = client.get("/games/lobby")
    assert res_enabled.status_code == 200


def test_admin_bypasses_disabled_feature(client, app):
    login(client, email="admin@test.com", password="admin123")

    # Disable ARCADE_GAMES
    with app.app_context():
        set_feature_flag("ARCADE_GAMES", False)

    # Admin should bypass and access /games/lobby normally
    res = client.get("/games/lobby")
    assert res.status_code == 200

    # Cleanup
    with app.app_context():
        set_feature_flag("ARCADE_GAMES", True)
