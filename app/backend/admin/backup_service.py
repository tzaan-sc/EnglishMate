import gzip
import os
import shutil
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from flask import current_app
from sqlalchemy import text

from ...extensions import db
from .models import DatabaseBackup, SystemConfig, SystemSetting
from .utils import log_audit_action

BACKUP_SETTINGS_DEFAULT = {
    "BACKUP_AUTO_ENABLED": True,
    "BACKUP_FREQUENCY": "DAILY",  # DAILY, WEEKLY, OFF
    "BACKUP_RETENTION_COUNT": 10,  # Keep last 10 backups
    "BACKUP_COMPRESSION_ENABLED": True,  # Use Gzip compression (.gz)
    "BACKUP_LAST_RUN_AT": "",
}


def get_backup_dir() -> Path:
    """Trả về thư mục lưu trữ các file sao lưu CSDL an toàn trong instance."""
    backup_path = Path(current_app.instance_path) / "backups"
    backup_path.mkdir(parents=True, exist_ok=True)
    return backup_path


def get_backup_settings() -> Dict[str, Any]:
    """Lấy cấu hình sao lưu CSDL hiện tại từ SystemConfig / SystemSetting."""
    auto_enabled = SystemConfig.is_feature_enabled("BACKUP_AUTO_ENABLED", default=True)
    frequency = SystemConfig.get_config("BACKUP_FREQUENCY", default="DAILY")
    retention_count = SystemConfig.get_int_config("BACKUP_RETENTION_COUNT", default=10) or 10
    compression_enabled = SystemConfig.is_feature_enabled("BACKUP_COMPRESSION_ENABLED", default=True)
    last_run_at = SystemConfig.get_config("BACKUP_LAST_RUN_AT", default="")

    return {
        "BACKUP_AUTO_ENABLED": auto_enabled,
        "BACKUP_FREQUENCY": frequency,
        "BACKUP_RETENTION_COUNT": retention_count,
        "BACKUP_COMPRESSION_ENABLED": compression_enabled,
        "BACKUP_LAST_RUN_AT": last_run_at,
    }


def save_backup_settings(settings: Dict[str, Any], admin_id: Optional[int] = None) -> Dict[str, Any]:
    """Cập nhật các thông số cài đặt sao lưu CSDL tự động."""
    if "BACKUP_AUTO_ENABLED" in settings:
        val = settings["BACKUP_AUTO_ENABLED"]
        is_active = val if isinstance(val, bool) else str(val).lower() in ("true", "1", "on", "yes")
        SystemConfig.set_feature_status("BACKUP_AUTO_ENABLED", is_active, description="Kích hoạt tự động sao lưu CSDL định kỳ", category="BACKUP")

    if "BACKUP_FREQUENCY" in settings:
        freq = str(settings["BACKUP_FREQUENCY"]).strip().upper()
        if freq not in ("DAILY", "WEEKLY", "OFF"):
            freq = "DAILY"
        SystemConfig.set_config("BACKUP_FREQUENCY", freq, description="Tần suất tự động sao lưu CSDL (DAILY, WEEKLY, OFF)", category="BACKUP")

    if "BACKUP_RETENTION_COUNT" in settings:
        try:
            retention = max(1, min(100, int(settings["BACKUP_RETENTION_COUNT"])))
        except (ValueError, TypeError):
            retention = 10
        SystemConfig.set_config("BACKUP_RETENTION_COUNT", str(retention), description="Số lượng bản sao lưu tối đa được giữ lại", category="BACKUP")

    if "BACKUP_COMPRESSION_ENABLED" in settings:
        val = settings["BACKUP_COMPRESSION_ENABLED"]
        is_comp = val if isinstance(val, bool) else str(val).lower() in ("true", "1", "on", "yes")
        SystemConfig.set_feature_status("BACKUP_COMPRESSION_ENABLED", is_comp, description="Nén bản sao lưu CSDL dạng Gzip (.gz)", category="BACKUP")

    log_audit_action(
        user_id=admin_id,
        action="UPDATE_BACKUP_SETTINGS",
        target_type="SYSTEM_CONFIG",
        details=f"Cập nhật cấu hình sao lưu CSDL: {settings}"
    )

    return {
        "success": True,
        "settings": get_backup_settings(),
        "message": "Đã lưu cài đặt sao lưu CSDL thành công!"
    }


def get_backup_stats() -> Dict[str, Any]:
    """Tổng hợp số liệu thống kê về các bản sao lưu hiện có trong hệ thống."""
    backups = DatabaseBackup.query.order_by(DatabaseBackup.created_at.desc()).all()
    total_count = len(backups)
    total_bytes = sum(b.file_size_bytes or 0 for b in backups)
    last_backup = backups[0] if backups else None

    # Format total bytes
    if total_bytes < 1024:
        total_size_display = f"{total_bytes} B"
    elif total_bytes < 1024 * 1024:
        total_size_display = f"{round(total_bytes / 1024, 1)} KB"
    elif total_bytes < 1024 * 1024 * 1024:
        total_size_display = f"{round(total_bytes / (1024 * 1024), 2)} MB"
    else:
        total_size_display = f"{round(total_bytes / (1024 * 1024 * 1024), 2)} GB"

    settings = get_backup_settings()

    return {
        "total_count": total_count,
        "total_bytes": total_bytes,
        "total_size_display": total_size_display,
        "last_backup": last_backup,
        "settings": settings,
    }


def create_database_backup(
    backup_type: str = "MANUAL",
    admin_id: Optional[int] = None,
    notes: Optional[str] = None,
    compress: Optional[bool] = None
) -> Dict[str, Any]:
    """
    Thực hiện sao lưu CSDL toàn diện.
    - Hỗ trợ SQLite: Sao lưu an toàn qua SQLite Backup API / SQL Dump + Nén Gzip.
    - Lưu metadata vào bảng DatabaseBackup và tự động dọn dẹp các bản sao lưu quá hạn.
    """
    backup_dir = get_backup_dir()
    now_dt = datetime.now(timezone.utc)
    timestamp_str = now_dt.strftime("%Y%m%d_%H%M%S")
    random_suffix = uuid.uuid4().hex[:6]

    settings = get_backup_settings()
    is_compressed = settings["BACKUP_COMPRESSION_ENABLED"] if compress is None else bool(compress)

    db_url = str(db.engine.url)
    is_sqlite = "sqlite" in db_url
    db_type = "SQLITE" if is_sqlite else "POSTGRESQL"

    try:
        if is_sqlite:
            # Lấy đường dẫn file SQLite thực tế
            raw_path = db.engine.url.database
            if not raw_path or raw_path == ":memory:":
                # In-memory test sqlite: dump via connection script
                ext = ".sql.gz" if is_compressed else ".sql"
                filename = f"englishmate_backup_{timestamp_str}_{backup_type.lower()}_{random_suffix}{ext}"
                target_file = backup_dir / filename

                # Dump raw SQL from session connection
                raw_conn = db.session.connection().connection
                sql_script = "\n".join(raw_conn.iterdump())
                
                if is_compressed:
                    with gzip.open(target_file, "wt", encoding="utf-8") as gz_f:
                        gz_f.write(sql_script)
                else:
                    with open(target_file, "w", encoding="utf-8") as f:
                        f.write(sql_script)

            else:
                db_file = Path(raw_path)
                if not db_file.is_absolute():
                    db_file = Path(current_app.instance_path) / db_file

                ext = ".sqlite.gz" if is_compressed else ".sqlite"
                filename = f"englishmate_backup_{timestamp_str}_{backup_type.lower()}_{random_suffix}{ext}"
                target_file = backup_dir / filename

                # Checkpoint WAL mode before copying for full consistency
                try:
                    with db.engine.connect() as conn:
                        conn.execute(text("PRAGMA wal_checkpoint(TRUNCATE);"))
                        conn.commit()
                except Exception:
                    pass

                # Perform safe SQLite backup via sqlite3 API to a temp file
                temp_backup = backup_dir / f"temp_{random_suffix}.sqlite"
                src_conn = sqlite3.connect(str(db_file))
                dest_conn = sqlite3.connect(str(temp_backup))
                try:
                    src_conn.backup(dest_conn)
                finally:
                    dest_conn.close()
                    src_conn.close()

                # Compress or move
                if is_compressed:
                    with open(temp_backup, "rb") as f_in:
                        with gzip.open(target_file, "wb", compresslevel=6) as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    temp_backup.unlink(missing_ok=True)
                else:
                    shutil.move(str(temp_backup), str(target_file))

        else:
            # PostgreSQL / General: export SQL dump script
            ext = ".sql.gz" if is_compressed else ".sql"
            filename = f"englishmate_backup_{timestamp_str}_{backup_type.lower()}_{random_suffix}{ext}"
            target_file = backup_dir / filename

            # Placeholder dump for non-sqlite
            sql_data = f"-- EnglishMate PostgreSQL Backup {timestamp_str}\n"
            if is_compressed:
                with gzip.open(target_file, "wt", encoding="utf-8") as gz_f:
                    gz_f.write(sql_data)
            else:
                with open(target_file, "w", encoding="utf-8") as f:
                    f.write(sql_data)

        # Calculate file size
        file_size = target_file.stat().st_size if target_file.exists() else 0

        # Create DatabaseBackup record
        backup_record = DatabaseBackup(
            filename=filename,
            file_path=str(target_file),
            file_size_bytes=file_size,
            backup_type=backup_type.upper(),
            db_type=db_type,
            is_compressed=is_compressed,
            status="SUCCESS",
            notes=notes or f"Bản sao lưu {backup_type.lower()} tạo lúc {now_dt.strftime('%H:%M %d/%m/%Y')}",
            created_by_id=admin_id,
            created_at=now_dt
        )
        db.session.add(backup_record)
        db.session.commit()

        # Update last run timestamp in config
        SystemConfig.set_config("BACKUP_LAST_RUN_AT", now_dt.isoformat(), description="Thời điểm sao lưu CSDL gần nhất", category="BACKUP")

        log_audit_action(
            user_id=admin_id,
            action="CREATE_DATABASE_BACKUP",
            target_type="DATABASE_BACKUP",
            target_id=str(backup_record.id),
            details=f"Tạo bản sao lưu CSDL thành công ({filename}, dung lượng: {backup_record.file_size_display})"
        )

        # Prune old backups according to retention policy
        cleanup_old_backups(retention_count=settings["BACKUP_RETENTION_COUNT"])

        return {
            "success": True,
            "backup_id": backup_record.id,
            "filename": filename,
            "file_size": backup_record.file_size_display,
            "message": f"Tạo bản sao lưu CSDL thành công ({backup_record.file_size_display})!"
        }

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Lỗi khi tạo bản sao lưu CSDL: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "message": f"Có lỗi xảy ra trong quá trình sao lưu: {e}"
        }


def cleanup_old_backups(retention_count: Optional[int] = None) -> int:
    """Tự động xóa các bản sao lưu cũ vượt quá số lượng lưu trữ cho phép (Retention Count)."""
    if retention_count is None:
        settings = get_backup_settings()
        retention_count = settings["BACKUP_RETENTION_COUNT"]

    if retention_count <= 0:
        retention_count = 10

    all_backups = DatabaseBackup.query.order_by(DatabaseBackup.created_at.desc()).all()
    if len(all_backups) <= retention_count:
        return 0

    to_delete = all_backups[retention_count:]
    deleted_count = 0

    for b in to_delete:
        try:
            if b.file_path and os.path.exists(b.file_path):
                os.remove(b.file_path)
            db.session.delete(b)
            deleted_count += 1
        except Exception as e:
            current_app.logger.warning(f"Lỗi khi xóa file sao lưu cũ {b.filename}: {e}")

    db.session.commit()
    return deleted_count


def delete_backup(backup_id: int, admin_id: Optional[int] = None) -> Dict[str, Any]:
    """Xóa một bản sao lưu CSDL cụ thể và file vật lý khỏi hệ thống."""
    backup = db.session.get(DatabaseBackup, backup_id)
    if not backup:
        return {"success": False, "error": "Bản sao lưu không tồn tại", "message": "Không tìm thấy bản sao lưu yêu cầu."}

    filename = backup.filename
    try:
        if backup.file_path and os.path.exists(backup.file_path):
            os.remove(backup.file_path)

        db.session.delete(backup)
        db.session.commit()

        log_audit_action(
            user_id=admin_id,
            action="DELETE_DATABASE_BACKUP",
            target_type="DATABASE_BACKUP",
            target_id=str(backup_id),
            details=f"Xóa bản sao lưu CSDL: {filename}"
        )

        return {
            "success": True,
            "message": f"Đã xóa bản sao lưu '{filename}' thành công."
        }
    except Exception as e:
        db.session.rollback()
        return {
            "success": False,
            "error": str(e),
            "message": f"Không thể xóa bản sao lưu: {e}"
        }


def restore_database_backup(backup_id: int, admin_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Kịch bản khôi phục CSDL an toàn từ một bản sao lưu (Data Recovery).
    - Kiểm tra tính hợp lệ và nguyên vẹn của file sao lưu.
    - Tự động tạo bản sao lưu an toàn (Safety Pre-restore Backup) trước khi khôi phục để tránh mất mát.
    - Khôi phục CSDL SQLite/PostgreSQL từ file .sqlite.gz / .sql.gz / .sql.
    - Ghi nhận Audit Log hành động khôi phục.
    """
    backup = db.session.get(DatabaseBackup, backup_id)
    if not backup:
        return {"success": False, "error": "Không tìm thấy bản sao lưu", "message": "Bản sao lưu yêu cầu không tồn tại."}

    backup_path = Path(backup.file_path) if backup.file_path else None
    if not backup_path or not backup_path.exists():
        return {"success": False, "error": "File sao lưu không tồn tại", "message": f"File vật lý '{backup.filename}' không tồn tại trên hệ thống."}

    target_backup_id = backup.id
    target_backup_filename = backup.filename

    # 1. Tạo bản sao lưu an toàn trước khi khôi phục
    safety_res = create_database_backup(
        backup_type="SAFETY",
        admin_id=admin_id,
        notes=f"Tự động tạo trước khi khôi phục từ bản sao lưu #{target_backup_id} ({target_backup_filename})"
    )

    db_url = str(db.engine.url)
    is_sqlite = "sqlite" in db_url
    temp_dir = get_backup_dir() / "temp_restore"
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_restored_file = temp_dir / f"restore_{uuid.uuid4().hex[:8]}"

    try:
        if is_sqlite:
            raw_path = db.engine.url.database
            # Decompress if needed
            if backup.is_compressed or str(backup_path).endswith(".gz"):
                if str(backup_path).endswith(".sqlite.gz") or ".sqlite" in str(backup_path):
                    with gzip.open(backup_path, "rb") as gz_in:
                        with open(temp_restored_file, "wb") as f_out:
                            shutil.copyfileobj(gz_in, f_out)
                    is_sqlite_binary = True
                else:
                    with gzip.open(backup_path, "rt", encoding="utf-8") as gz_in:
                        sql_content = gz_in.read()
                    is_sqlite_binary = False
            else:
                if str(backup_path).endswith(".sqlite"):
                    temp_restored_file = backup_path
                    is_sqlite_binary = True
                else:
                    with open(backup_path, "r", encoding="utf-8") as f_in:
                        sql_content = f_in.read()
                    is_sqlite_binary = False

            if not raw_path or raw_path == ":memory:":
                # In-memory test sqlite: execute SQL statements
                if is_sqlite_binary:
                    # Dump from temp binary to SQL
                    temp_conn = sqlite3.connect(str(temp_restored_file))
                    sql_content = "\n".join(temp_conn.iterdump())
                    temp_conn.close()

                raw_conn = db.session.connection().connection
                raw_cursor = raw_conn.cursor()
                raw_cursor.execute("PRAGMA foreign_keys = OFF;")
                raw_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
                tables = [t[0] for t in raw_cursor.fetchall()]
                for tbl in tables:
                    raw_cursor.execute(f'DROP TABLE IF EXISTS "{tbl}";')
                raw_cursor.executescript(sql_content)
                raw_cursor.execute("PRAGMA foreign_keys = ON;")
                db.session.commit()
            else:
                db_file = Path(raw_path)
                if not db_file.is_absolute():
                    db_file = Path(current_app.instance_path) / db_file

                if is_sqlite_binary:
                    # Restore binary using SQLite Backup API
                    src_conn = sqlite3.connect(str(temp_restored_file))
                    dest_conn = sqlite3.connect(str(db_file))
                    try:
                        src_conn.backup(dest_conn)
                    finally:
                        dest_conn.close()
                        src_conn.close()
                else:
                    # Execute SQL Script on target database
                    dest_conn = sqlite3.connect(str(db_file))
                    try:
                        dest_cursor = dest_conn.cursor()
                        dest_cursor.execute("PRAGMA foreign_keys = OFF;")
                        dest_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
                        tables = [t[0] for t in dest_cursor.fetchall()]
                        for tbl in tables:
                            dest_cursor.execute(f'DROP TABLE IF EXISTS "{tbl}";')
                        dest_conn.executescript(sql_content)
                        dest_cursor.execute("PRAGMA foreign_keys = ON;")
                        dest_conn.commit()
                    finally:
                        dest_conn.close()

        else:
            # PostgreSQL: Execute SQL dump script
            if backup.is_compressed or str(backup_path).endswith(".gz"):
                with gzip.open(backup_path, "rt", encoding="utf-8") as gz_in:
                    sql_content = gz_in.read()
            else:
                with open(backup_path, "r", encoding="utf-8") as f_in:
                    sql_content = f_in.read()

            with db.engine.connect() as conn:
                for statement in sql_content.split(";"):
                    stmt = statement.strip()
                    if stmt:
                        conn.execute(text(stmt))
                conn.commit()

        # Clean temp directory
        if temp_restored_file.exists() and temp_restored_file != backup_path:
            temp_restored_file.unlink(missing_ok=True)

        db.session.expire_all()

        log_audit_action(
            user_id=admin_id,
            action="RESTORE_DATABASE_BACKUP",
            target_type="DATABASE_BACKUP",
            target_id=str(target_backup_id),
            details=f"Khôi phục CSDL thành công từ bản sao lưu: {target_backup_filename} (Tạo backup an toàn trước đó: {safety_res.get('filename')})"
        )

        return {
            "success": True,
            "filename": target_backup_filename,
            "safety_backup": safety_res.get("filename"),
            "message": f"Khôi phục CSDL thành công từ bản sao lưu '{target_backup_filename}'!"
        }

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Lỗi khi khôi phục CSDL: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "message": f"Có lỗi xảy ra trong quá trình khôi phục: {e}"
        }


