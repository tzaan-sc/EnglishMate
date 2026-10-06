"""Tests for Theming (Dark Mode), Onboarding Tour state, and UX features."""
import pytest
from app.backend.auth.models import User
from app.extensions import db
from tests.conftest import login


def test_save_theme_preference_api(client):
    login(client, "student@test.com", "user123")
    res = client.post("/api/preferences/theme", json={"theme": "dark"})
    assert res.status_code == 200
    data = res.get_json()
    assert data["ok"] is True
    assert data["theme"] == "dark"

    # Verify persisted in database
    with client.application.app_context():
        user = User.query.filter_by(email="student@test.com").first()
        assert user.theme_preference == "dark"

    # Test invalid theme rejection
    res_bad = client.post("/api/preferences/theme", json={"theme": "neon-glow"})
    assert res_bad.status_code == 400


def test_onboarding_lifecycle_api(client):
    login(client, "student@test.com", "user123")

    # Complete onboarding
    res = client.post("/api/onboarding/complete", json={})
    assert res.status_code == 200
    assert res.get_json()["ok"] is True

    with client.application.app_context():
        user = User.query.filter_by(email="student@test.com").first()
        assert user.onboarding_completed is True

    # Reset onboarding
    res_reset = client.post("/api/onboarding/reset", json={})
    assert res_reset.status_code == 200
    assert res_reset.get_json()["ok"] is True

    with client.application.app_context():
        user = User.query.filter_by(email="student@test.com").first()
        assert user.onboarding_completed is False


def test_ux_modals_and_theme_toggle_rendered_in_base(client):
    login(client, "student@test.com", "user123")
    res = client.get("/dashboard")
    assert res.status_code == 200
    html = res.data.decode("utf-8")

    # Theme toggle & theme modal
    assert "data-theme-toggle" in html
    assert 'id="themeModal"' in html
    assert 'id="ux-config"' in html

    # Shortcuts modal
    assert 'id="shortcutsModal"' in html
    assert "Phím tắt hệ thống" in html

    # Support modal & FAB
    assert 'id="supportModal"' in html
    assert 'id="supportFab"' in html
    assert "Trung tâm Hỗ trợ &amp; Trợ giúp" in html or "Trung tâm Hỗ trợ & Trợ giúp" in html


def test_public_pages_render_theme_toggle(client):
    res = client.get("/")
    assert res.status_code == 200
    html = res.data.decode("utf-8")
    assert "data-theme-toggle" in html
    assert 'id="shortcutsModal"' in html
    assert 'id="supportFab"' in html
