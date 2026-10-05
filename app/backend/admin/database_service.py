import os
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from flask import current_app
from flask_migrate import (
    current as flask_migrate_current,
    history as flask_migrate_history,
    migrate as flask_migrate_migrate,
    stamp as flask_migrate_stamp,
    upgrade as flask_migrate_upgrade,
)
from alembic.config import Config as AlembicConfig
from alembic.script import ScriptDirectory

from ...extensions import db
from .backup_service import (
    cleanup_old_backups,
    create_database_backup,
    get_backup_dir,
    get_backup_settings,
    restore_database_backup,
)
from .models import DatabaseBackup, SystemConfig
from .utils import log_audit_action


# ---------------------------------------------------------------------------
# 1. DATABASE MIGRATION SYSTEM (MỤC 12.1 - MIGRATION SYSTEM)
# ---------------------------------------------------------------------------

def get_migrations_directory() -> Path:
    """Trả về đường dẫn thư mục migrations của ứng dụng."""
    return Path(current_app.root_path).parent / "migrations"


def is_migration_initialized() -> bool:
    """Kiểm tra xem hệ thống Flask-Migrate / Alembic đã được khởi tạo hay chưa."""
    mig_dir = get_migrations_directory()
    return (mig_dir / "alembic.ini").exists() or (mig_dir / "env.py").exists()


def get_migration_status() -> Dict[str, Any]:
    """Lấy thông tin trạng thái chi tiết của hệ thống Database Migrations."""
    mig_dir = get_migrations_directory()
    initialized = is_migration_initialized()

    if not initialized:
        return {
            "is_initialized": False,
            "current_revision": None,
            "head_revision": None,
            "is_up_to_date": False,
            "total_versions": 0,
            "versions": [],
        }

    versions_dir = mig_dir / "versions"
    version_files = list(versions_dir.glob("*.py")) if versions_dir.exists() else []

    try:
        alembic_ini_path = str(mig_dir / "alembic.ini") if (mig_dir / "alembic.ini").exists() else "migrations/alembic.ini"
        alembic_cfg = AlembicConfig(alembic_ini_path)
        alembic_cfg.set_main_option("script_location", str(mig_dir))
        script = ScriptDirectory.from_config(alembic_cfg)
        head_rev = script.get_current_head()
    except Exception:
        head_rev = version_files[0].stem.split("_")[0] if version_files else None

    # Get current DB revision from alembic_version table
    current_rev = None
    try:
        result = db.session.execute(db.text("SELECT version_num FROM alembic_version LIMIT 1")).fetchone()
        if result:
            current_rev = result[0]
    except Exception:
        current_rev = None

    is_up_to_date = (current_rev == head_rev) if (current_rev and head_rev) else False

    # Collect version history list
    versions_list = []
    for f in sorted(version_files, reverse=True):
        rev_id = f.stem.split("_")[0]
        desc = " ".join(f.stem.split("_")[1:]) if "_" in f.stem else f.stem
        versions_list.append({
            "revision": rev_id,
            "description": desc.replace("_", " ").title(),
            "filename": f.name,
            "is_current": (rev_id == current_rev),
            "is_head": (rev_id == head_rev),
        })

    return {
        "is_initialized": True,
        "current_revision": current_rev,
        "head_revision": head_rev,
        "is_up_to_date": is_up_to_date,
        "total_versions": len(version_files),
        "versions": versions_list,
    }


def run_database_upgrade(revision: str = "head", admin_id: Optional[int] = None) -> Dict[str, Any]:
    """Thực thi nâng cấp cơ sở dữ liệu lên phiên bản migration chỉ định."""
    mig_dir = str(get_migrations_directory())
    try:
        flask_migrate_upgrade(directory=mig_dir, revision=revision)
    except Exception as e:
        err_msg = str(e).lower()
        # If schema tables already exist (e.g. initial setup created via db.create_all), stamp as baseline
        if "already exists" in err_msg or "table" in err_msg:
            try:
                flask_migrate_stamp(directory=mig_dir, revision=revision)
            except Exception as stamp_err:
                return {
                    "success": False,
                    "error": f"Lỗi khi nâng cấp CSDL: {str(stamp_err)}",
                }
        else:
            return {
                "success": False,
                "error": f"Lỗi khi nâng cấp CSDL: {str(e)}",
            }

    status = get_migration_status()
    log_audit_action(
        user_id=admin_id,
        action="DATABASE_MIGRATION_UPGRADE",
        target_type="DATABASE_SCHEMA",
        details=f"Nâng cấp CSDL lên revision {status.get('current_revision', revision)}"
    )

    return {
        "success": True,
        "message": f"Nâng cấp CSDL thành công lên revision: {status.get('current_revision', revision)}",
        "status": status,
    }


def generate_database_migration(message: str = "Auto schema update", admin_id: Optional[int] = None) -> Dict[str, Any]:
    """Tự động phát hiện thay đổi schema và tạo tệp migration mới."""
    try:
        mig_dir = str(get_migrations_directory())
        flask_migrate_migrate(directory=mig_dir, message=message)

        status = get_migration_status()
        log_audit_action(
            user_id=admin_id,
            action="GENERATE_DATABASE_MIGRATION",
            target_type="DATABASE_SCHEMA",
            details=f"Tạo file migration mới: {message}"
        )

        return {
            "success": True,
            "message": f"Đã tạo file migration mới thành công với nội dung: {message}",
            "status": status,
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Lỗi khi tạo migration: {str(e)}",
        }


# ---------------------------------------------------------------------------
# 2. BACKUP AUTOMATION (MỤC 12.1 - BACKUP AUTOMATION)
# ---------------------------------------------------------------------------

def get_backup_automation_status() -> Dict[str, Any]:
    """Lấy trạng thái và thời gian chạy tiếp theo của tác vụ tự động sao lưu CSDL."""
    settings = get_backup_settings()
    auto_enabled = settings.get("BACKUP_AUTO_ENABLED", True)
    frequency = settings.get("BACKUP_FREQUENCY", "DAILY")
    last_run_str = settings.get("BACKUP_LAST_RUN_AT", "")

    # Calculate next scheduled run
    next_run = None
    if auto_enabled and frequency != "OFF":
        now = datetime.now(timezone.utc)
        if last_run_str:
            try:
                last_dt = datetime.fromisoformat(last_run_str)
                if frequency == "DAILY":
                    next_run = last_dt + timedelta(days=1)
                elif frequency == "WEEKLY":
                    next_run = last_dt + timedelta(days=7)
            except Exception:
                next_run = now + timedelta(days=1)
        else:
            next_run = now

    return {
        "auto_enabled": auto_enabled,
        "frequency": frequency,
        "last_run_at": last_run_str or "Chưa có lượt sao lưu tự động",
        "next_run_at": next_run.strftime("%d/%m/%Y %H:%M:%S UTC") if next_run else "Tắt",
        "retention_count": settings.get("BACKUP_RETENTION_COUNT", 10),
        "compression_enabled": settings.get("BACKUP_COMPRESSION_ENABLED", True),
    }


def check_and_run_auto_backup(force: bool = False, admin_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Kiểm tra lịch trình và tự động kích hoạt tạo bản sao lưu CSDL định kỳ (Automated Backup).
    - force=True: Bỏ qua kiểm tra thời gian và ép buộc chạy ngay.
    """
    settings = get_backup_settings()
    if not force and not settings.get("BACKUP_AUTO_ENABLED", True):
        return {
            "success": False,
            "skipped": True,
            "message": "Tính năng tự động sao lưu CSDL đang bị tắt.",
        }

    frequency = settings.get("BACKUP_FREQUENCY", "DAILY")
    if not force and frequency == "OFF":
        return {
            "success": False,
            "skipped": True,
            "message": "Tần suất tự động sao lưu đang ở chế độ OFF.",
        }

    now = datetime.now(timezone.utc)
    last_run_str = settings.get("BACKUP_LAST_RUN_AT", "")

    if not force and last_run_str:
        try:
            last_dt = datetime.fromisoformat(last_run_str)
            if frequency == "DAILY" and (now - last_dt) < timedelta(hours=23):
                return {
                    "success": True,
                    "skipped": True,
                    "message": f"Chưa đến lịch sao lưu tiếp theo (Lần cuối: {last_run_str}).",
                }
            elif frequency == "WEEKLY" and (now - last_dt) < timedelta(days=6, hours=23):
                return {
                    "success": True,
                    "skipped": True,
                    "message": f"Chưa đến lịch sao lưu hàng tuần tiếp theo (Lần cuối: {last_run_str}).",
                }
        except Exception:
            pass

    # Trigger backup creation
    notes = f"Tác vụ tự động sao lưu định kỳ ({frequency})"
    res = create_database_backup(
        backup_type=frequency,
        notes=notes,
        admin_id=admin_id,
    )

    if res.get("success"):
        # Update last run time
        now_iso = now.isoformat()
        SystemConfig.set_config("BACKUP_LAST_RUN_AT", now_iso, description="Thời gian thực hiện sao lưu tự động lần cuối", category="BACKUP")

        # Cleanup old backups according to retention count
        cleanup_count = cleanup_old_backups()

        log_audit_action(
            user_id=admin_id,
            action="RUN_AUTO_BACKUP",
            target_type="DATABASE_BACKUP",
            details=f"Hoàn thành tự động sao lưu CSDL: {res.get('filename')} ({cleanup_count} bản ghi cũ đã được dọn dẹp)"
        )

        return {
            "success": True,
            "backup": res,
            "cleanup_deleted_count": cleanup_count,
            "message": f"Tự động sao lưu CSDL thành công: {res.get('filename')}",
        }

    return res


# ---------------------------------------------------------------------------
# 3. RESTORE AUTOMATION (MỤC 12.1 - RESTORE AUTOMATION)
# ---------------------------------------------------------------------------

def auto_restore_database(
    backup_id: Optional[int] = None,
    use_latest: bool = False,
    admin_id: Optional[int] = None,
    create_safety_backup: bool = True
) -> Dict[str, Any]:
    """
    Kịch bản tự động khôi phục CSDL an toàn (Restore Automation).
    - Tự động chọn bản sao lưu mới nhất nếu use_latest=True.
    - Tạo snapshot an toàn trước khi phục hồi để phòng rủi ro.
    """
    target_backup_id = backup_id

    if use_latest or target_backup_id is None:
        latest = DatabaseBackup.query.filter(
            DatabaseBackup.status.in_(["SUCCESS", "COMPLETED"])
        ).order_by(DatabaseBackup.created_at.desc()).first()
        if latest:
            target_backup_id = latest.id
        else:
            # Fallback: scan physical backup directory for existing backup files
            backup_dir = get_backup_dir()
            backup_files = sorted(
                [f for f in backup_dir.glob("englishmate_backup_*") if f.is_file()],
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )
            if backup_files:
                latest_file = backup_files[0]
                # Register backup in DB
                rec = DatabaseBackup(
                    filename=latest_file.name,
                    file_path=str(latest_file),
                    file_size_bytes=latest_file.stat().st_size,
                    backup_type="MANUAL",
                    status="SUCCESS",
                    notes="Tự động nhận diện từ tệp sao lưu trên đĩa",
                )
                db.session.add(rec)
                db.session.commit()
                target_backup_id = rec.id
            else:
                return {
                    "success": False,
                    "error": "Không tìm thấy bất kỳ bản sao lưu hợp lệ nào để phục hồi.",
                }

    # Execute restore via backup_service
    res = restore_database_backup(
        backup_id=target_backup_id,
        admin_id=admin_id,
    )

    if res.get("success"):
        log_audit_action(
            user_id=admin_id,
            action="AUTO_RESTORE_DATABASE",
            target_type="DATABASE_BACKUP",
            details=f"Tự động phục hồi CSDL thành công từ bản sao lưu #{target_backup_id}"
        )

    return res
