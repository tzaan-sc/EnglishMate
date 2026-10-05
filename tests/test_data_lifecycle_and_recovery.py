from datetime import datetime, timezone, timedelta
from tests.conftest import login
from app.extensions import db
from app.backend.auth.models import User
from app.backend.admin.models import DatabaseBackup
from app.backend.admin.backup_service import (
    create_database_backup,
    restore_database_backup,
    delete_backup,
    cleanup_old_backups,
    get_backup_stats,
)
from app.backend.admin.data_lifecycle_service import (
    get_inactive_users_stats,
    purge_soft_deleted_users,
    run_data_lifecycle_maintenance_job,
)


def test_database_backup_and_recovery_flow(app):
    """Kiểm tra quy trình tạo bản sao lưu và khôi phục CSDL an toàn (Data Recovery)."""
    with app.app_context():
        # 1. Tạo bản sao lưu ban đầu
        res_backup = create_database_backup(backup_type="MANUAL", notes="Test Initial Backup")
        assert res_backup["success"] is True
        backup_id = res_backup["backup_id"]

        # 2. Thêm một user thử nghiệm
        temp_user = User(username="temp_user_to_restore", email="temp_restore@test.com")
        temp_user.set_password("pass123")
        db.session.add(temp_user)
        db.session.commit()
        assert User.query.filter_by(username="temp_user_to_restore").first() is not None

        # 3. Khôi phục CSDL từ bản sao lưu ban đầu
        res_restore = restore_database_backup(backup_id=backup_id)
        assert res_restore["success"] is True
        assert res_restore.get("safety_backup") is not None

        # 4. Dọn dẹp bản sao lưu test
        delete_backup(backup_id)


def test_inactive_users_retention_stats(app):
    """Kiểm tra thống kê tài khoản không hoạt động theo chính sách Data Retention."""
    with app.app_context():
        stats = get_inactive_users_stats(days=180)
        assert stats is not None
        assert "inactive_users_count" in stats
        assert "soft_deleted_users" in stats
        assert "total_regular_users" in stats
        assert stats["retention_days"] == 180


def test_purge_soft_deleted_users(app):
    """Kiểm tra dọn dẹp vĩnh viễn (Hard Purge) tài khoản soft-delete đã quá hạn."""
    with app.app_context():
        # Tạo tài khoản soft-delete quá hạn 200 ngày
        old_date = datetime.now(timezone.utc) - timedelta(days=200)
        soft_deleted_user = User(
            username="old_deleted_user",
            email="old_deleted@test.com",
            is_active=False,
            role="USER"
        )
        soft_deleted_user.set_password("pass123")
        db.session.add(soft_deleted_user)
        db.session.commit()

        # Update timestamps to be older than 180 days
        soft_deleted_user.updated_at = old_date
        db.session.commit()

        # 1. Dry run
        dry_res = purge_soft_deleted_users(days=180, dry_run=True)
        assert dry_res["success"] is True
        assert dry_res["dry_run"] is True
        assert dry_res["matching_count"] >= 1
        assert User.query.filter_by(username="old_deleted_user").first() is not None

        # 2. Live purge
        live_res = purge_soft_deleted_users(days=180, dry_run=False)
        assert live_res["success"] is True
        assert live_res["purged_count"] >= 1
        assert User.query.filter_by(username="old_deleted_user").first() is None


def test_data_lifecycle_maintenance_job(app):
    """Kiểm tra job tổng thể bảo trì vòng đời dữ liệu (Data Lifecycle Maintenance)."""
    with app.app_context():
        res = run_data_lifecycle_maintenance_job()
        assert res["success"] is True
        assert "details" in res
        assert "audit_logs_cleanup" in res["details"]
        assert "purged_users" in res["details"]


def test_data_lifecycle_and_restore_api_endpoints(client, app):
    """Kiểm tra các REST API endpoints quản trị Data Lifecycle và Khôi phục CSDL."""
    # 1. Non-admin forbidden
    login(client, "student@test.com", "user123")
    res_stats_forbidden = client.get("/admin/system/data-lifecycle/stats")
    assert res_stats_forbidden.status_code == 403

    res_purge_forbidden = client.post("/admin/system/data-lifecycle/purge", json={"days": 180})
    assert res_purge_forbidden.status_code == 403

    client.post("/auth/logout")

    # 2. Admin authorized
    login(client, "admin@test.com", "admin123")

    # Stats API
    res_stats = client.get("/admin/system/data-lifecycle/stats")
    assert res_stats.status_code == 200
    stats_data = res_stats.get_json()
    assert stats_data["success"] is True
    assert "stats" in stats_data

    # Dry-run Purge API
    res_purge = client.post("/admin/system/data-lifecycle/purge", json={"days": 180, "dry_run": True})
    assert res_purge.status_code == 200
    purge_data = res_purge.get_json()
    assert purge_data["success"] is True
    assert purge_data["dry_run"] is True

    # Maintenance API
    res_maint = client.post("/admin/system/data-lifecycle/maintenance")
    assert res_maint.status_code == 200
    maint_data = res_maint.get_json()
    assert maint_data["success"] is True
