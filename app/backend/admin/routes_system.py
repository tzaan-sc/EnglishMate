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
