import os
import tempfile
from datetime import datetime, timezone, timedelta
import pytest
from app.extensions import db
from app.backend.admin.models import AuditLog, SystemSetting
from app.backend.admin.log_service import (
    get_log_retention_days,
    set_log_retention_days,
    get_retention_stats,
    cleanup_audit_logs,
    export_logs_to_file
)
from tests.conftest import login


def test_log_retention_service_default_and_set(app):
    with app.app_context():
        # Default should be 90
        SystemSetting.query.filter_by(key="LOG_RETENTION_DAYS").delete()
        db.session.commit()
        assert get_log_retention_days() == 90

        # Update retention days
        days = set_log_retention_days(180)
        assert days == 180
        assert get_log_retention_days() == 180

        # Invalid values should raise ValueError
        with pytest.raises(ValueError):
            set_log_retention_days(0)
        with pytest.raises(ValueError):
            set_log_retention_days(-5)
        with pytest.raises(ValueError):
            set_log_retention_days("invalid")


def test_cleanup_audit_logs_and_dry_run(app):
    with app.app_context():
        # Clear existing logs
        AuditLog.query.delete()
        db.session.commit()

        now_utc = datetime.now(timezone.utc)

        # Create old logs (100 days old, 150 days old) and fresh logs (5 days old)
        old_log_1 = AuditLog(action="OLD_ACTION_1", details="100 days old", created_at=now_utc - timedelta(days=100))
        old_log_2 = AuditLog(action="OLD_ACTION_2", details="150 days old", created_at=now_utc - timedelta(days=150))
        recent_log = AuditLog(action="RECENT_ACTION", details="5 days old", created_at=now_utc - timedelta(days=5))

        db.session.add_all([old_log_1, old_log_2, recent_log])
        db.session.commit()

        # Check retention stats
        stats = get_retention_stats(custom_days=90)
        assert stats["total_logs"] == 3
        assert stats["eligible_logs"] == 2

        # Test DRY-RUN with 90 days retention
        dry_res = cleanup_audit_logs(days=90, dry_run=True)
        assert dry_res["success"] is True
        assert dry_res["dry_run"] is True
        assert dry_res["matching_count"] == 2
        assert AuditLog.query.count() == 3  # nothing actually deleted

        # Test REAL PURGE with temporary archive CSV
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            purge_res = cleanup_audit_logs(days=90, archive_path=tmp_path, dry_run=False)
            assert purge_res["success"] is True
            assert purge_res["dry_run"] is False
            assert purge_res["deleted_count"] == 2

            # Only recent_log should remain
            remaining = AuditLog.query.all()
            assert len(remaining) == 1
            assert remaining[0].action == "RECENT_ACTION"

            # Check archive file content
            assert os.path.exists(tmp_path)
            with open(tmp_path, "r", encoding="utf-8-sig") as f:
                content = f.read()
                assert "OLD_ACTION_1" in content
                assert "OLD_ACTION_2" in content
                assert "RECENT_ACTION" not in content
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


def test_admin_retention_api_and_routes(client, app):
    login(client, email="admin@test.com", password="admin123")

    # 1. Test GET /admin/audit-logs/retention-info
    res_info = client.get("/admin/audit-logs/retention-info?days=60")
    assert res_info.status_code == 200
    json_info = res_info.get_json()
    assert json_info["success"] is True
    assert "stats" in json_info
    assert json_info["stats"]["retention_days"] == 60

    # 2. Test POST /admin/audit-logs/settings
    res_setting = client.post(
        "/admin/audit-logs/settings",
        json={"retention_days": 120}
    )
    assert res_setting.status_code == 200
    json_setting = res_setting.get_json()
    assert json_setting["success"] is True
    assert json_setting["days"] == 120

    with app.app_context():
        assert get_log_retention_days() == 120

    # Test invalid setting
    res_invalid = client.post(
        "/admin/audit-logs/settings",
        json={"retention_days": -10}
    )
    assert res_invalid.status_code == 400

    # 3. Test GET /admin/audit-logs page renders banner and modal
    res_page = client.get("/admin/audit-logs")
    assert res_page.status_code == 200
    assert "Chính sách lưu trữ log:".encode("utf-8") in res_page.data
    assert "retentionModal".encode("utf-8") in res_page.data
    assert "120 ngày".encode("utf-8") in res_page.data

    # 4. Test POST /admin/audit-logs/cleanup
    with app.app_context():
        # Seed an old log
        old_log = AuditLog(
            action="TEMP_PURGE_TEST",
            details="To be purged",
            created_at=datetime.now(timezone.utc) - timedelta(days=200)
        )
        db.session.add(old_log)
        db.session.commit()

    res_cleanup_dry = client.post(
        "/admin/audit-logs/cleanup",
        json={"days": 120, "dry_run": True}
    )
    assert res_cleanup_dry.status_code == 200
    assert res_cleanup_dry.get_json()["dry_run"] is True

    res_cleanup_real = client.post(
        "/admin/audit-logs/cleanup",
        json={"days": 120, "dry_run": False}
    )
    assert res_cleanup_real.status_code == 200
    json_real = res_cleanup_real.get_json()
    assert json_real["success"] is True
    assert json_real["deleted_count"] >= 1


def test_flask_cli_cleanup_logs(app):
    runner = app.test_cli_runner()

    with app.app_context():
        now_utc = datetime.now(timezone.utc)
        log1 = AuditLog(action="CLI_OLD_1", details="old", created_at=now_utc - timedelta(days=100))
        log2 = AuditLog(action="CLI_NEW_1", details="new", created_at=now_utc - timedelta(days=2))
        db.session.add_all([log1, log2])
        db.session.commit()

    # Run CLI dry-run
    result_dry = runner.invoke(args=["cleanup-logs", "--days", "60", "--dry-run"])
    assert result_dry.exit_code == 0
    assert "[DRY RUN]" in result_dry.output

    # Run CLI real purge
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
        tmp_archive = tmp.name

    try:
        result_purge = runner.invoke(args=["cleanup-logs", "--days", "60", "--archive-path", tmp_archive])
        assert result_purge.exit_code == 0
        assert "[SUCCESS]" in result_purge.output
        assert "Archive saved to:" in result_purge.output
    finally:
        if os.path.exists(tmp_archive):
            os.remove(tmp_archive)
