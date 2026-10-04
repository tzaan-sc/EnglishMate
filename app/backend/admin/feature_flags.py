from functools import wraps
from flask import abort, current_app, flash, jsonify, redirect, request, url_for
from flask_login import current_user
from app.extensions import db
from .models import SystemConfig
from .utils import log_audit_action


DEFAULT_FEATURE_FLAGS = {
    "ARCADE_GAMES": {
        "name": "Sảnh Trò Chơi Arcade (Learning Games)",
        "description": "Cho phép học viên truy cập sảnh trò chơi luyện từ vựng và câu hỏi (Matching, Typing, Speed Quiz, Listening Rush).",
        "category": "LEARNING_GAMES",
        "default": True,
        "icon": "ph-game-controller"
    },
    "AI_GRADING": {
        "name": "Hệ Thống Chấm Điểm Tự Động AI (Speaking & Essay)",
        "description": "Kích hoạt pipeline AI Speech-to-Text và LLM để tự động chấm bài viết luận Task 1/2 và bài thi nói Speaking.",
        "category": "AI_SYSTEM",
        "default": True,
        "icon": "ph-sparkle"
    },
    "USER_REGISTRATION": {
        "name": "Mở Cổng Đăng Ký Tài Khoản Mới (User Registration)",
        "description": "Cho phép người dùng tự do đăng ký tài khoản thành viên mới trên hệ thống qua form /auth/register.",
        "category": "USER_SECURITY",
        "default": True,
        "icon": "ph-user-plus"
    },
    "BADGE_SHARING": {
        "name": "Chia Sẻ Huy Hiệu & Thành Tích (Badge Sharing)",
        "description": "Cho phép học viên tải ảnh huy hiệu và chia sẻ trực tiếp lên các nền tảng mạng xã hội Facebook, Twitter, Zalo.",
        "category": "COMMUNITY_ENGAGEMENT",
        "default": True,
        "icon": "ph-share-network"
    },
    "AUDIO_ACCENT_SELECTION": {
        "name": "Lựa Chọn Giọng Đọc Đa Vùng Miền (US/UK/AU Accent)",
        "description": "Cho phép học viên tùy chọn phát âm giọng Anh-Mỹ (US), Anh-Anh (UK), hoặc Anh-Úc (AU) trong bài học.",
        "category": "LEARNING_GAMES",
        "default": True,
        "icon": "ph-speaker-high"
    },
    "LEADERBOARD": {
        "name": "Bảng Xếp Hạng Học Tập (Gamification Leaderboard)",
        "description": "Hiển thị bảng xếp hạng đua top điểm kinh nghiệm XP tuần và tháng trên toàn hệ thống.",
        "category": "COMMUNITY_ENGAGEMENT",
        "default": True,
        "icon": "ph-trophy"
    },
    "DAILY_GOAL_REMINDERS": {
        "name": "Nhắc Nhở Mục Tiêu Hàng Ngày (Daily Goal Reminders)",
        "description": "Tự động gửi email thông báo và popup nhắc nhở học viên hoàn thành mục tiêu học tập trước 23:59 mỗi ngày.",
        "category": "COMMUNITY_ENGAGEMENT",
        "default": True,
        "icon": "ph-bell-ringing"
    }
}

CATEGORIES_META = {
    "LEARNING_GAMES": {"title": "Học Tập & Trò Chơi", "badge_class": "bg-primary-subtle text-primary border-primary-subtle"},
    "AI_SYSTEM": {"title": "Trí Tuệ Nhân Tạo (AI)", "badge_class": "bg-purple-subtle text-purple border-purple-subtle"},
    "USER_SECURITY": {"title": "Người Dùng & Bảo Mật", "badge_class": "bg-danger-subtle text-danger border-danger-subtle"},
    "COMMUNITY_ENGAGEMENT": {"title": "Tương Tác & Gamification", "badge_class": "bg-success-subtle text-success border-success-subtle"},
    "GENERAL": {"title": "Chung", "badge_class": "bg-secondary-subtle text-secondary border-secondary-subtle"}
}


def is_feature_enabled(key: str, default: bool = True) -> bool:
    """Kiểm tra xem một tính năng (Feature Flag) có đang được bật hay không."""
    if not key:
        return default
    normalized_key = key.strip().upper()
    fallback_default = DEFAULT_FEATURE_FLAGS.get(normalized_key, {}).get("default", default)
    return SystemConfig.is_feature_enabled(normalized_key, default=fallback_default)


def get_all_feature_flags() -> list[dict]:
    """Lấy danh sách tất cả các feature flags trên hệ thống, kết hợp dữ liệu DB và mặc định."""
    try:
        db_configs = {c.key.upper(): c for c in SystemConfig.query.all()}
    except Exception:
        db_configs = {}

    flags = []
    # Merge default definitions
    for key, meta in DEFAULT_FEATURE_FLAGS.items():
        db_item = db_configs.get(key)
        is_active = db_item.is_active if db_item else meta["default"]
        updated_at = db_item.updated_at if db_item else None
        description = db_item.description if (db_item and db_item.description) else meta["description"]
        category = db_item.category if (db_item and db_item.category) else meta["category"]

        flags.append({
            "key": key,
            "name": meta["name"],
            "description": description,
            "category": category,
            "category_title": CATEGORIES_META.get(category, {}).get("title", category),
            "category_badge": CATEGORIES_META.get(category, {}).get("badge_class", "bg-light text-dark"),
            "icon": meta.get("icon", "ph-toggle-right"),
            "is_active": is_active,
            "updated_at": updated_at.strftime("%d/%m/%Y %H:%M") if updated_at else "Mặc định hệ thống"
        })

    # Include any custom flags created directly in DB
    for key, item in db_configs.items():
        if key not in DEFAULT_FEATURE_FLAGS:
            flags.append({
                "key": key,
                "name": item.description or key,
                "description": item.description or f"Tính năng tùy chỉnh {key}",
                "category": item.category or "GENERAL",
                "category_title": CATEGORIES_META.get(item.category or "GENERAL", {}).get("title", item.category or "GENERAL"),
                "category_badge": CATEGORIES_META.get(item.category or "GENERAL", {}).get("badge_class", "bg-light text-dark"),
                "icon": "ph-sliders",
                "is_active": item.is_active,
                "updated_at": item.updated_at.strftime("%d/%m/%Y %H:%M") if item.updated_at else "---"
            })

    return flags


def set_feature_flag(key: str, is_active: bool, admin_id: int = None, description: str = None) -> dict:
    """Cập nhật trạng thái Bật/Tắt của một Feature Flag."""
    normalized_key = key.strip().upper()
    meta = DEFAULT_FEATURE_FLAGS.get(normalized_key, {})
    desc = description or meta.get("description", f"Feature flag for {normalized_key}")
    cat = meta.get("category", "GENERAL")

    config = SystemConfig.set_feature_status(
        key=normalized_key,
        is_active=bool(is_active),
        description=desc,
        category=cat
    )

    act_str = "BẬT" if is_active else "TẮT"
    feature_name = meta.get("name", normalized_key)

    if admin_id:
        try:
            log_audit_action(
                admin_id,
                "TOGGLE_FEATURE_FLAG",
                "SystemConfig",
                str(config.id),
                f"{act_str} tính năng '{feature_name}' ({normalized_key})"
            )
        except Exception:
            pass

    return {
        "success": True,
        "key": normalized_key,
        "is_active": config.is_active,
        "name": feature_name,
        "message": f"Đã {act_str.lower()} tính năng '{feature_name}' thành công."
    }


def feature_flag_required(feature_key: str, redirect_endpoint: str = "main.dashboard", error_message: str = None):
    """
    Decorator bảo vệ route: chặn người dùng nếu tính năng bị Admin tắt trong Feature Flags.
    
    :param feature_key: Tên cờ tính năng (ví dụ: 'ARCADE_GAMES', 'AI_GRADING', 'USER_REGISTRATION')
    :param redirect_endpoint: Endpoint chuyển hướng nếu bị chặn (cho request web HTML)
    :param error_message: Thông báo lỗi tùy biến
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not is_feature_enabled(feature_key):
                # Bypass check for system Admin
                if current_user.is_authenticated and (getattr(current_user, "is_admin", False) or getattr(current_user, "role", "") == "ADMIN"):
                    return f(*args, **kwargs)

                meta = DEFAULT_FEATURE_FLAGS.get(feature_key.upper(), {})
                feat_name = meta.get("name", feature_key)
                msg = error_message or f"Tính năng '{feat_name}' hiện đang tạm đóng bởi Quản trị viên để nâng cấp hoặc bảo trì."

                if request.is_json or request.path.startswith("/api/"):
                    return jsonify({
                        "error": "feature_disabled",
                        "feature": feature_key,
                        "message": msg
                    }), 403

                flash(msg, "warning")
                try:
                    target_url = url_for(redirect_endpoint) if redirect_endpoint else (request.referrer or url_for("main.dashboard"))
                except Exception:
                    try:
                        target_url = url_for("main.dashboard")
                    except Exception:
                        target_url = "/"
                return redirect(target_url)
            return f(*args, **kwargs)
        return decorated_function
    return decorator
