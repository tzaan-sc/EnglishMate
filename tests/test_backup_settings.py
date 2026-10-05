import os
import gzip
from pathlib import Path
from tests.conftest import login
from app.backend.admin.models import DatabaseBackup, SystemConfig
from app.backend.admin.backup_service import (
    create_database_backup,
    get_backup_settings,
    save_backup_settings,
    cleanup_old_backups,
    delete_backup,
    get_backup_dir
)


def test_backup_page_access_forbidden_for_learners(client):
    """Học viên bình thường không được phép truy cập trang sao lưu CSDL."""
    login(client, "student@test.com", "user123")
    res = client.get("/admin/system/backup")
    assert res.status_code == 403


def test_admin_can_access_backup_page(client):
    """Admin có quyền truy cập trang quản trị sao lưu CSDL."""
    login(client, "admin@test.com", "admin123")
    res = client.get("/admin/system/backup")
    assert res.status_code == 200
    assert "Cài đặt Sao lưu CSDL".encode("utf-8") in res.data
    assert "Tạo bản sao lưu ngay".encode("utf-8") in res.data


def test_create_manual_backup_and_download(client, app):
    """Admin tạo bản sao lưu thủ công qua POST và tải file về máy."""
    login(client, "admin@test.com", "admin123")

    # 1. Trigger backup creation
    res = client.post("/admin/system/backup/create", data={
        "backup_type": "MANUAL",
        "notes": "Test manual backup notes"
    }, follow_redirects=True)
    assert res.status_code == 200

    with app.app_context():
        backup = DatabaseBackup.query.order_by(DatabaseBackup.id.desc()).first()
        assert backup is not None
        assert backup.backup_type == "MANUAL"
        assert backup.status == "SUCCESS"
        assert backup.is_compressed is True
        assert os.path.exists(backup.file_path)
        backup_id = backup.id
        backup_filename = backup.filename

    # 2. Download backup file
    res_down = client.get(f"/admin/system/backup/download/{backup_id}")
    assert res_down.status_code == 200
    assert backup_filename in res_down.headers.get("Content-Disposition", "")


def test_create_backup_json_api(client, app):
    """Tạo bản sao lưu qua JSON API."""
    login(client, "admin@test.com", "admin123")

    res = client.post("/admin/system/backup/create", json={
        "backup_type": "DAILY",
        "notes": "Automated JSON backup"
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert "backup_id" in data


def test_update_backup_settings_via_api(client, app):
    """Cập nhật cấu hình tự động sao lưu CSDL."""
    login(client, "admin@test.com", "admin123")

    new_settings = {
        "BACKUP_AUTO_ENABLED": True,
        "BACKUP_FREQUENCY": "WEEKLY",
        "BACKUP_RETENTION_COUNT": 5,
        "BACKUP_COMPRESSION_ENABLED": True
    }

    res = client.post("/admin/system/backup/settings", json=new_settings)
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert data["settings"]["BACKUP_FREQUENCY"] == "WEEKLY"
    assert data["settings"]["BACKUP_RETENTION_COUNT"] == 5

    with app.app_context():
        assert SystemConfig.get_config("BACKUP_FREQUENCY") == "WEEKLY"
        assert SystemConfig.get_int_config("BACKUP_RETENTION_COUNT") == 5


def test_delete_backup_route(client, app):
    """Xóa một bản sao lưu CSDL."""
    login(client, "admin@test.com", "admin123")

    with app.app_context():
        res = create_database_backup(backup_type="MANUAL", notes="To be deleted")
        backup_id = res["backup_id"]

    res_del = client.post(f"/admin/system/backup/delete/{backup_id}", json={})
    assert res_del.status_code == 200
    assert res_del.get_json()["success"] is True

    with app.app_context():
        from app.extensions import db
        assert db.session.get(DatabaseBackup, backup_id) is None


def test_backup_cleanup_old_records(app):
    """Tự động dọn dẹp các bản sao lưu vượt quá retention count."""
    with app.app_context():
        # Set retention to 2
        save_backup_settings({"BACKUP_RETENTION_COUNT": 2})

        # Create 4 backups
        b1 = create_database_backup(backup_type="DAILY", notes="B1")
        b2 = create_database_backup(backup_type="DAILY", notes="B2")
        b3 = create_database_backup(backup_type="DAILY", notes="B3")
        b4 = create_database_backup(backup_type="DAILY", notes="B4")

        # Cleanup keeping only 2
        deleted = cleanup_old_backups(retention_count=2)
        remaining = DatabaseBackup.query.count()
        assert remaining <= 2


def test_backup_db_cli(app):
    """Kiểm tra lệnh CLI `flask backup-db`."""
    runner = app.test_cli_runner()
    result = runner.invoke(args=["backup-db", "--type=DAILY", "--notes=CLI test backup"])
    assert result.exit_code == 0
    assert "[SUCCESS]" in result.output
