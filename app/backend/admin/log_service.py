import csv
import os
from datetime import datetime, timezone, timedelta
from io import StringIO
from app.extensions import db
from .models import AuditLog, SystemSetting
from .utils import log_audit_action


DEFAULT_RETENTION_DAYS = 90
SETTING_KEY_RETENTION = "LOG_RETENTION_DAYS"


def get_log_retention_days() -> int:
    """Lấy số ngày lưu trữ log được cấu hình trong SystemSetting (mặc định 90 ngày)."""
    days = SystemSetting.get_int_setting(SETTING_KEY_RETENTION, default=DEFAULT_RETENTION_DAYS)
    if days is None or days <= 0:
        return DEFAULT_RETENTION_DAYS
    return days


def set_log_retention_days(days: int) -> int:
    """Cập nhật cấu hình số ngày lưu trữ log vào SystemSetting."""
    try:
        days = int(days)
        if days < 1:
            raise ValueError("Số ngày lưu trữ phải lớn hơn 0")
    except (TypeError, ValueError) as e:
        raise ValueError("Số ngày lưu trữ không hợp lệ") from e

    SystemSetting.set_setting(
        SETTING_KEY_RETENTION,
        str(days),
        "Số ngày lưu trữ nhật ký kiểm tra (Audit Logs) trước khi tự động dọn dẹp"
    )
    return days


def get_retention_stats(custom_days: int = None) -> dict:
    """Lấy thống kê tổng quát về nhật ký kiểm tra và số bản ghi đủ điều kiện dọn dẹp."""
    retention_days = custom_days if (custom_days and custom_days > 0) else get_log_retention_days()
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)

    total_logs = AuditLog.query.count()
    eligible_logs = AuditLog.query.filter(AuditLog.created_at < cutoff_date).count()

    oldest_log = AuditLog.query.order_by(AuditLog.created_at.asc()).first()
    newest_log = AuditLog.query.order_by(AuditLog.created_at.desc()).first()

    return {
        "retention_days": retention_days,
        "total_logs": total_logs,
        "eligible_logs": eligible_logs,
        "cutoff_date": cutoff_date.isoformat(),
        "oldest_log_date": oldest_log.created_at_vn.strftime("%d/%m/%Y %H:%M:%S") if (oldest_log and oldest_log.created_at_vn) else None,
        "newest_log_date": newest_log.created_at_vn.strftime("%d/%m/%Y %H:%M:%S") if (newest_log and newest_log.created_at_vn) else None,
    }


def export_logs_to_file(query_or_logs, file_path: str) -> int:
    """Xuất danh sách log ra file CSV lưu trữ trước khi dọn dẹp."""
    if hasattr(query_or_logs, "all"):
        logs = query_or_logs.all()
    else:
        logs = query_or_logs

    dirname = os.path.dirname(os.path.abspath(file_path))
    if dirname and not os.path.exists(dirname):
        os.makedirs(dirname, exist_ok=True)

    with open(file_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "ID", "User ID", "Username", "Action", "Target Type", 
            "Target ID", "IP Address", "Created At (UTC+7)", "Details"
        ])
        for log in logs:
            username = log.user.username if log.user else "System"
            created_str = log.created_at_vn.strftime("%Y-%m-%d %H:%M:%S") if log.created_at_vn else ""
            writer.writerow([
                log.id,
                log.user_id or "",
                username,
                log.action or "",
                log.target_type or "",
                log.target_id or "",
                log.ip_address or "",
                created_str,
                log.details or ""
            ])
    return len(logs)


def cleanup_audit_logs(days: int = None, archive_path: str = None, dry_run: bool = False, current_user_id: int = None) -> dict:
    """
    Thực hiện dọn dẹp hoặc lưu trữ các bản ghi nhật ký kiểm tra (Audit Logs) cũ hơn số ngày chỉ định.
    
    :param days: Số ngày lưu trữ (nếu None sẽ lấy từ SystemSetting hoặc mặc định 90).
    :param archive_path: Đường dẫn file CSV lưu trữ trước khi xóa (tùy chọn).
    :param dry_run: Chế độ kiểm tra, không thực sự xóa dữ liệu.
    :param current_user_id: ID admin thực hiện hành động để ghi log kiểm tra.
    :return: dict chứa kết quả thực hiện.
    """
    if days is None or days <= 0:
        days = get_log_retention_days()

    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
    query = AuditLog.query.filter(AuditLog.created_at < cutoff_date)
    count = query.count()

    if count == 0:
        return {
            "success": True,
            "deleted_count": 0,
            "dry_run": dry_run,
            "days": days,
            "cutoff_date": cutoff_date.isoformat(),
            "archived_file": None,
            "message": f"Không có bản ghi nhật ký nào cũ hơn {days} ngày (trước {cutoff_date.strftime('%d/%m/%Y')})."
        }

    archived_file_saved = None
    if archive_path:
        archived_count = export_logs_to_file(query, archive_path)
        archived_file_saved = os.path.abspath(archive_path)

    if dry_run:
        return {
            "success": True,
            "dry_run": True,
            "matching_count": count,
            "deleted_count": 0,
            "days": days,
            "cutoff_date": cutoff_date.isoformat(),
            "archived_file": archived_file_saved,
            "message": f"[DRY-RUN] Tìm thấy {count} bản ghi nhật ký cũ hơn {days} ngày cần dọn dẹp."
        }

    # Batch delete
    deleted_rows = query.delete(synchronize_session=False)
    db.session.commit()

    if current_user_id:
        try:
            log_audit_action(
                current_user_id,
                "CLEANUP_AUDIT_LOGS",
                "AuditLog",
                None,
                f"Dọn dẹp {deleted_rows} bản ghi nhật ký cũ hơn {days} ngày (trước {cutoff_date.strftime('%d/%m/%Y')})"
                + (f", lưu trữ tại {archive_path}" if archive_path else "")
            )
        except Exception:
            pass

    return {
        "success": True,
        "dry_run": False,
        "deleted_count": deleted_rows,
        "days": days,
        "cutoff_date": cutoff_date.isoformat(),
        "archived_file": archived_file_saved,
        "message": f"Đã dọn dẹp thành công {deleted_rows} bản ghi nhật ký cũ hơn {days} ngày."
    }
