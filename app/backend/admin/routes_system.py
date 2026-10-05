from flask import render_template, request, jsonify, flash, redirect, url_for
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


