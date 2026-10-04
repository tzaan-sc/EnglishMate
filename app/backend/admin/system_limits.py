from typing import Any, Dict, List, Optional, Tuple
from app.extensions import db
from .models import SystemConfig
from .utils import log_audit_action


SYSTEM_LIMITS_METADATA: Dict[str, Dict[str, Any]] = {
    "MAX_FAILED_LOGIN_ATTEMPTS": {
        "key": "MAX_FAILED_LOGIN_ATTEMPTS",
        "name": "Số lần đăng nhập sai tối đa",
        "description": "Số lần người dùng được phép nhập sai mật khẩu liên tiếp trước khi tài khoản bị khóa tạm thời.",
        "category": "SECURITY",
        "category_title": "Bảo mật & Đăng nhập",
        "default": 5,
        "min": 3,
        "max": 20,
        "step": 1,
        "unit": "lần",
        "icon": "ph-shield-warning",
        "recommended": 5,
    },
    "LOCKOUT_MINUTES": {
        "key": "LOCKOUT_MINUTES",
        "name": "Thời gian khóa đăng nhập",
        "description": "Thời gian tài khoản bị tạm khóa (tính theo phút) khi vượt quá số lần đăng nhập sai tối đa.",
        "category": "SECURITY",
        "category_title": "Bảo mật & Đăng nhập",
        "default": 15,
        "min": 1,
        "max": 1440,
        "step": 1,
        "unit": "phút",
        "icon": "ph-clock-countdown",
        "recommended": 15,
    },
    "SESSION_TIMEOUT_MINUTES": {
        "key": "SESSION_TIMEOUT_MINUTES",
        "name": "Thời gian hết hạn phiên làm việc (Session Inactivity)",
        "description": "Thời gian không có tương tác người dùng (tính theo phút) trước khi phiên làm việc tự động hết hạn và đăng xuất an toàn.",
        "category": "SESSION",
        "category_title": "Phiên làm việc & Tài nguyên",
        "default": 30,
        "min": 5,
        "max": 10080,
        "step": 5,
        "unit": "phút",
        "icon": "ph-hourglass-high",
        "recommended": 30,
    },
    "MAX_AVATAR_SIZE_MB": {
        "key": "MAX_AVATAR_SIZE_MB",
        "name": "Dung lượng ảnh đại diện tối đa",
        "description": "Giới hạn kích thước file ảnh đại diện (Avatar) được phép tải lên hồ sơ cá nhân (tính theo Megabytes).",
        "category": "STORAGE",
        "category_title": "Lưu trữ & Dung lượng Tải lên",
        "default": 5,
        "min": 1,
        "max": 50,
        "step": 1,
        "unit": "MB",
        "icon": "ph-user-circle",
        "recommended": 5,
    },
    "MAX_UPLOAD_SIZE_MB": {
        "key": "MAX_UPLOAD_SIZE_MB",
        "name": "Dung lượng tệp đính kèm / âm thanh tối đa",
        "description": "Giới hạn kích thước file tải lên bài học, đề thi và các file ghi âm giọng nói (tính theo Megabytes).",
        "category": "STORAGE",
        "category_title": "Lưu trữ & Dung lượng Tải lên",
        "default": 15,
        "min": 1,
        "max": 100,
        "step": 1,
        "unit": "MB",
        "icon": "ph-file-arrow-up",
        "recommended": 15,
    },
}

LIMIT_CATEGORIES = {
    "SECURITY": {
        "title": "Bảo mật & Đăng nhập",
        "description": "Cấu hình số lần đăng nhập sai và thời gian khóa tài khoản bảo vệ chống tấn công brute-force.",
        "icon": "ph-shield-check",
        "badge_class": "bg-danger-subtle text-danger border-danger-subtle",
    },
    "SESSION": {
        "title": "Phiên làm việc & Tài nguyên",
        "description": "Cấu hình thời gian duy trì phiên hoạt động của người dùng.",
        "icon": "ph-timer",
        "badge_class": "bg-primary-subtle text-primary border-primary-subtle",
    },
    "STORAGE": {
        "title": "Lưu trữ & Dung lượng Tải lên",
        "description": "Giới hạn dung lượng tải lên avatar và tệp dữ liệu media.",
        "icon": "ph-hard-drives",
        "badge_class": "bg-success-subtle text-success border-success-subtle",
    },
}


def get_system_limit(key: str, default: Optional[int] = None) -> int:
    """
    Lấy giá trị giới hạn hệ thống hiện tại từ CSDL SystemConfig.
    Nếu chưa được cấu hình, trả về giá trị mặc định từ metadata.
    """
    norm_key = key.strip().upper()
    meta = SYSTEM_LIMITS_METADATA.get(norm_key)
    fallback = default if default is not None else (meta["default"] if meta else 0)
    return SystemConfig.get_int_config(norm_key, default=fallback)


def get_all_system_limits() -> List[Dict[str, Any]]:
    """
    Lấy toàn bộ danh sách các thông số giới hạn hệ thống kèm thông tin cấu hình hiện tại trong DB.
    """
    try:
        db_configs = {c.key.upper(): c for c in SystemConfig.query.all()}
    except Exception:
        db_configs = {}

    limits = []
    for key, meta in SYSTEM_LIMITS_METADATA.items():
        db_item = db_configs.get(key)
        current_val = meta["default"]
        updated_at = None
        is_customized = False

        if db_item and db_item.value is not None:
            try:
                current_val = int(db_item.value)
                is_customized = (current_val != meta["default"])
                updated_at = db_item.updated_at
            except (ValueError, TypeError):
                current_val = meta["default"]

        limits.append({
            "key": key,
            "name": meta["name"],
            "description": meta["description"],
            "category": meta["category"],
            "category_title": meta["category_title"],
            "value": current_val,
            "default": meta["default"],
            "min": meta["min"],
            "max": meta["max"],
            "step": meta["step"],
            "unit": meta["unit"],
            "icon": meta["icon"],
            "recommended": meta["recommended"],
            "is_customized": is_customized,
            "updated_at": updated_at,
        })

    return limits


def get_grouped_system_limits() -> Dict[str, Dict[str, Any]]:
    """
    Nhóm danh sách các giới hạn theo chuyên mục để hiển thị trực quan trên giao diện Admin.
    """
    all_limits = get_all_system_limits()
    grouped = {}

    for cat_key, cat_info in LIMIT_CATEGORIES.items():
        items = [lim for lim in all_limits if lim["category"] == cat_key]
        if items:
            grouped[cat_key] = {
                "title": cat_info["title"],
                "description": cat_info["description"],
                "icon": cat_info["icon"],
                "badge_class": cat_info["badge_class"],
                "limits": items,
            }

    return grouped


def set_system_limit(key: str, value: Any, admin_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Cập nhật một giá trị giới hạn hệ thống và ghi nhận Audit Log.
    """
    norm_key = key.strip().upper()
    if norm_key not in SYSTEM_LIMITS_METADATA:
        return {
            "success": False,
            "error": f"Không tìm thấy tham số cấu hình giới hạn '{key}'."
        }

    meta = SYSTEM_LIMITS_METADATA[norm_key]

    try:
        int_val = int(value)
    except (ValueError, TypeError):
        return {
            "success": False,
            "error": f"Giá trị '{value}' cho '{meta['name']}' không hợp lệ (phải là số nguyên)."
        }

    if int_val < meta["min"] or int_val > meta["max"]:
        return {
            "success": False,
            "error": f"Giá trị cho '{meta['name']}' phải nằm trong khoảng từ {meta['min']} đến {meta['max']} {meta['unit']}."
        }

    # Save to SystemConfig
    SystemConfig.set_config(
        key=norm_key,
        value=int_val,
        description=meta["description"],
        category="LIMITS",
        is_active=True
    )

    if admin_id:
        log_audit_action(
            user_id=admin_id,
            action="UPDATE_SYSTEM_LIMIT",
            target_type="SYSTEM_CONFIG",
            target_id=norm_key,
            details=f"Cập nhật giới hạn {meta['name']} ({norm_key}) thành {int_val} {meta['unit']}"
        )

    return {
        "success": True,
        "key": norm_key,
        "value": int_val,
        "unit": meta["unit"],
        "message": f"Đã cập nhật '{meta['name']}' thành công ({int_val} {meta['unit']})."
    }


def bulk_update_system_limits(limits_dict: Dict[str, Any], admin_id: Optional[int] = None) -> Tuple[bool, List[str], List[str]]:
    """
    Cập nhật đồng thời nhiều giá trị giới hạn từ Form.
    Trả về (is_all_success, success_messages, error_messages).
    """
    success_messages = []
    error_messages = []

    for key, val in limits_dict.items():
        norm_key = key.strip().upper()
        if norm_key in SYSTEM_LIMITS_METADATA:
            res = set_system_limit(norm_key, val, admin_id=admin_id)
            if res["success"]:
                success_messages.append(res["message"])
            else:
                error_messages.append(res.get("error", "Lỗi không xác định"))

    is_all_success = len(error_messages) == 0
    return is_all_success, success_messages, error_messages


def reset_system_limits(admin_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Khôi phục toàn bộ các giới hạn hệ thống về giá trị mặc định ban đầu.
    """
    for key, meta in SYSTEM_LIMITS_METADATA.items():
        SystemConfig.set_config(
            key=key,
            value=meta["default"],
            description=meta["description"],
            category="LIMITS",
            is_active=True
        )

    if admin_id:
        log_audit_action(
            user_id=admin_id,
            action="RESET_SYSTEM_LIMITS",
            target_type="SYSTEM_CONFIG",
            target_id="ALL_LIMITS",
            details="Khôi phục toàn bộ giới hạn hệ thống về cấu hình mặc định ban đầu."
        )

    return {
        "success": True,
        "message": "Đã khôi phục toàn bộ giới hạn hệ thống về cấu hình mặc định thành công."
    }
