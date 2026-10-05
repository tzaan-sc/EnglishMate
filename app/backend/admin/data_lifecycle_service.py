from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

from flask import current_app
from sqlalchemy import text

from ...extensions import db
from ..auth.models import User
from .models import AuditLog, SystemConfig, SystemSetting
from .utils import log_audit_action

DEFAULT_INACTIVE_USER_DAYS = 365
DEFAULT_PURGE_SOFT_DELETE_DAYS = 180


def get_inactive_users_stats(days: Optional[int] = None) -> Dict[str, Any]:
    """
    Thống kê số lượng người dùng không hoạt động (Inactive Users) theo số ngày chỉ định.
    Người dùng không hoạt động là:
    - Chưa từng đăng nhập hoặc có `last_login_at` cũ hơn `cutoff_date`
    - Hoặc `last_activity_date` cũ hơn `cutoff_date`
    - Và không phải tài khoản Quản trị viên (ADMIN)
    """
    retention_days = days if (days is not None and days > 0) else SystemConfig.get_int_config("INACTIVE_USER_RETENTION_DAYS", default=DEFAULT_INACTIVE_USER_DAYS)
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)
    cutoff_date_only = cutoff_date.date()

    total_users = User.query.filter_by(role="USER").count()
    soft_deleted_users = User.query.filter_by(is_active=False).count()

    # Query inactive accounts
    inactive_query = User.query.filter(
        User.role == "USER",
        User.created_at < cutoff_date,
        (User.last_login_at == None) | (User.last_login_at < cutoff_date),
        (User.last_activity_date == None) | (User.last_activity_date < cutoff_date_only)
    )
    inactive_count = inactive_query.count()

    # Query soft-deleted users eligible for purging (> 180 days)
    purge_cutoff = datetime.now(timezone.utc) - timedelta(days=DEFAULT_PURGE_SOFT_DELETE_DAYS)
    purge_eligible_query = User.query.filter(
        User.is_active == False,
        User.updated_at < purge_cutoff
    )
    purge_eligible_count = purge_eligible_query.count()

    return {
        "retention_days": retention_days,
        "cutoff_date": cutoff_date.isoformat(),
        "total_regular_users": total_users,
        "soft_deleted_users": soft_deleted_users,
        "inactive_users_count": inactive_count,
        "purge_eligible_count": purge_eligible_count,
        "purge_cutoff_days": DEFAULT_PURGE_SOFT_DELETE_DAYS,
        "purge_cutoff_date": purge_cutoff.isoformat(),
    }


def purge_soft_deleted_users(
    days: Optional[int] = None,
    dry_run: bool = False,
    admin_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Dọn dẹp vĩnh viễn (Hard Purge) các tài khoản đã bị khóa/soft-delete (`is_active=False`)
    quá thời hạn quy định (mặc định 180 ngày).
    """
    purge_days = days if (days is not None and days > 0) else SystemConfig.get_int_config("PURGE_SOFT_DELETE_DAYS", default=DEFAULT_PURGE_SOFT_DELETE_DAYS)
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=purge_days)

    query = User.query.filter(
        User.is_active == False,
        User.role == "USER",
        User.updated_at < cutoff_date
    )
    count = query.count()

    if count == 0:
        return {
            "success": True,
            "purged_count": 0,
            "dry_run": dry_run,
            "days": purge_days,
            "cutoff_date": cutoff_date.isoformat(),
            "message": f"Không có tài khoản soft-delete nào quá hạn {purge_days} ngày."
        }

    if dry_run:
        sample_users = [{"id": u.id, "username": u.username, "email": u.email} for u in query.limit(10).all()]
        return {
            "success": True,
            "dry_run": True,
            "matching_count": count,
            "purged_count": 0,
            "days": purge_days,
            "cutoff_date": cutoff_date.isoformat(),
            "sample_users": sample_users,
            "message": f"[DRY-RUN] Tìm thấy {count} tài khoản soft-deleted quá hạn {purge_days} ngày cần dọn dẹp."
        }

    # Delete records
    deleted_count = 0
    users_to_delete = query.all()
    for u in users_to_delete:
        db.session.delete(u)
        deleted_count += 1
    db.session.commit()

    log_audit_action(
        user_id=admin_id,
        action="PURGE_SOFT_DELETED_USERS",
        target_type="USER",
        details=f"Dọn dẹp vĩnh viễn {deleted_count} tài khoản soft-deleted quá hạn {purge_days} ngày"
    )

    return {
        "success": True,
        "dry_run": False,
        "purged_count": deleted_count,
        "days": purge_days,
        "cutoff_date": cutoff_date.isoformat(),
        "message": f"Đã dọn dẹp vĩnh viễn {deleted_count} tài khoản soft-deleted thành công!"
    }


def run_data_lifecycle_maintenance_job(admin_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Thực hiện tổng thể quy trình bảo trì vòng đời dữ liệu (Data Lifecycle Maintenance):
    1. Tự động sao lưu CSDL định kỳ (nếu cấu hình BACKUP_AUTO_ENABLED=True)
    2. Dọn dẹp Audit Logs cũ theo retention policy
    3. Dọn dẹp bản sao lưu CSDL cũ theo retention count
    4. Dọn dẹp tài khoản soft-deleted quá hạn 180 ngày
    """
    from .backup_service import create_database_backup, cleanup_old_backups, get_backup_settings
    from .log_service import cleanup_audit_logs

    results = {}

    # 1. Check auto backup
    b_settings = get_backup_settings()
    if b_settings.get("BACKUP_AUTO_ENABLED"):
        backup_res = create_database_backup(backup_type="AUTO", admin_id=admin_id, notes="Tự động sao lưu bảo trì hệ thống định kỳ")
        results["auto_backup"] = backup_res
    else:
        results["auto_backup"] = {"skipped": True, "message": "Tự động sao lưu đang tắt"}

    # 2. Cleanup audit logs
    log_res = cleanup_audit_logs(current_user_id=admin_id)
    results["audit_logs_cleanup"] = log_res

    # 3. Cleanup old backups
    backup_cleanup_count = cleanup_old_backups()
    results["backups_cleanup"] = {"deleted_count": backup_cleanup_count}

    # 4. Purge soft-deleted users
    purge_res = purge_soft_deleted_users(admin_id=admin_id)
    results["purged_users"] = purge_res

    return {
        "success": True,
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "details": results,
        "message": "Hoàn tất bảo trì vòng đời dữ liệu hệ thống (Data Lifecycle Maintenance)!"
    }
