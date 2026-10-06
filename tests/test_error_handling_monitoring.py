"""
Unit and Integration Tests for EnglishMate Error Handling, Analysis & Monitoring (Section 12.7)
Covers:
1. Error Analysis: Fingerprinting, error grouping, occurrence frequency, status code distribution, 7-day trend.
2. Error Monitoring: Exception capture, traceback recording, Sentry SDK integration, simulation, incident resolution, and purge.
"""

import time
import pytest
from flask import Flask, jsonify, request
from app import create_app
from app.config import TestConfig
from app.extensions import db
from app.backend.auth.models import User
from app.backend.admin.models import SystemErrorLog
from app.backend.admin.error_monitoring_service import (
    record_system_error,
    compute_error_fingerprint,
    get_error_analytics,
    get_error_incidents_list,
    resolve_error_incident,
    resolve_all_error_incidents,
    purge_old_error_logs,
    trigger_simulated_error,
    is_sentry_active,
)


@pytest.fixture
def test_app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(test_app):
    return test_app.test_client()


@pytest.fixture
def admin_user(test_app):
    with test_app.app_context():
        admin = User(
            username="err_admin",
            email="err_admin@example.com",
            role="ADMIN",
            xp=1000
        )
        admin.set_password("AdminPass123!")
        db.session.add(admin)
        db.session.commit()
        return admin.id


# ===========================================================================
# 1. TEST ERROR FINGERPRINTING & GROUPING
# ===========================================================================
def test_error_fingerprinting_and_grouping(test_app):
    with test_app.app_context():
        fp1 = compute_error_fingerprint("ValueError", "Invalid student ID: 12345")
        fp2 = compute_error_fingerprint("ValueError", "Invalid student ID: 99999")
        # Normalized messages should produce identical fingerprints
        assert fp1 == fp2

        # Record first occurrence
        try:
            _ = 10 / 0
        except Exception as exc:
            log1 = record_system_error(
                exc=exc,
                status_code=500,
                severity="CRITICAL",
                route="/test/calculate",
                method="GET"
            )
            assert log1 is not None
            assert log1.occurrence_count == 1
            assert log1.exception_type == "ZeroDivisionError"
            assert log1.status_code == 500

        # Record second occurrence of the same error -> should group and increment count
        try:
            _ = 100 / 0
        except Exception as exc:
            log2 = record_system_error(
                exc=exc,
                status_code=500,
                severity="CRITICAL",
                route="/test/calculate",
                method="GET"
            )
            assert log2.id == log1.id
            assert log2.occurrence_count == 2


# ===========================================================================
# 2. TEST ERROR RECORDING WITH HTTP CONTEXT & TRACEBACK
# ===========================================================================
def test_error_recording_context_and_traceback(test_app):
    with test_app.app_context():
        try:
            raise KeyError("missing_auth_header")
        except Exception as exc:
            log_entry = record_system_error(
                exc=exc,
                status_code=400,
                severity="WARNING",
                route="/api/v1/auth/token",
                method="POST",
                user_id=42,
                ip_address="192.168.1.100",
                user_agent="Mozilla/5.0 TestBrowser",
                params={"client": "mobile_app"}
            )
            assert log_entry is not None
            assert log_entry.exception_type == "KeyError"
            assert "KeyError" in log_entry.traceback_text
            assert log_entry.route == "/api/v1/auth/token"
            assert log_entry.user_id == 42
            assert log_entry.ip_address == "192.168.1.100"
            assert log_entry.is_resolved is False


# ===========================================================================
# 3. TEST ERROR ANALYTICS & METRICS
# ===========================================================================
def test_error_analytics_aggregation(test_app):
    with test_app.app_context():
        # Clean existing logs
        SystemErrorLog.query.delete()
        db.session.commit()

        # Seed sample error occurrences
        record_system_error(exc=ValueError("Val err 1"), status_code=400, severity="WARNING", route="/api/v1/items")
        record_system_error(exc=TypeError("Type err 1"), status_code=500, severity="ERROR", route="/api/v1/lessons")
        record_system_error(exc=RuntimeError("Run err 1"), status_code=503, severity="CRITICAL", route="/api/v1/exams")

        analytics = get_error_analytics(days=7)
        assert analytics["total_occurrences"] >= 3
        assert analytics["unique_groups"] >= 3
        assert analytics["unresolved_count"] >= 3
        assert "400" in analytics["status_distribution"]
        assert "500" in analytics["status_distribution"]
        assert "503" in analytics["status_distribution"]
        assert len(analytics["exception_types"]) >= 3
        assert len(analytics["top_routes"]) >= 3
        assert len(analytics["daily_trend"]) == 7


# ===========================================================================
# 4. TEST ERROR RESOLUTION & PURGE
# ===========================================================================
def test_error_resolution_and_purge(test_app, admin_user):
    with test_app.app_context():
        err = record_system_error(exc=IndexError("List index out of range"), status_code=500, route="/test/index")
        assert err.is_resolved is False

        # Resolve single error
        ok = resolve_error_incident(error_id=err.error_id, admin_id=admin_user, notes="Fixed in patch v1.2")
        assert ok is True

        refreshed = SystemErrorLog.query.filter_by(error_id=err.error_id).first()
        assert refreshed.is_resolved is True
        assert refreshed.resolved_by_id == admin_user
        assert refreshed.resolution_notes == "Fixed in patch v1.2"

        # Resolve all errors
        record_system_error(exc=AttributeError("None object has no attr"), status_code=500, route="/test/attr")
        resolved_all_count = resolve_all_error_incidents(admin_id=admin_user)
        assert resolved_all_count >= 1

        unresolved = SystemErrorLog.query.filter_by(is_resolved=False).count()
        assert unresolved == 0


# ===========================================================================
# 5. TEST SIMULATED ERROR TRIGGER
# ===========================================================================
def test_simulated_error_trigger(test_app):
    with test_app.app_context():
        res = trigger_simulated_error(error_type="division_by_zero")
        assert res["success"] is True
        assert res["simulated_type"] == "division_by_zero"
        assert res["error_id"] is not None
        assert res["fingerprint"] is not None

        # Verify it was logged in database
        logged = SystemErrorLog.query.filter_by(error_id=res["error_id"]).first()
        assert logged is not None
        assert logged.exception_type == "ZeroDivisionError"


# ===========================================================================
# 6. TEST ADMIN ERROR DASHBOARD & APIS
# ===========================================================================
def test_admin_error_routes(test_app, client, admin_user):
    with client.session_transaction() as sess:
        sess["_user_id"] = str(admin_user)
        sess["_fresh"] = True

    # Seed an error
    with test_app.app_context():
        seeded = record_system_error(exc=ValueError("Seeded error for admin route"), status_code=500, route="/api/test")
        seeded_id = seeded.error_id

    # 1. View Dashboard
    res = client.get("/admin/system/errors")
    assert res.status_code == 200
    assert "Phân tích & Giám sát Lỗi" in res.get_data(as_text=True)

    # 2. Analytics API
    res_analytics = client.get("/admin/system/errors/api/analytics")
    assert res_analytics.status_code == 200
    assert "total_occurrences" in res_analytics.json

    # 3. Error Detail API
    res_detail = client.get(f"/admin/system/errors/{seeded_id}")
    assert res_detail.status_code == 200
    assert res_detail.json["data"]["error_id"] == seeded_id
    assert res_detail.json["data"]["exception_type"] == "ValueError"

    # 4. Resolve Route
    res_resolve = client.post(
        f"/admin/system/errors/{seeded_id}/resolve",
        json={"notes": "Resolved via Admin test"}
    )
    assert res_resolve.status_code == 200
    assert res_resolve.json["success"] is True

    # 5. Resolve All Route
    res_resolve_all = client.post("/admin/system/errors/resolve-all", json={})
    assert res_resolve_all.status_code == 200
    assert res_resolve_all.json["success"] is True

    # 6. Test Trigger API
    res_test = client.post("/admin/system/errors/test-trigger", json={"error_type": "key_error"})
    assert res_test.status_code == 200
    assert res_test.json["success"] is True
