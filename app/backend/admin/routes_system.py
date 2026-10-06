from flask import render_template, request, jsonify, flash, redirect, url_for, send_file, abort
from flask_login import current_user
from . import bp
from .utils import admin_required, log_audit_action
from .feature_flags import get_all_feature_flags, set_feature_flag, CATEGORIES_META, DEFAULT_FEATURE_FLAGS


@bp.get("/system/feature-flags")
@bp.get("/feature-flags")
@admin_required
def feature_flags():
    """Trang quản trị Bật/Tắt các tính năng hệ thống trong thời gian thực (Feature Flags)."""
    flags = get_all_feature_flags()
    
    # Group flags by category
    grouped_flags = {}
    for cat_key, cat_info in CATEGORIES_META.items():
        cat_items = [f for f in flags if f["category"] == cat_key]
        if cat_items:
            grouped_flags[cat_key] = {
                "title": cat_info["title"],
                "badge_class": cat_info["badge_class"],
                "flags": cat_items
            }

    total_flags = len(flags)
    active_flags = sum(1 for f in flags if f["is_active"])

    return render_template(
        "admin/feature_flags.html",
        flags=flags,
        grouped_flags=grouped_flags,
        total_flags=total_flags,
        active_flags=active_flags
    )


@bp.post("/system/feature-flags/<feature_key>/toggle")
@admin_required
def toggle_feature_flag(feature_key):
    """API chuyển đổi trạng thái Bật/Tắt của một Feature Flag qua AJAX hoặc Form."""
    data = request.get_json(silent=True) or request.form
    raw_val = data.get("is_active") if "is_active" in data else data.get("status")
    
    if raw_val is not None:
        if isinstance(raw_val, bool):
            is_active = raw_val
        else:
            is_active = str(raw_val).strip().lower() in ("1", "true", "on", "yes")
    else:
        # Toggle current state if not specified
        from .feature_flags import is_feature_enabled
        is_active = not is_feature_enabled(feature_key)

    res = set_feature_flag(
        key=feature_key,
        is_active=is_active,
        admin_id=current_user.id
    )

    if request.is_json:
        return jsonify(res)

    flash(res["message"], "success")
    return redirect(url_for("admin.feature_flags"))


@bp.post("/system/feature-flags/bulk")
@admin_required
def bulk_update_feature_flags():
    """Cập nhật nhiều Feature Flags cùng lúc từ Form Quản trị."""
    data = request.get_json(silent=True) or request.form
    flags_data = data.get("flags") or {}
    
    updated = []
    if isinstance(flags_data, dict):
        for key, is_active in flags_data.items():
            active_bool = is_active if isinstance(is_active, bool) else str(is_active).lower() in ("true", "1", "on")
            r = set_feature_flag(key, active_bool, admin_id=current_user.id)
            updated.append(r)

    return jsonify({
        "success": True,
        "updated_count": len(updated),
        "message": f"Đã cập nhật {len(updated)} tính năng thành công."
    })


# ---------------------------------------------------------------------------
# SYSTEM LIMITS & RESOURCE THRESHOLDS ROUTES
# ---------------------------------------------------------------------------
from .system_limits import (
    get_all_system_limits,
    get_grouped_system_limits,
    set_system_limit,
    bulk_update_system_limits,
    reset_system_limits,
    SYSTEM_LIMITS_METADATA,
    LIMIT_CATEGORIES,
)


@bp.get("/system/limits")
@bp.get("/limits")
@admin_required
def system_limits():
    """Trang giao diện quản trị cấu hình các giới hạn hệ thống (System Limits)."""
    limits = get_all_system_limits()
    grouped_limits = get_grouped_system_limits()
    total_limits = len(limits)
    customized_count = sum(1 for lim in limits if lim["is_customized"])

    return render_template(
        "admin/system_limits.html",
        limits=limits,
        grouped_limits=grouped_limits,
        total_limits=total_limits,
        customized_count=customized_count,
    )


@bp.post("/system/limits")
@admin_required
def update_system_limits():
    """Cập nhật các thông số giới hạn hệ thống qua Form hoặc AJAX."""
    data = request.get_json(silent=True) or request.form.to_dict()
    
    # Filter only relevant limit keys
    limits_to_update = {}
    for key in SYSTEM_LIMITS_METADATA:
        if key in data:
            limits_to_update[key] = data[key]

    is_all_success, success_msgs, error_msgs = bulk_update_system_limits(
        limits_to_update,
        admin_id=current_user.id
    )

    if request.is_json:
        return jsonify({
            "success": is_all_success,
            "success_count": len(success_msgs),
            "error_count": len(error_msgs),
            "success_messages": success_msgs,
            "error_messages": error_msgs,
            "message": "Cập nhật giới hạn hệ thống thành công." if is_all_success else "Có lỗi xảy ra khi cập nhật giới hạn.",
        })

    if error_msgs:
        for err in error_msgs:
            flash(err, "danger")
    if success_msgs:
        flash(f"Đã cập nhật thành công {len(success_msgs)} giới hạn hệ thống!", "success")

    return redirect(url_for("admin.system_limits"))


@bp.post("/system/limits/<limit_key>")
@admin_required
def update_single_system_limit(limit_key):
    """Cập nhật một thông số giới hạn đơn lẻ qua AJAX."""
    data = request.get_json(silent=True) or request.form
    val = data.get("value")
    
    res = set_system_limit(limit_key, val, admin_id=current_user.id)
    if request.is_json:
        return jsonify(res)

    if res["success"]:
        flash(res["message"], "success")
    else:
        flash(res.get("error", "Lỗi không xác định"), "danger")

    return redirect(url_for("admin.system_limits"))


@bp.post("/system/limits/reset")
@admin_required
def reset_all_system_limits():
    """Khôi phục toàn bộ các giới hạn hệ thống về mặc định."""
    res = reset_system_limits(admin_id=current_user.id)
    if request.is_json:
        return jsonify(res)

    flash(res["message"], "info")
    return redirect(url_for("admin.system_limits"))


# ---------------------------------------------------------------------------
# PERFORMANCE SETTINGS & CACHE CONFIGURATION ROUTES
# ---------------------------------------------------------------------------
from .performance_settings import (
    get_all_performance_settings,
    get_grouped_performance_settings,
    set_performance_setting,
    bulk_update_performance_settings,
    reset_performance_settings,
    PERFORMANCE_SETTINGS_METADATA,
    PERFORMANCE_CATEGORIES,
)


@bp.get("/system/performance")
@bp.get("/performance")
@admin_required
def performance_settings():
    """Trang giao diện quản trị cấu hình thông số hiệu năng, phân trang và bộ nhớ đệm (Performance Settings)."""
    settings = get_all_performance_settings()
    grouped_settings = get_grouped_performance_settings()
    total_settings = len(settings)
    customized_count = sum(1 for s in settings if s["is_customized"])

    return render_template(
        "admin/performance_settings.html",
        settings=settings,
        grouped_settings=grouped_settings,
        total_settings=total_settings,
        customized_count=customized_count,
    )


@bp.post("/system/performance")
@admin_required
def update_performance_settings():
    """Cập nhật các thông số hiệu năng qua Form hoặc AJAX."""
    data = request.get_json(silent=True) or request.form.to_dict()

    settings_to_update = {}
    for key in PERFORMANCE_SETTINGS_METADATA:
        if key in data:
            settings_to_update[key] = data[key]

    is_all_success, success_msgs, error_msgs = bulk_update_performance_settings(
        settings_to_update,
        admin_id=current_user.id
    )

    if request.is_json:
        return jsonify({
            "success": is_all_success,
            "success_count": len(success_msgs),
            "error_count": len(error_msgs),
            "success_messages": success_msgs,
            "error_messages": error_msgs,
            "message": "Cập nhật thông số hiệu năng thành công." if is_all_success else "Có lỗi xảy ra khi cập nhật hiệu năng.",
        })

    if error_msgs:
        for err in error_msgs:
            flash(err, "danger")
    if success_msgs:
        flash(f"Đã cập nhật thành công {len(success_msgs)} thông số hiệu năng!", "success")

    return redirect(url_for("admin.performance_settings"))


@bp.post("/system/performance/<setting_key>")
@admin_required
def update_single_performance_setting(setting_key):
    """Cập nhật một thông số hiệu năng đơn lẻ qua AJAX."""
    data = request.get_json(silent=True) or request.form
    val = data.get("value")

    res = set_performance_setting(setting_key, val, admin_id=current_user.id)
    if request.is_json:
        return jsonify(res)

    if res["success"]:
        flash(res["message"], "success")
    else:
        flash(res.get("error", "Lỗi không xác định"), "danger")

    return redirect(url_for("admin.performance_settings"))


@bp.post("/system/performance/reset")
@admin_required
def reset_all_performance_settings():
    """Khôi phục toàn bộ các thông số hiệu năng về mặc định."""
    res = reset_performance_settings(admin_id=current_user.id)
    if request.is_json:
        return jsonify(res)

    flash(res["message"], "info")
    return redirect(url_for("admin.performance_settings"))


# ---------------------------------------------------------------------------
# DATABASE BACKUP & RESTORE / RETENTION CONFIGURATION ROUTES
# ---------------------------------------------------------------------------
import os
from .models import DatabaseBackup
from .backup_service import (
    get_backup_settings,
    save_backup_settings,
    get_backup_stats,
    create_database_backup,
    cleanup_old_backups,
    delete_backup,
)
from .file_backup_service import (
    get_uploads_stats,
    get_cloud_storage_settings,
    save_cloud_storage_settings,
    backup_uploads_to_cloud,
    create_uploads_archive,
)
from ...utils.media_processor import compress_image, normalize_audio_volume, crop_and_resize_square


@bp.get("/system/backup")
@bp.get("/backup")
@admin_required
def backup_settings():
    """Trang giao diện quản trị Cài đặt và Quản lý sao lưu CSDL & File Uploads (Backup Settings)."""
    backups = DatabaseBackup.query.order_by(DatabaseBackup.created_at.desc()).all()
    stats = get_backup_stats()
    settings = get_backup_settings()
    uploads_stats = get_uploads_stats()

    return render_template(
        "admin/backup_settings.html",
        backups=backups,
        stats=stats,
        settings=settings,
        uploads_stats=uploads_stats
    )


@bp.post("/system/backup/create")
@bp.post("/backup/create")
@admin_required
def create_backup_route():
    """Thực hiện tạo bản sao lưu CSDL ngay lập tức (Backup Now)."""
    data = request.get_json(silent=True) or request.form
    backup_type = data.get("backup_type", "MANUAL")
    notes = data.get("notes")

    res = create_database_backup(
        backup_type=backup_type,
        admin_id=current_user.id,
        notes=notes
    )

    if request.is_json:
        return jsonify(res)

    if res["success"]:
        flash(res["message"], "success")
    else:
        flash(res.get("error", "Lỗi tạo bản sao lưu CSDL."), "danger")

    return redirect(url_for("admin.backup_settings"))


@bp.post("/system/backup/settings")
@bp.post("/backup/settings")
@admin_required
def update_backup_settings_route():
    """Cập nhật cấu hình tần suất tự động sao lưu và số lượng bản sao lưu giữ lại."""
    data = request.get_json(silent=True) or request.form.to_dict()

    res = save_backup_settings(data, admin_id=current_user.id)

    if request.is_json:
        return jsonify(res)

    flash(res["message"], "success")
    return redirect(url_for("admin.backup_settings"))


@bp.get("/system/backup/download/<int:backup_id>")
@bp.get("/backup/download/<int:backup_id>")
@admin_required
def download_backup_route(backup_id):
    """Tải file sao lưu CSDL về máy an toàn."""
    from ...extensions import db
    backup = db.session.get(DatabaseBackup, backup_id)
    if not backup:
        flash("Không tìm thấy bản sao lưu yêu cầu.", "danger")
        return redirect(url_for("admin.backup_settings"))

    if not backup.file_path or not os.path.exists(backup.file_path):
        flash(f"File sao lưu vật lý '{backup.filename}' không tồn tại trên máy chủ.", "danger")
        return redirect(url_for("admin.backup_settings"))

    log_audit_action(
        user_id=current_user.id,
        action="DOWNLOAD_DATABASE_BACKUP",
        target_type="DATABASE_BACKUP",
        target_id=str(backup.id),
        details=f"Tải xuống file sao lưu CSDL: {backup.filename}"
    )

    return send_file(
        backup.file_path,
        as_attachment=True,
        download_name=backup.filename
    )


@bp.post("/system/backup/delete/<int:backup_id>")
@bp.post("/backup/delete/<int:backup_id>")
@admin_required
def delete_backup_route(backup_id):
    """Xóa một bản sao lưu CSDL khỏi hệ thống."""
    res = delete_backup(backup_id, admin_id=current_user.id)

    if request.is_json:
        return jsonify(res)

    if res["success"]:
        flash(res["message"], "success")
    else:
        flash(res.get("error", "Lỗi khi xóa bản sao lưu."), "danger")

    return redirect(url_for("admin.backup_settings"))


@bp.post("/system/backup/cleanup")
@bp.post("/backup/cleanup")
@admin_required
def cleanup_backups_route():
    """Dọn dẹp các bản sao lưu cũ theo chính sách Retention Count."""
    deleted_count = cleanup_old_backups()
    msg = f"Đã dọn dẹp {deleted_count} bản sao lưu cũ thành công." if deleted_count > 0 else "Không có bản sao lưu nào vượt quá số lượng lưu trữ cho phép."

    if request.is_json:
        return jsonify({"success": True, "deleted_count": deleted_count, "message": msg})

    flash(msg, "info")
    return redirect(url_for("admin.backup_settings"))


@bp.post("/system/backup/uploads")
@bp.post("/backup/uploads")
@admin_required
def backup_uploads_route():
    """Sao lưu thư mục static/uploads/ lên Cloud Storage (S3 / Cloudinary / Local Zip)."""
    data = request.get_json(silent=True) or request.form
    provider = data.get("provider", "LOCAL").strip().upper()
    notes = data.get("notes")

    res = backup_uploads_to_cloud(
        provider=provider,
        admin_id=current_user.id,
        notes=notes
    )

    if request.is_json:
        return jsonify(res)

    if res.get("success"):
        flash(res["message"], "success")
    else:
        flash(res.get("error", "Lỗi sao lưu thư mục uploads."), "danger")

    return redirect(url_for("admin.backup_settings"))


@bp.get("/system/backup/uploads/stats")
@bp.get("/backup/uploads/stats")
@admin_required
def get_uploads_stats_route():
    """Lấy số liệu thống kê chi tiết thư mục static/uploads/ và trạng thái cloud."""
    stats = get_uploads_stats()
    return jsonify({"success": True, "stats": stats})


@bp.post("/system/backup/cloud-settings")
@bp.post("/backup/cloud-settings")
@admin_required
def update_cloud_settings_route():
    """Cập nhật các thông số kết nối Cloud Storage (AWS S3, Cloudinary)."""
    data = request.get_json(silent=True) or request.form.to_dict()
    res = save_cloud_storage_settings(data, admin_id=current_user.id)

    if request.is_json:
        return jsonify(res)

    flash(res["message"], "success")
    return redirect(url_for("admin.backup_settings"))


@bp.post("/system/media/compress-image")
@bp.post("/media/compress-image")
@admin_required
def compress_image_api():
    """API nén ảnh theo yêu cầu với Pillow."""
    file = request.files.get("image")
    if not file:
        return jsonify({"success": False, "error": "Vui lòng chọn file ảnh cần nén."}), 400

    quality = request.form.get("quality", type=int) or 85
    max_w = request.form.get("max_width", type=int) or 1920
    max_h = request.form.get("max_height", type=int) or 1920
    fmt = request.form.get("format") or None

    try:
        res = compress_image(
            input_source=file,
            max_width=max_w,
            max_height=max_h,
            quality=quality,
            output_format=fmt
        )
        return jsonify({
            "success": True,
            "original_size": res["original_size"],
            "compressed_size": res["compressed_size"],
            "saved_bytes": res["saved_bytes"],
            "reduction_percent": res["reduction_percent"],
            "width": res["width"],
            "height": res["height"],
            "format": res["format"]
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@bp.post("/system/media/normalize-audio")
@bp.post("/media/normalize-audio")
@admin_required
def normalize_audio_api():
    """API chuẩn hóa âm lượng file audio."""
    file = request.files.get("audio")
    if not file:
        return jsonify({"success": False, "error": "Vui lòng chọn file âm thanh cần chuẩn hóa."}), 400

    target_dbfs = request.form.get("target_dbfs", type=float) or -3.0

    try:
        res = normalize_audio_volume(
            input_audio=file,
            target_dbfs=target_dbfs
        )
        return jsonify({
            "success": True,
            "engine": res["engine"],
            "original_max_dbfs": res["original_max_dbfs"],
            "target_dbfs": res["target_dbfs"],
            "gain_applied_db": res["gain_applied_db"],
            "duration_seconds": res["duration_seconds"],
            "channels": res["channels"],
            "sample_rate": res["sample_rate"],
            "output_size": res["output_size"]
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ---------------------------------------------------------------------------
# HTTP SECURITY HEADERS CONFIGURATION ROUTES
# ---------------------------------------------------------------------------
from .security_headers import get_security_headers_config, save_security_headers_config


@bp.get("/system/security-headers")
@bp.get("/security-headers")
@admin_required
def get_security_headers_route():
    """Lấy thông tin cấu hình HTTP Security Headers hiện tại."""
    cfg = get_security_headers_config()
    return jsonify({"success": True, "config": cfg})


@bp.post("/system/security-headers")
@bp.post("/security-headers")
@admin_required
def update_security_headers_route():
    """Cập nhật các thông số bảo vệ HTTP Security Headers."""
    data = request.get_json(silent=True) or request.form.to_dict()
    res = save_security_headers_config(data, admin_id=current_user.id)
    if request.is_json:
        return jsonify(res)
    flash(res["message"], "success")
    return redirect(url_for("admin.dashboard"))


# ---------------------------------------------------------------------------
# PERMISSION CACHE MANAGEMENT ROUTES (MỤC 11.2)
# ---------------------------------------------------------------------------
from .permission_cache import get_permission_cache_stats, invalidate_permission_cache


@bp.get("/system/permission-cache/stats")
@bp.get("/system/permissions/cache-stats")
@admin_required
def get_permission_cache_stats_route():
    """Lấy thông tin thống kê trạng thái bộ nhớ đệm quyền hạn người dùng."""
    stats = get_permission_cache_stats()
    return jsonify({"success": True, "stats": stats})


@bp.post("/system/permission-cache/clear")
@bp.post("/system/permissions/clear-cache")
@admin_required
def clear_permission_cache_route():
    """Xóa toàn bộ hoặc một phần bộ nhớ đệm quyền hạn người dùng."""
    data = request.get_json(silent=True) or request.form
    target_user_id = data.get("user_id")
    
    user_id = None
    if target_user_id is not None and str(target_user_id).isdigit():
        user_id = int(target_user_id)

    cleared_count = invalidate_permission_cache(user_id=user_id)
    
    target_desc = f"cho User #{user_id}" if user_id else "cho tất cả người dùng"
    log_audit_action(
        user_id=current_user.id,
        action="CLEAR_PERMISSION_CACHE",
        target_type="SYSTEM_CACHE",
        target_id=str(user_id) if user_id else None,
        details=f"Xóa bộ nhớ đệm quyền hạn {target_desc} ({cleared_count} bản ghi)"
    )

    msg = f"Đã xóa bộ nhớ đệm quyền hạn {target_desc} ({cleared_count} bản ghi)."
    if request.is_json:
        return jsonify({"success": True, "cleared_count": cleared_count, "message": msg})

    flash(msg, "success")
    return redirect(url_for("admin.users", tab="roles"))


# ---------------------------------------------------------------------------
# DATA MASKING & SENSITIVE DATA PROTECTION ROUTES (MỤC 11.3)
# ---------------------------------------------------------------------------
from .data_masking import (
    mask_email,
    mask_ip_address,
    mask_phone,
    mask_text,
    mask_sensitive_dict,
    is_data_masking_enabled,
)


@bp.get("/system/data-masking/preview")
@bp.get("/system/masking/preview")
@admin_required
def preview_data_masking_route():
    """Trả về bản xem trước dữ liệu mẫu sau khi áp dụng các bộ lọc che giấu dữ liệu."""
    sample_email = request.args.get("email", "student.english@example.com")
    sample_ip = request.args.get("ip", "192.168.1.105")
    sample_phone = request.args.get("phone", "0912345678")

    return jsonify({
        "success": True,
        "is_masking_enabled": is_data_masking_enabled(),
        "original": {
            "email": sample_email,
            "ip": sample_ip,
            "phone": sample_phone,
        },
        "masked": {
            "email": mask_email(sample_email),
            "ip_medium": mask_ip_address(sample_ip, mask_level="medium"),
            "ip_low": mask_ip_address(sample_ip, mask_level="low"),
            "ip_high": mask_ip_address(sample_ip, mask_level="high"),
            "phone": mask_phone(sample_phone),
        }
    })


@bp.post("/system/data-masking/mask")
@bp.post("/system/masking/mask")
@admin_required
def mask_payload_route():
    """API tiện ích che giấu các trường nhạy cảm trong Dictionary/JSON payload."""
    data = request.get_json(silent=True) or request.form.to_dict()
    masked = mask_sensitive_dict(data)
    return jsonify({"success": True, "masked_data": masked})


# ---------------------------------------------------------------------------
# DATA RECOVERY, RETENTION & PURGING ROUTES (MỤC 11.4 - 11.7)
# ---------------------------------------------------------------------------
from .backup_service import restore_database_backup
from .data_lifecycle_service import (
    get_inactive_users_stats,
    purge_soft_deleted_users,
    run_data_lifecycle_maintenance_job,
)


@bp.post("/system/backup/restore/<int:backup_id>")
@bp.post("/backup/restore/<int:backup_id>")
@admin_required
def restore_backup_route(backup_id):
    """Kịch bản khôi phục CSDL an toàn từ một bản sao lưu (Data Recovery)."""
    res = restore_database_backup(backup_id=backup_id, admin_id=current_user.id)

    if request.is_json:
        return jsonify(res)

    if res["success"]:
        flash(res["message"], "success")
    else:
        flash(res.get("error", "Lỗi trong quá trình khôi phục CSDL."), "danger")

    return redirect(url_for("admin.backup_settings"))


@bp.get("/system/data-lifecycle/stats")
@bp.get("/system/retention/stats")
@admin_required
def data_lifecycle_stats_route():
    """Lấy số liệu thống kê tài khoản không hoạt động và tài khoản chờ dọn dẹp."""
    days = request.args.get("days", type=int)
    stats = get_inactive_users_stats(days=days)
    return jsonify({"success": True, "stats": stats})


@bp.post("/system/data-lifecycle/purge")
@bp.post("/system/retention/purge")
@admin_required
def purge_soft_deleted_users_route():
    """Dọn dẹp vĩnh viễn (Hard Purge) các tài khoản soft-delete đã quá hạn."""
    data = request.get_json(silent=True) or request.form
    days = data.get("days")
    dry_run = data.get("dry_run", False)
    if isinstance(dry_run, str):
        dry_run = dry_run.lower() in ("true", "1", "yes")

    if days is not None and str(days).isdigit():
        days = int(days)
    else:
        days = None

    res = purge_soft_deleted_users(days=days, dry_run=dry_run, admin_id=current_user.id)

    if request.is_json:
        return jsonify(res)

    flash(res["message"], "success" if res["success"] else "danger")
    return redirect(url_for("admin.users", tab="users"))


@bp.post("/system/data-lifecycle/maintenance")
@admin_required
def run_data_maintenance_route():
    """Chạy tổng thể quy trình bảo trì vòng đời dữ liệu hệ thống."""
    res = run_data_lifecycle_maintenance_job(admin_id=current_user.id)
    return jsonify(res)


# ---------------------------------------------------------------------------
# NETWORK SECURITY & FIREWALL MANAGEMENT ROUTES (MỤC 11.8 - 11.15)
# ---------------------------------------------------------------------------
from .models import SystemConfig
from .network_security import (
    get_network_monitoring_stats,
    add_ip_blacklist,
    remove_ip_blacklist,
    add_admin_ip_whitelist,
    remove_admin_ip_whitelist,
    generate_nginx_ssl_config,
    generate_ufw_firewall_script,
    get_cloudflare_ddos_recommendations,
    get_cors_allowed_origins,
    is_https_enforced,
    _BLACKLISTED_IPS,
    _ADMIN_WHITELISTED_IPS,
)



@bp.get("/system/network-security")
@bp.get("/network-security")
@admin_required
def network_security():
    """Trang giao diện quản trị An ninh mạng, Tường lửa, HTTPS, CORS và Giám sát lưu lượng (Network Security)."""
    stats = get_network_monitoring_stats()
    nginx_config = generate_nginx_ssl_config()
    ufw_script = generate_ufw_firewall_script()
    cloudflare_info = get_cloudflare_ddos_recommendations()

    return render_template(
        "admin/network_security.html",
        stats=stats,
        blacklisted_ips=_BLACKLISTED_IPS,
        whitelisted_ips=_ADMIN_WHITELISTED_IPS,
        nginx_config=nginx_config,
        ufw_script=ufw_script,
        cloudflare_info=cloudflare_info,
    )


@bp.get("/system/network-security/stats")
@bp.get("/network-security/stats")
@admin_required
def network_security_stats_route():
    """API lấy thông số giám sát lưu lượng mạng và kết nối thời gian thực."""
    stats = get_network_monitoring_stats()
    return jsonify({"success": True, "stats": stats})


@bp.post("/system/network-security/ip-rules")
@bp.post("/network-security/ip-rules")
@admin_required
def manage_ip_rules_route():
    """Thêm hoặc gỡ bỏ quy tắc IP Blacklist / Whitelist."""
    data = request.get_json(silent=True) or request.form
    action = data.get("action", "").strip().lower()
    list_type = data.get("list_type", "").strip().lower()
    if list_type and action in ("add", "remove"):
        action = f"{action}_{list_type}"

    ip = data.get("ip", "").strip()
    reason = data.get("reason", "Quản trị viên cấu hình")
    duration = data.get("duration_minutes")
    duration_minutes = int(duration) if duration and str(duration).isdigit() else None

    if not ip:
        return jsonify({"success": False, "error": "Vui lòng nhập địa chỉ IP hợp lệ."}), 400

    if action == "add_blacklist":
        res = add_ip_blacklist(ip, reason=reason, duration_minutes=duration_minutes, admin_id=current_user.id)
    elif action == "remove_blacklist":
        res = remove_ip_blacklist(ip, admin_id=current_user.id)
    elif action == "add_whitelist":
        res = add_admin_ip_whitelist(ip, admin_id=current_user.id)
    elif action == "remove_whitelist":
        res = remove_admin_ip_whitelist(ip, admin_id=current_user.id)
    else:
        return jsonify({"success": False, "error": "Hành động không hợp lệ."}), 400

    if request.is_json:
        return jsonify(res)

    flash(res.get("message", "Đã cập nhật quy tắc IP thành công."), "success" if res.get("success") else "danger")
    return redirect(url_for("admin.network_security"))


@bp.post("/system/network-security/settings")
@bp.post("/network-security/settings")
@admin_required
def update_network_security_settings_route():
    """Cập nhật cấu hình Bắt buộc HTTPS, CORS và Admin IP Whitelist."""
    data = request.get_json(silent=True) or request.form.to_dict()

    https_val = data.get("HTTPS_ENFORCEMENT_ENABLED", data.get("https_enforcement"))
    if https_val is not None:
        is_https = https_val if isinstance(https_val, bool) else str(https_val).lower() in ("true", "1", "on", "yes")
        SystemConfig.set_feature_status("HTTPS_ENFORCEMENT_ENABLED", is_https, description="Tự động chuyển hướng HTTP sang HTTPS", category="NETWORK")

    admin_wl_val = data.get("ADMIN_IP_WHITELIST_ENABLED", data.get("admin_ip_whitelist_enabled"))
    if admin_wl_val is not None:
        is_wl = admin_wl_val if isinstance(admin_wl_val, bool) else str(admin_wl_val).lower() in ("true", "1", "on", "yes")
        SystemConfig.set_feature_status("ADMIN_IP_WHITELIST_ENABLED", is_wl, description="Kích hoạt kiểm tra Admin IP Whitelist", category="NETWORK")

    cors_val = data.get("CORS_ALLOWED_ORIGINS", data.get("cors_origins"))
    if cors_val is not None:
        origins = str(cors_val).strip()
        SystemConfig.set_config("CORS_ALLOWED_ORIGINS", origins, description="Danh sách domain được phép gọi API (CORS)", category="NETWORK")

    log_audit_action(
        user_id=current_user.id,
        action="UPDATE_NETWORK_SETTINGS",
        target_type="SYSTEM_CONFIG",
        details=f"Cập nhật cấu hình an ninh mạng: {data}"
    )

    if request.is_json:
        return jsonify({"success": True, "message": "Đã lưu cài đặt an ninh mạng thành công!"})

    flash("Đã lưu cài đặt an ninh mạng thành công!", "success")
    return redirect(url_for("admin.network_security"))



@bp.get("/system/network-security/deployment-scripts")
@admin_required
def network_deployment_scripts_route():
    """Trả về các file cấu hình máy chủ Nginx, UFW Firewall và Cloudflare WAF."""
    domain = request.args.get("domain", "englishmate.vn")
    port = request.args.get("port", 5000, type=int)

    return jsonify({
        "success": True,
        "nginx_ssl_config": generate_nginx_ssl_config(domain=domain, app_port=port),
        "ufw_firewall_script": generate_ufw_firewall_script(),
        "cloudflare_ddos_guide": get_cloudflare_ddos_recommendations(),
    })


# ---------------------------------------------------------------------------
# DATABASE MANAGEMENT & AUTOMATION ROUTES (MỤC 12.1 - DATABASE FEATURES)
# ---------------------------------------------------------------------------
from .database_service import (
    get_migration_status,
    run_database_upgrade,
    generate_database_migration,
    get_backup_automation_status,
    check_and_run_auto_backup,
    auto_restore_database,
)


@bp.get("/system/database/status")
@bp.get("/system/migrations/status")
@admin_required
def database_status_route():
    """Lấy thông tin tổng hợp về Database Migrations và Backup Automation."""
    mig_status = get_migration_status()
    auto_backup_status = get_backup_automation_status()

    return jsonify({
        "success": True,
        "migrations": mig_status,
        "auto_backup": auto_backup_status,
    })


@bp.post("/system/database/upgrade")
@bp.post("/system/migrations/upgrade")
@admin_required
def database_upgrade_route():
    """Thực thi nâng cấp CSDL lên phiên bản migration mới nhất (Alembic Upgrade)."""
    data = request.get_json(silent=True) or request.form
    revision = data.get("revision", "head")
    res = run_database_upgrade(revision=revision, admin_id=current_user.id)
    return jsonify(res)


@bp.post("/system/database/migrate")
@bp.post("/system/migrations/generate")
@admin_required
def database_generate_migration_route():
    """Tự động phát hiện thay đổi schema và tạo tệp migration mới."""
    data = request.get_json(silent=True) or request.form
    message = data.get("message", "Auto migration")
    res = generate_database_migration(message=message, admin_id=current_user.id)
    return jsonify(res)


@bp.post("/system/database/auto-backup")
@admin_required
def run_auto_backup_route():
    """Chạy quy trình kiểm tra và tự động sao lưu CSDL theo lịch trình (Backup Automation)."""
    data = request.get_json(silent=True) or request.form
    force = data.get("force", False)
    if isinstance(force, str):
        force = force.lower() in ("true", "1", "yes")

    res = check_and_run_auto_backup(force=force, admin_id=current_user.id)
    return jsonify(res)


@bp.post("/system/database/auto-restore")
@admin_required
def run_auto_restore_route():
    """Tự động phục hồi CSDL từ bản sao lưu gần nhất hoặc theo ID (Restore Automation)."""
    data = request.get_json(silent=True) or request.form
    backup_id = data.get("backup_id")
    use_latest = data.get("use_latest", False)
    if isinstance(use_latest, str):
        use_latest = use_latest.lower() in ("true", "1", "yes")

    if backup_id is not None and str(backup_id).isdigit():
        backup_id = int(backup_id)
    else:
        backup_id = None
        use_latest = True

    res = auto_restore_database(
        backup_id=backup_id,
        use_latest=use_latest,
        admin_id=current_user.id,
    )
    return jsonify(res)


# ---------------------------------------------------------------------------
# EMAIL SYSTEM MANAGEMENT & ANALYTICS ROUTES (MỤC 12.4)
# ---------------------------------------------------------------------------
from .models import EmailLog, EmailTemplate, EmailBounce
from .email_service import (
    init_default_email_templates,
    get_email_analytics,
    enqueue_email,
    send_templated_email,
    process_scheduled_email_queue,
)


@bp.get("/system/email")
@bp.get("/email")
@admin_required
def email_system_dashboard():
    """Giao diện Quản trị Hệ thống Email: Mẫu HTML, Analytics, Hàng đợi & Lịch sử gửi, Bounces."""
    init_default_email_templates()
    templates = EmailTemplate.query.order_by(EmailTemplate.id.asc()).all()
    recent_logs = EmailLog.query.order_by(EmailLog.created_at.desc()).limit(50).all()
    bounces = EmailBounce.query.order_by(EmailBounce.created_at.desc()).all()
    analytics = get_email_analytics(days=30)

    return render_template(
        "admin/email_system.html",
        templates=templates,
        recent_logs=recent_logs,
        bounces=bounces,
        analytics=analytics
    )


@bp.get("/system/email/analytics")
@bp.get("/email/analytics")
@admin_required
def email_analytics_api():
    """API lấy dữ liệu thống kê phân tích hiệu suất email (Open rate, Bounce, timeline)."""
    days = request.args.get("days", default=30, type=int)
    analytics = get_email_analytics(days=days)
    return jsonify({"success": True, "analytics": analytics})


@bp.post("/system/email/templates/<int:template_id>")
@bp.post("/email/templates/<int:template_id>")
@admin_required
def update_email_template_route(template_id):
    """Cập nhật nội dung tiêu đề và mã HTML của mẫu email."""
    tpl = db.session.get(EmailTemplate, template_id)
    if not tpl:
        return jsonify({"success": False, "error": "Mẫu email không tồn tại."}), 404

    data = request.get_json(silent=True) or request.form
    if "subject" in data and data["subject"].strip():
        tpl.subject = data["subject"].strip()
    if "html_content" in data:
        tpl.html_content = data["html_content"]
    if "is_active" in data:
        val = data["is_active"]
        tpl.is_active = val if isinstance(val, bool) else str(val).lower() in ("true", "1", "yes")

    db.session.commit()

    log_audit_action(
        user_id=current_user.id,
        action="UPDATE_EMAIL_TEMPLATE",
        target_type="EMAIL_TEMPLATE",
        target_id=str(tpl.id),
        details=f"Cập nhật mẫu email '{tpl.name}' ({tpl.key})"
    )

    if request.is_json:
        return jsonify({"success": True, "message": f"Đã lưu mẫu email '{tpl.name}' thành công!"})

    flash(f"Đã lưu mẫu email '{tpl.name}' thành công!", "success")
    return redirect(url_for("admin.email_system_dashboard"))


@bp.post("/system/email/templates/preview")
@bp.post("/email/templates/preview")
@admin_required
def preview_email_template_route():
    """Render HTML xem trước của mẫu email với dữ liệu thử nghiệm."""
    data = request.get_json(silent=True) or request.form
    subject_raw = data.get("subject", "")
    html_raw = data.get("html_content", "")
    variables_map = data.get("variables") or {}
    if isinstance(variables_map, str):
        try:
            variables_map = json.loads(variables_map)
        except Exception:
            variables_map = {}

    rendered_subject = subject_raw
    rendered_html = html_raw
    for k, v in variables_map.items():
        rendered_subject = rendered_subject.replace("{{" + f" {k} " + "}}", str(v)).replace("{{" + k + "}}", str(v))
        rendered_html = rendered_html.replace("{{" + f" {k} " + "}}", str(v)).replace("{{" + k + "}}", str(v))

    return jsonify({
        "success": True,
        "subject": rendered_subject,
        "html_content": rendered_html
    })


@bp.post("/system/email/send-test")
@bp.post("/email/send-test")
@admin_required
def send_test_email_route():
    """Gửi email thử nghiệm hoặc hẹn giờ gửi email từ Admin."""
    data = request.get_json(silent=True) or request.form
    to_email = data.get("recipient", "").strip()
    template_key = data.get("template_key", "").strip()
    subject = data.get("subject", "").strip()
    html_content = data.get("html_content", "").strip()
    schedule_iso = data.get("scheduled_at", "").strip()

    if not to_email:
        return jsonify({"success": False, "error": "Vui lòng nhập email người nhận."}), 400

    scheduled_at_dt = None
    if schedule_iso:
        try:
            scheduled_at_dt = datetime.fromisoformat(schedule_iso.replace("Z", "+00:00"))
        except Exception:
            pass

    if template_key:
        context = data.get("context") or {
            "username": "Học viên Test",
            "otp_code": "888999",
            "expire_minutes": 15,
            "reset_url": "https://englishmate.vn/auth/reset-password?token=sample",
            "target_goal": "50 XP",
            "study_url": "https://englishmate.vn/learning/vocabulary",
            "dashboard_url": "https://englishmate.vn/dashboard",
            "title": "Thông báo kiểm thử hệ thống",
            "message_content": "Đây là email kiểm tra tính năng hàng đợi và tracking.",
            "cta_text": "Xem ngay",
            "cta_url": "https://englishmate.vn"
        }
        res = send_templated_email(
            to_email=to_email,
            template_key=template_key,
            context=context,
            scheduled_at=scheduled_at_dt,
            admin_id=current_user.id
        )
    else:
        res = enqueue_email(
            to_email=to_email,
            subject=subject or "[EnglishMate] Test Email",
            html_content=html_content or "<p>Nội dung kiểm tra hệ thống email EnglishMate.</p>",
            email_type="ADMIN_TEST",
            scheduled_at=scheduled_at_dt,
            admin_id=current_user.id
        )

    log_audit_action(
        user_id=current_user.id,
        action="SEND_ADMIN_EMAIL",
        target_type="EMAIL_LOG",
        details=f"Admin gửi email tới {to_email} (Type: {template_key or 'CUSTOM'}, Status: {res.get('status')})"
    )

    if request.is_json:
        return jsonify(res)

    flash("Đã đưa email vào hàng đợi gửi thành công!", "success")
    return redirect(url_for("admin.email_system_dashboard"))


@bp.post("/system/email/process-queue")
@bp.post("/email/process-queue")
@admin_required
def process_email_queue_route():
    """Kích hoạt quét và gửi các email hẹn giờ đến hạn trong hàng đợi."""
    processed = process_scheduled_email_queue()
    msg = f"Đã xử lý gửi {processed} email hẹn giờ thành công." if processed > 0 else "Không có email hẹn giờ nào đến hạn."
    if request.is_json:
        return jsonify({"success": True, "processed_count": processed, "message": msg})
    flash(msg, "info")
    return redirect(url_for("admin.email_system_dashboard"))


@bp.post("/system/email/bounces/delete/<int:bounce_id>")
@bp.post("/email/bounces/delete/<int:bounce_id>")
@admin_required
def delete_email_bounce_route(bounce_id):
    """Gỡ bỏ địa chỉ email khỏi danh sách Bounce để cho phép gửi lại."""
    bounce = db.session.get(EmailBounce, bounce_id)
    if bounce:
        email_str = bounce.email
        db.session.delete(bounce)
        db.session.commit()
        log_audit_action(
            user_id=current_user.id,
            action="UNBLOCK_EMAIL_BOUNCE",
            target_type="EMAIL_BOUNCE",
            target_id=str(bounce_id),
            details=f"Gỡ bỏ email khỏi Bounce blocklist: {email_str}"
        )
    if request.is_json:
        return jsonify({"success": True, "message": "Đã gỡ bỏ email khỏi danh sách chặn Bounce."})
    flash("Đã gỡ bỏ email khỏi danh sách chặn Bounce.", "success")
    return redirect(url_for("admin.email_system_dashboard"))









