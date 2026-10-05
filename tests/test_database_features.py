import json
import pytest
from tests.conftest import login
from app.extensions import db
from app.backend.admin.models import DatabaseBackup, SystemConfig
from app.backend.admin.database_service import (
    get_migration_status,
    is_migration_initialized,
    run_database_upgrade,
    get_backup_automation_status,
    check_and_run_auto_backup,
    auto_restore_database,
)
from app.backend.admin.backup_service import create_database_backup


def test_migration_system_status(app):
    """Kiểm tra hệ thống Migration System (Flask-Migrate / Alembic) đã được khởi tạo và nhận diện schema."""
    with app.app_context():
        assert is_migration_initialized() is True
        status = get_migration_status()
        assert status["is_initialized"] is True
        assert status["total_versions"] >= 1
        assert "versions" in status
        assert len(status["versions"]) >= 1
        assert status["head_revision"] is not None


def test_migration_system_upgrade_execution(app):
    """Kiểm tra việc thực thi nâng cấp CSDL lên revision chỉ định qua migration system."""
    with app.app_context():
        status_before = get_migration_status()
        head_rev = status_before.get("head_revision")
        if head_rev:
            res = run_database_upgrade(revision=head_rev)
            assert res["success"] is True
            assert "Nâng cấp CSDL thành công" in res["message"]


def test_backup_automation_status_and_execution(app):
    """Kiểm tra tính năng tự động sao lưu CSDL định kỳ (Backup Automation)."""
    with app.app_context():
        # 1. Check automation status
        auto_status = get_backup_automation_status()
        assert "auto_enabled" in auto_status
        assert "frequency" in auto_status
        assert "next_run_at" in auto_status

        # 2. Trigger auto-backup (force=True)
        res = check_and_run_auto_backup(force=True)
        assert res["success"] is True
        assert "backup" in res
        assert "cleanup_deleted_count" in res
        assert res["backup"]["success"] is True

        # Verify DatabaseBackup record created
        latest_backup = DatabaseBackup.query.order_by(DatabaseBackup.created_at.desc()).first()
        assert latest_backup is not None
        assert latest_backup.status == "SUCCESS"

        # 3. Subsequent check without force should be skipped (too recent)
        res_skip = check_and_run_auto_backup(force=False)
        assert res_skip.get("skipped") is True


def test_restore_automation_safety_flow(app):
    """Kiểm tra kịch bản tự động khôi phục CSDL an toàn (Restore Automation)."""
    with app.app_context():
        # Create a baseline backup first
        b_res = create_database_backup(backup_type="MANUAL", notes="Restore automation test baseline")
        assert b_res["success"] is True
        backup_id = b_res["backup_id"]

        # Run auto-restore
        restore_res = auto_restore_database(backup_id=backup_id)
        assert restore_res["success"] is True
        assert "safety_backup" in restore_res
        assert "Khôi phục CSDL thành công" in restore_res["message"]

        # Auto-restore using use_latest=True
        latest_res = auto_restore_database(use_latest=True)
        assert latest_res["success"] is True


def test_admin_database_features_api_endpoints(client, app):
    """Kiểm tra các endpoint REST quản lý Database Migrations, Auto-Backup và Auto-Restore trên giao diện Admin."""
    # 1. Student unauthorized check
    login(client, "student@test.com", "user123")
    res_unauth = client.get("/admin/system/database/status")
    assert res_unauth.status_code == 403

    # Logout student
    client.get("/auth/logout", follow_redirects=True)

    # 2. Admin authorized check
    login_res = login(client, "admin@test.com", "admin123")
    assert login_res.status_code == 200

    # Status API
    res_status = client.get("/admin/system/database/status")
    assert res_status.status_code == 200
    data = res_status.get_json()
    assert data["success"] is True
    assert "migrations" in data
    assert "auto_backup" in data

    # Trigger Auto-Backup API
    res_backup = client.post("/admin/system/database/auto-backup", json={"force": True})
    assert res_backup.status_code == 200
    assert res_backup.get_json()["success"] is True

    # Trigger Auto-Restore API
    res_restore = client.post("/admin/system/database/auto-restore", json={"use_latest": True})
    assert res_restore.status_code == 200
    assert res_restore.get_json()["success"] is True
