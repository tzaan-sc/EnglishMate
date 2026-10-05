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


@bp.get("/system/backup")
@bp.get("/backup")
@admin_required
def backup_settings():
    """Trang giao diện quản trị Cài đặt và Quản lý sao lưu CSDL (Database Backup Settings)."""
    backups = DatabaseBackup.query.order_by(DatabaseBackup.created_at.desc()).all()
    stats = get_backup_stats()
    settings = get_backup_settings()

    return render_template(
        "admin/backup_settings.html",
        backups=backups,
        stats=stats,
        settings=settings
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




