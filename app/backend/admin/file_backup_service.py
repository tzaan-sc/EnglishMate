import io
import os
import shutil
import zipfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from flask import current_app

from ...extensions import db
from .models import DatabaseBackup, SystemConfig, SystemSetting
from .utils import log_audit_action

try:
    import boto3
    from botocore.config import Config as BotoConfig
    HAS_BOTO3 = True
except ImportError:
    HAS_BOTO3 = False

try:
    import cloudinary
    import cloudinary.uploader
    HAS_CLOUDINARY = True
except ImportError:
    HAS_CLOUDINARY = False


def get_uploads_dir() -> Path:
    """Trả về đường dẫn thư mục uploads chính của ứng dụng."""
    if current_app and current_app.static_folder:
        uploads_path = Path(current_app.static_folder) / "uploads"
    else:
        uploads_path = Path(os.getcwd()) / "app" / "frontend" / "static" / "uploads"
    uploads_path.mkdir(parents=True, exist_ok=True)
    return uploads_path


def get_file_backup_dir() -> Path:
    """Trả về thư mục lưu trữ các file nén sao lưu uploads cục bộ trong instance/backups/uploads."""
    if current_app and hasattr(current_app, "instance_path"):
        base_dir = Path(current_app.instance_path) / "backups" / "uploads"
    else:
        base_dir = Path(os.getcwd()) / "instance" / "backups" / "uploads"
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir


def format_bytes(size_bytes: int) -> str:
    """Format dung lượng byte sang định dạng B, KB, MB, GB dễ đọc."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{round(size_bytes / 1024, 1)} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{round(size_bytes / (1024 * 1024), 2)} MB"
    else:
        return f"{round(size_bytes / (1024 * 1024 * 1024), 2)} GB"


def get_uploads_stats() -> Dict[str, Any]:
    """
    Tổng hợp thống kê chi tiết thư mục static/uploads/:
    - Tổng số file, tổng dung lượng.
    - Phân tích chi tiết từng thư mục con: avatars, exams, audio, general.
    - Trạng thái cấu hình Cloud Storage (S3, Cloudinary).
    """
    uploads_dir = get_uploads_dir()
    total_files = 0
    total_bytes = 0
    folder_stats: Dict[str, Dict[str, Any]] = {
        "avatars": {"files": 0, "bytes": 0, "display": "0 B"},
        "exams": {"files": 0, "bytes": 0, "display": "0 B"},
        "audio": {"files": 0, "bytes": 0, "display": "0 B"},
        "others": {"files": 0, "bytes": 0, "display": "0 B"},
    }

    if uploads_dir.exists():
        for root, dirs, files in os.walk(uploads_dir):
            rel_root = os.path.relpath(root, uploads_dir).lower()
            category = "others"
            if rel_root == "avatars" or rel_root.startswith("avatars"):
                category = "avatars"
            elif rel_root == "exams" or rel_root.startswith("exams"):
                category = "exams"
            elif rel_root == "audio" or rel_root.startswith("audio"):
                category = "audio"

            for f in files:
                f_path = Path(root) / f
                try:
                    f_size = f_path.stat().st_size
                    total_files += 1
                    total_bytes += f_size
                    folder_stats[category]["files"] += 1
                    folder_stats[category]["bytes"] += f_size
                except Exception:
                    pass

    for cat in folder_stats:
        folder_stats[cat]["display"] = format_bytes(folder_stats[cat]["bytes"])

    cloud_settings = get_cloud_storage_settings()

    return {
        "total_files": total_files,
        "total_bytes": total_bytes,
        "total_size_display": format_bytes(total_bytes),
        "folder_stats": folder_stats,
        "cloud_settings": cloud_settings,
        "uploads_path": str(uploads_dir)
    }


def get_cloud_storage_settings() -> Dict[str, Any]:
    """Lấy cấu hình Cloud Storage hiện tại từ SystemConfig / Environment Variables."""
    s3_bucket = SystemConfig.get_config("S3_BUCKET_NAME", default=os.getenv("S3_BUCKET_NAME", ""))
    s3_region = SystemConfig.get_config("AWS_REGION", default=os.getenv("AWS_REGION", "ap-southeast-1"))
    s3_endpoint = SystemConfig.get_config("S3_ENDPOINT_URL", default=os.getenv("S3_ENDPOINT_URL", ""))
    s3_has_key = bool(SystemConfig.get_config("AWS_ACCESS_KEY_ID", default=os.getenv("AWS_ACCESS_KEY_ID", "")))
    s3_has_secret = bool(SystemConfig.get_config("AWS_SECRET_ACCESS_KEY", default=os.getenv("AWS_SECRET_ACCESS_KEY", "")))
    s3_enabled = SystemConfig.is_feature_enabled("S3_BACKUP_ENABLED", default=False)

    cld_name = SystemConfig.get_config("CLOUDINARY_CLOUD_NAME", default=os.getenv("CLOUDINARY_CLOUD_NAME", ""))
    cld_has_key = bool(SystemConfig.get_config("CLOUDINARY_API_KEY", default=os.getenv("CLOUDINARY_API_KEY", "")))
    cld_has_secret = bool(SystemConfig.get_config("CLOUDINARY_API_SECRET", default=os.getenv("CLOUDINARY_API_SECRET", "")))
    cld_folder = SystemConfig.get_config("CLOUDINARY_FOLDER", default="englishmate_backups")
    cld_enabled = SystemConfig.is_feature_enabled("CLOUDINARY_BACKUP_ENABLED", default=False)

    return {
        "s3_bucket": s3_bucket,
        "s3_region": s3_region,
        "s3_endpoint": s3_endpoint,
        "s3_configured": bool(s3_bucket and (s3_has_key or os.getenv("AWS_ACCESS_KEY_ID"))),
        "s3_enabled": s3_enabled,
        "cloudinary_cloud_name": cld_name,
        "cloudinary_folder": cld_folder,
        "cloudinary_configured": bool(cld_name and (cld_has_key or os.getenv("CLOUDINARY_API_KEY"))),
        "cloudinary_enabled": cld_enabled,
    }


def save_cloud_storage_settings(settings: Dict[str, Any], admin_id: Optional[int] = None) -> Dict[str, Any]:
    """Cập nhật các tham số cấu hình Cloud Storage (S3 / Cloudinary)."""
    # S3 Settings
    if "S3_BUCKET_NAME" in settings:
        SystemConfig.set_config("S3_BUCKET_NAME", settings["S3_BUCKET_NAME"].strip(), description="Tên AWS S3 Bucket sao lưu uploads", category="CLOUD_STORAGE")
    if "AWS_REGION" in settings:
        SystemConfig.set_config("AWS_REGION", settings["AWS_REGION"].strip(), description="AWS Region S3", category="CLOUD_STORAGE")
    if "S3_ENDPOINT_URL" in settings:
        SystemConfig.set_config("S3_ENDPOINT_URL", settings["S3_ENDPOINT_URL"].strip(), description="Custom S3 / MinIO / R2 Endpoint URL", category="CLOUD_STORAGE")
    if "AWS_ACCESS_KEY_ID" in settings and settings["AWS_ACCESS_KEY_ID"].strip():
        SystemConfig.set_config("AWS_ACCESS_KEY_ID", settings["AWS_ACCESS_KEY_ID"].strip(), description="AWS Access Key ID", category="CLOUD_STORAGE")
    if "AWS_SECRET_ACCESS_KEY" in settings and settings["AWS_SECRET_ACCESS_KEY"].strip():
        SystemConfig.set_config("AWS_SECRET_ACCESS_KEY", settings["AWS_SECRET_ACCESS_KEY"].strip(), description="AWS Secret Access Key", category="CLOUD_STORAGE")
    if "S3_BACKUP_ENABLED" in settings:
        val = settings["S3_BACKUP_ENABLED"]
        is_active = val if isinstance(val, bool) else str(val).lower() in ("true", "1", "on", "yes")
        SystemConfig.set_feature_status("S3_BACKUP_ENABLED", is_active, description="Kích hoạt tự động sao lưu S3", category="CLOUD_STORAGE")

    # Cloudinary Settings
    if "CLOUDINARY_CLOUD_NAME" in settings:
        SystemConfig.set_config("CLOUDINARY_CLOUD_NAME", settings["CLOUDINARY_CLOUD_NAME"].strip(), description="Cloudinary Cloud Name", category="CLOUD_STORAGE")
    if "CLOUDINARY_API_KEY" in settings and settings["CLOUDINARY_API_KEY"].strip():
        SystemConfig.set_config("CLOUDINARY_API_KEY", settings["CLOUDINARY_API_KEY"].strip(), description="Cloudinary API Key", category="CLOUD_STORAGE")
    if "CLOUDINARY_API_SECRET" in settings and settings["CLOUDINARY_API_SECRET"].strip():
        SystemConfig.set_config("CLOUDINARY_API_SECRET", settings["CLOUDINARY_API_SECRET"].strip(), description="Cloudinary API Secret", category="CLOUD_STORAGE")
    if "CLOUDINARY_FOLDER" in settings:
        SystemConfig.set_config("CLOUDINARY_FOLDER", settings["CLOUDINARY_FOLDER"].strip() or "englishmate_backups", description="Cloudinary Backup Folder", category="CLOUD_STORAGE")
    if "CLOUDINARY_BACKUP_ENABLED" in settings:
        val = settings["CLOUDINARY_BACKUP_ENABLED"]
        is_active = val if isinstance(val, bool) else str(val).lower() in ("true", "1", "on", "yes")
        SystemConfig.set_feature_status("CLOUDINARY_BACKUP_ENABLED", is_active, description="Kích hoạt tự động sao lưu Cloudinary", category="CLOUD_STORAGE")

    log_audit_action(
        user_id=admin_id,
        action="UPDATE_CLOUD_STORAGE_SETTINGS",
        target_type="SYSTEM_CONFIG",
        details="Cập nhật thông số kết nối Cloud Storage (AWS S3 / Cloudinary)"
    )

    return {
        "success": True,
        "message": "Đã lưu cài đặt Cloud Storage thành công!",
        "settings": get_cloud_storage_settings()
    }


def create_uploads_archive(archive_format: str = "zip") -> Dict[str, Any]:
    """
    Nén toàn bộ thư mục static/uploads/ thành file nén .zip với thuật toán tối ưu.
    Lưu trữ an toàn tại instance/backups/uploads/.
    """
    uploads_dir = get_uploads_dir()
    backup_dir = get_file_backup_dir()

    now_dt = datetime.now(timezone.utc)
    timestamp_str = now_dt.strftime("%Y%m%d_%H%M%S")
    rand_suffix = uuid.uuid4().hex[:6]
    filename = f"uploads_backup_{timestamp_str}_{rand_suffix}.zip"
    target_zip_path = backup_dir / filename

    file_count = 0
    with zipfile.ZipFile(target_zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
        if uploads_dir.exists():
            for root, dirs, files in os.walk(uploads_dir):
                for file in files:
                    file_path = Path(root) / file
                    rel_path = os.path.relpath(file_path, uploads_dir)
                    zipf.write(file_path, arcname=rel_path)
                    file_count += 1

    file_size_bytes = target_zip_path.stat().st_size if target_zip_path.exists() else 0

    return {
        "success": True,
        "filename": filename,
        "file_path": str(target_zip_path),
        "file_size_bytes": file_size_bytes,
        "file_size_display": format_bytes(file_size_bytes),
        "file_count": file_count,
        "created_at": now_dt
    }


def upload_to_s3(
    file_path: Union[str, Path],
    s3_key: Optional[str] = None,
    custom_config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Tải file sao lưu lên AWS S3 (hoặc S3-compatible như MinIO, Cloudflare R2).
    """
    if not HAS_BOTO3:
        return {"success": False, "error": "Thư viện boto3 chưa được cài đặt."}

    file_p = Path(file_path)
    if not file_p.exists():
        return {"success": False, "error": f"File '{file_path}' không tồn tại."}

    cfg = custom_config or {}
    bucket_name = cfg.get("S3_BUCKET_NAME") or SystemConfig.get_config("S3_BUCKET_NAME") or os.getenv("S3_BUCKET_NAME")
    aws_access_key = cfg.get("AWS_ACCESS_KEY_ID") or SystemConfig.get_config("AWS_ACCESS_KEY_ID") or os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_key = cfg.get("AWS_SECRET_ACCESS_KEY") or SystemConfig.get_config("AWS_SECRET_ACCESS_KEY") or os.getenv("AWS_SECRET_ACCESS_KEY")
    region = cfg.get("AWS_REGION") or SystemConfig.get_config("AWS_REGION") or os.getenv("AWS_REGION", "ap-southeast-1")
    endpoint_url = cfg.get("S3_ENDPOINT_URL") or SystemConfig.get_config("S3_ENDPOINT_URL") or os.getenv("S3_ENDPOINT_URL") or None

    if not bucket_name:
        return {"success": False, "error": "Chưa cấu hình tên S3 Bucket (S3_BUCKET_NAME)."}

    key = s3_key or f"backups/uploads/{file_p.name}"

    try:
        session_kwargs = {"region_name": region}
        if aws_access_key and aws_secret_key:
            session_kwargs["aws_access_key_id"] = aws_access_key
            session_kwargs["aws_secret_access_key"] = aws_secret_key

        client_kwargs = {}
        if endpoint_url:
            client_kwargs["endpoint_url"] = endpoint_url

        s3_client = boto3.client("s3", **session_kwargs, **client_kwargs)
        s3_client.upload_file(str(file_p), bucket_name, key)

        s3_url = f"https://{bucket_name}.s3.{region}.amazonaws.com/{key}" if not endpoint_url else f"{endpoint_url}/{bucket_name}/{key}"

        return {
            "success": True,
            "provider": "S3",
            "bucket": bucket_name,
            "key": key,
            "url": s3_url,
            "filename": file_p.name,
            "file_size": file_p.stat().st_size
        }
    except Exception as e:
        current_app.logger.error(f"Lỗi khi upload lên S3: {e}", exc_info=True)
        return {"success": False, "error": str(e), "provider": "S3"}


def upload_to_cloudinary(
    file_path: Union[str, Path],
    public_id: Optional[str] = None,
    custom_config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Tải file sao lưu lên Cloudinary Storage dưới dạng raw file archive.
    """
    if not HAS_CLOUDINARY:
        return {"success": False, "error": "Thư viện cloudinary chưa được cài đặt."}

    file_p = Path(file_path)
    if not file_p.exists():
        return {"success": False, "error": f"File '{file_path}' không tồn tại."}

    cfg = custom_config or {}
    cloud_name = cfg.get("CLOUDINARY_CLOUD_NAME") or SystemConfig.get_config("CLOUDINARY_CLOUD_NAME") or os.getenv("CLOUDINARY_CLOUD_NAME")
    api_key = cfg.get("CLOUDINARY_API_KEY") or SystemConfig.get_config("CLOUDINARY_API_KEY") or os.getenv("CLOUDINARY_API_KEY")
    api_secret = cfg.get("CLOUDINARY_API_SECRET") or SystemConfig.get_config("CLOUDINARY_API_SECRET") or os.getenv("CLOUDINARY_API_SECRET")
    folder = cfg.get("CLOUDINARY_FOLDER") or SystemConfig.get_config("CLOUDINARY_FOLDER") or "englishmate_backups"

    if not cloud_name:
        return {"success": False, "error": "Chưa cấu hình Cloudinary Cloud Name (CLOUDINARY_CLOUD_NAME)."}

    try:
        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret,
            secure=True
        )

        p_id = public_id or f"{folder}/{file_p.stem}"

        response = cloudinary.uploader.upload(
            str(file_p),
            resource_type="raw",
            public_id=p_id,
            overwrite=True
        )

        return {
            "success": True,
            "provider": "CLOUDINARY",
            "public_id": response.get("public_id", p_id),
            "url": response.get("secure_url") or response.get("url"),
            "bytes": response.get("bytes", file_p.stat().st_size),
            "filename": file_p.name
        }
    except Exception as e:
        current_app.logger.error(f"Lỗi khi upload lên Cloudinary: {e}", exc_info=True)
        return {"success": False, "error": str(e), "provider": "CLOUDINARY"}


def backup_uploads_to_cloud(
    provider: str = "LOCAL",  # "S3", "CLOUDINARY", "LOCAL", "ALL"
    admin_id: Optional[int] = None,
    notes: Optional[str] = None
) -> Dict[str, Any]:
    """
    Quy trình trọn gói sao lưu thư mục static/uploads/:
    1. Đóng gói nén ZIP toàn bộ static/uploads/.
    2. Tải lên Cloud Storage (AWS S3 hoặc Cloudinary hoặc Lưu trữ cục bộ).
    3. Ghi log bản ghi vào DatabaseBackup và AuditLog.
    """
    provider_clean = provider.strip().upper()

    # 1. Đóng gói ZIP
    archive_res = create_uploads_archive(archive_format="zip")
    if not archive_res.get("success"):
        return archive_res

    filename = archive_res["filename"]
    file_path = archive_res["file_path"]
    file_size_bytes = archive_res["file_size_bytes"]
    now_dt = archive_res["created_at"]

    cloud_results: Dict[str, Any] = {}
    cloud_url = None
    target_db_type = f"UPLOADS_{provider_clean}"

    # 2. Upload theo provider
    if provider_clean in ("S3", "ALL"):
        s3_res = upload_to_s3(file_path)
        cloud_results["s3"] = s3_res
        if s3_res.get("success"):
            cloud_url = s3_res.get("url")

    if provider_clean in ("CLOUDINARY", "ALL"):
        cld_res = upload_to_cloudinary(file_path)
        cloud_results["cloudinary"] = cld_res
        if cld_res.get("success") and not cloud_url:
            cloud_url = cld_res.get("url")

    # 3. Tạo bản ghi DatabaseBackup
    notes_str = notes or f"Sao lưu Uploads ({archive_res['file_count']} files) -> {provider_clean}"
    if cloud_url:
        notes_str += f" [Cloud URL: {cloud_url}]"

    backup_record = DatabaseBackup(
        filename=filename,
        file_path=file_path,
        file_size_bytes=file_size_bytes,
        backup_type="UPLOADS_BACKUP",
        db_type=target_db_type,
        is_compressed=True,
        status="SUCCESS",
        notes=notes_str,
        created_by_id=admin_id,
        created_at=now_dt
    )
    db.session.add(backup_record)
    db.session.commit()

    log_audit_action(
        user_id=admin_id,
        action="BACKUP_UPLOADS_FOLDER",
        target_type="FILE_BACKUP",
        target_id=str(backup_record.id),
        details=f"Sao lưu thư mục static/uploads/ ({archive_res['file_size_display']}, {archive_res['file_count']} files) lên {provider_clean}"
    )

    return {
        "success": True,
        "backup_id": backup_record.id,
        "filename": filename,
        "file_size": archive_res["file_size_display"],
        "file_count": archive_res["file_count"],
        "provider": provider_clean,
        "cloud_url": cloud_url,
        "cloud_results": cloud_results,
        "message": f"Sao lưu thư mục uploads thành công ({archive_res['file_size_display']}, {archive_res['file_count']} files)!"
    }


def restore_uploads_from_archive(archive_path: Union[str, Path], clean_before_restore: bool = False) -> Dict[str, Any]:
    """
    Khôi phục dữ liệu thư mục uploads từ file nén ZIP.
    """
    archive_p = Path(archive_path)
    if not archive_p.exists():
        return {"success": False, "error": "File sao lưu không tồn tại."}

    uploads_dir = get_uploads_dir()

    if clean_before_restore and uploads_dir.exists():
        for item in uploads_dir.iterdir():
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()

    extracted_count = 0
    with zipfile.ZipFile(archive_p, "r") as zipf:
        zipf.extractall(uploads_dir)
        extracted_count = len(zipf.namelist())

    return {
        "success": True,
        "extracted_count": extracted_count,
        "uploads_dir": str(uploads_dir),
        "message": f"Khôi phục thành công {extracted_count} files vào thư mục uploads."
    }
