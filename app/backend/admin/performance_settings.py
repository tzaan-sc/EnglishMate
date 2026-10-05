from typing import Any, Dict, List, Optional, Tuple
from app.extensions import db
from .models import SystemConfig
from .utils import log_audit_action


PERFORMANCE_SETTINGS_METADATA: Dict[str, Dict[str, Any]] = {
    "DEFAULT_PAGE_SIZE": {
        "key": "DEFAULT_PAGE_SIZE",
        "name": "Số lượng bản ghi hiển thị mặc định mỗi trang (Page Size)",
        "description": "Số lượng dòng dữ liệu hiển thị mặc định trên mỗi trang danh sách bảng dữ liệu chung (Từ vựng, Bài học, Đề thi).",
        "category": "PAGINATION",
        "category_title": "Phân trang & Hiển thị Danh sách",
        "default": 20,
        "min": 5,
        "max": 100,
        "step": 5,
        "unit": "dòng/trang",
        "icon": "ph-list-dashes",
        "recommended": 20,
    },
    "ADMIN_AUDIT_LOG_PAGE_SIZE": {
        "key": "ADMIN_AUDIT_LOG_PAGE_SIZE",
        "name": "Số bản ghi Nhật ký Audit mỗi trang",
        "description": "Số lượng sự kiện nhật ký kiểm tra hệ thống (Audit Logs) hiển thị trên mỗi trang quản trị.",
        "category": "PAGINATION",
        "category_title": "Phân trang & Hiển thị Danh sách",
        "default": 20,
        "min": 5,
        "max": 100,
        "step": 5,
        "unit": "dòng/trang",
        "icon": "ph-clock-counter-clockwise",
        "recommended": 20,
    },
    "ADMIN_IMPORT_HISTORY_PAGE_SIZE": {
        "key": "ADMIN_IMPORT_HISTORY_PAGE_SIZE",
        "name": "Số bản ghi Lịch sử Import mỗi trang",
        "description": "Số lượng đợt nhập dữ liệu Excel/JSON hiển thị trên mỗi trang bảng lịch sử tại Import Hub.",
        "category": "PAGINATION",
        "category_title": "Phân trang & Hiển thị Danh sách",
        "default": 15,
        "min": 5,
        "max": 50,
        "step": 5,
        "unit": "dòng/trang",
        "icon": "ph-file-arrow-down",
        "recommended": 15,
    },
    "STATIC_CACHE_MAX_AGE_SECONDS": {
        "key": "STATIC_CACHE_MAX_AGE_SECONDS",
        "name": "Thời gian Cache File Tĩnh (Cache-Control max-age)",
        "description": "Thời gian trình duyệt của người dùng lưu cache các tài nguyên tĩnh CSS, JavaScript, Web Fonts, hình ảnh (tính theo giây).",
        "category": "CACHING",
        "category_title": "Bộ nhớ đệm & Tăng tốc Tải trang",
        "default": 86400,
        "min": 0,
        "max": 2592000,
        "step": 3600,
        "unit": "giây (86400s = 24h)",
        "icon": "ph-lightning",
        "recommended": 86400,
    },
    "API_RESPONSE_CACHE_SECONDS": {
        "key": "API_RESPONSE_CACHE_SECONDS",
        "name": "Thời gian Cache dữ liệu API công khai",
        "description": "Thời gian lưu tạm kết quả phản hồi của các API danh mục tĩnh, thống kê công khai để giảm tải truy vấn cơ sở dữ liệu.",
        "category": "CACHING",
        "category_title": "Bộ nhớ đệm & Tăng tốc Tải trang",
        "default": 300,
        "min": 0,
        "max": 3600,
        "step": 60,
        "unit": "giây (300s = 5 phút)",
        "icon": "ph-arrows-clockwise",
        "recommended": 300,
    },
    "SQLITE_CACHE_SIZE_MB": {
        "key": "SQLITE_CACHE_SIZE_MB",
        "name": "Dung lượng Bộ nhớ Cache CSDL SQLite",
        "description": "Dung lượng bộ nhớ RAM (Megabytes) được cấp phát cho cache truy vấn SQLite nhằm tăng tốc độ truy vấn phức tạp.",
        "category": "DATABASE",
        "category_title": "Cơ sở dữ liệu & Tối ưu hóa Bộ nhớ",
        "default": 64,
        "min": 16,
        "max": 512,
        "step": 16,
        "unit": "MB",
        "icon": "ph-database",
        "recommended": 64,
    },
}

PERFORMANCE_CATEGORIES = {
    "PAGINATION": {
        "title": "Phân trang & Hiển thị Danh sách",
        "description": "Cấu hình số lượng bản ghi hiển thị trên mỗi trang nhằm cân đối giữa trải nghiệm người dùng và tốc độ render.",
        "icon": "ph-list-numbers",
        "badge_class": "bg-primary-subtle text-primary border-primary-subtle",
    },
    "CACHING": {
        "title": "Bộ nhớ đệm & Tăng tốc Tải trang",
        "description": "Điều chỉnh thời gian lưu cache HTTP phía client và cache phản hồi để giảm tải máy chủ và tăng tốc độ duyệt web.",
        "icon": "ph-lightning",
        "badge_class": "bg-warning-subtle text-warning border-warning-subtle",
    },
    "DATABASE": {
        "title": "Cơ sở dữ liệu & Tối ưu hóa Bộ nhớ",
        "description": "Thiết lập dung lượng RAM đệm cache truy vấn để tối ưu hóa hiệu suất đọc ghi dữ liệu lớn.",
        "icon": "ph-database",
        "badge_class": "bg-success-subtle text-success border-success-subtle",
    },
}


def get_performance_setting(key: str, default: Optional[int] = None) -> int:
    """
    Lấy giá trị cấu hình hiệu năng từ CSDL SystemConfig.
    Nếu chưa có trong CSDL, trả về giá trị mặc định từ metadata.
    """
    norm_key = key.strip().upper()
    meta = PERFORMANCE_SETTINGS_METADATA.get(norm_key)
    fallback = default if default is not None else (meta["default"] if meta else 0)
    return SystemConfig.get_int_config(norm_key, default=fallback)


def get_effective_page_size(setting_key: str, default: int = 20, custom_arg: Optional[Any] = None) -> int:
    """
    Lấy số lượng bản ghi mỗi trang, ưu tiên query param `per_page` nếu có và hợp lệ,
    ngược lại lấy từ cấu hình Performance Settings trong CSDL.
    """
    if custom_arg is not None:
        try:
            val = int(custom_arg)
            if 1 <= val <= 200:
                return val
        except (ValueError, TypeError):
            pass

    return get_performance_setting(setting_key, default=default)


def get_all_performance_settings() -> List[Dict[str, Any]]:
    """
    Lấy danh sách tất cả các thông số cấu hình hiệu năng kèm trạng thái hiện tại.
    """
    try:
        db_configs = {c.key.upper(): c for c in SystemConfig.query.all()}
    except Exception:
        db_configs = {}

    settings_list = []
    for key, meta in PERFORMANCE_SETTINGS_METADATA.items():
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

        settings_list.append({
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

    return settings_list


def get_grouped_performance_settings() -> Dict[str, Dict[str, Any]]:
    """
    Nhóm danh sách các thông số hiệu năng theo chuyên mục để hiển thị trực quan trên giao diện Admin.
    """
    all_settings = get_all_performance_settings()
    grouped = {}

    for cat_key, cat_info in PERFORMANCE_CATEGORIES.items():
        items = [s for s in all_settings if s["category"] == cat_key]
        if items:
            grouped[cat_key] = {
                "title": cat_info["title"],
                "description": cat_info["description"],
                "icon": cat_info["icon"],
                "badge_class": cat_info["badge_class"],
                "settings": items,
            }

    return grouped


def set_performance_setting(key: str, value: Any, admin_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Cập nhật một thông số cấu hình hiệu năng và ghi nhận Audit Log.
    """
    norm_key = key.strip().upper()
    if norm_key not in PERFORMANCE_SETTINGS_METADATA:
        return {
            "success": False,
            "error": f"Không tìm thấy tham số cấu hình hiệu năng '{key}'."
        }

    meta = PERFORMANCE_SETTINGS_METADATA[norm_key]

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
        category="PERFORMANCE",
        is_active=True
    )

    if admin_id:
        log_audit_action(
            user_id=admin_id,
            action="UPDATE_PERFORMANCE_SETTING",
            target_type="SYSTEM_CONFIG",
            target_id=norm_key,
            details=f"Cập nhật thông số hiệu năng {meta['name']} ({norm_key}) thành {int_val} {meta['unit']}"
        )

    return {
        "success": True,
        "key": norm_key,
        "value": int_val,
        "unit": meta["unit"],
        "message": f"Đã cập nhật '{meta['name']}' thành công ({int_val} {meta['unit']})."
    }


def bulk_update_performance_settings(settings_dict: Dict[str, Any], admin_id: Optional[int] = None) -> Tuple[bool, List[str], List[str]]:
    """
    Cập nhật đồng thời nhiều giá trị thông số hiệu năng từ Form.
    Trả về (is_all_success, success_messages, error_messages).
    """
    success_messages = []
    error_messages = []

    for key, val in settings_dict.items():
        norm_key = key.strip().upper()
        if norm_key in PERFORMANCE_SETTINGS_METADATA:
            res = set_performance_setting(norm_key, val, admin_id=admin_id)
            if res["success"]:
                success_messages.append(res["message"])
            else:
                error_messages.append(res.get("error", "Lỗi không xác định"))

    is_all_success = len(error_messages) == 0
    return is_all_success, success_messages, error_messages


def reset_performance_settings(admin_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Khôi phục toàn bộ các thông số hiệu năng về giá trị mặc định ban đầu.
    """
    for key, meta in PERFORMANCE_SETTINGS_METADATA.items():
        SystemConfig.set_config(
            key=key,
            value=meta["default"],
            description=meta["description"],
            category="PERFORMANCE",
            is_active=True
        )

    if admin_id:
        log_audit_action(
            user_id=admin_id,
            action="RESET_PERFORMANCE_SETTINGS",
            target_type="SYSTEM_CONFIG",
            target_id="ALL_PERFORMANCE",
            details="Khôi phục toàn bộ thông số hiệu năng hệ thống về cấu hình mặc định ban đầu."
        )

    return {
        "success": True,
        "message": "Đã khôi phục toàn bộ thông số hiệu năng về cấu hình mặc định thành công."
    }
