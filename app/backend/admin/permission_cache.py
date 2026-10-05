import time
from typing import Any, Dict, Optional, Set, Tuple

_PERMISSION_CACHE: Dict[int, Dict[str, Any]] = {}
DEFAULT_CACHE_TTL_SECONDS = 900  # 15 phút (900s), tối đa 1800s (30 phút)


def get_permission_cache_ttl() -> int:
    """Lấy thời gian sống (TTL) của bộ nhớ đệm quyền hạn từ SystemConfig."""
    try:
        from .models import SystemConfig
        val = SystemConfig.get_int_config("PERMISSION_CACHE_TTL_SECONDS", default=DEFAULT_CACHE_TTL_SECONDS)
        return max(60, min(86400, val or DEFAULT_CACHE_TTL_SECONDS))
    except Exception:
        return DEFAULT_CACHE_TTL_SECONDS


def get_cached_user_permissions(user_id: int) -> Optional[Set[str]]:
    """
    Lấy danh sách quyền hạn đã được cache của User.
    Trả về None nếu cache miss hoặc đã hết hạn TTL.
    """
    if not user_id or user_id not in _PERMISSION_CACHE:
        return None

    entry = _PERMISSION_CACHE[user_id]
    now = time.time()
    if now > entry["expires_at"]:
        # Cache expired
        _PERMISSION_CACHE.pop(user_id, None)
        return None

    return entry["permissions"]


def set_cached_user_permissions(
    user_id: int,
    permissions: Set[str],
    ttl_seconds: Optional[int] = None
) -> None:
    """Lưu trữ quyền hạn của User vào bộ nhớ đệm In-memory với thời gian TTL."""
    if not user_id:
        return

    ttl = ttl_seconds if ttl_seconds is not None else get_permission_cache_ttl()
    now = time.time()
    _PERMISSION_CACHE[user_id] = {
        "permissions": set(permissions),
        "cached_at": now,
        "expires_at": now + ttl
    }


def invalidate_permission_cache(user_id: Optional[int] = None) -> int:
    """
    Xóa bộ nhớ đệm quyền hạn khi có thay đổi vai trò hoặc quyền hạn.
    - Nếu user_id được chỉ định: Xóa cache của user đó.
    - Nếu user_id là None: Xóa toàn bộ cache của tất cả người dùng.
    """
    if user_id is not None:
        if user_id in _PERMISSION_CACHE:
            _PERMISSION_CACHE.pop(user_id, None)
            return 1
        return 0
    else:
        count = len(_PERMISSION_CACHE)
        _PERMISSION_CACHE.clear()
        return count


def get_permission_cache_stats() -> Dict[str, Any]:
    """Tổng hợp thông số thống kê về bộ nhớ đệm quyền hạn hiện tại."""
    now = time.time()
    active_count = 0
    expired_count = 0

    for uid, entry in list(_PERMISSION_CACHE.items()):
        if now <= entry["expires_at"]:
            active_count += 1
        else:
            expired_count += 1

    return {
        "total_cached_users": len(_PERMISSION_CACHE),
        "active_entries": active_count,
        "expired_entries": expired_count,
        "ttl_seconds": get_permission_cache_ttl(),
        "ttl_minutes": round(get_permission_cache_ttl() / 60, 1),
    }
