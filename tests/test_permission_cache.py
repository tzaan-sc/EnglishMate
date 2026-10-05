import time
from tests.conftest import login
from app.extensions import db
from app.backend.auth.models import User
from app.backend.admin.models import Role, Permission, RolePermission, UserRole
from app.backend.admin.utils import get_user_permissions, has_permission
from app.backend.admin.permission_cache import (
    get_cached_user_permissions,
    set_cached_user_permissions,
    invalidate_permission_cache,
    get_permission_cache_stats,
    get_permission_cache_ttl,
)


def test_permission_cache_basic_get_set():
    """Kiểm tra lưu trữ và truy xuất quyền hạn từ cache in-memory."""
    invalidate_permission_cache()

    user_id = 9999
    perms = {"lessons:read", "vocabulary:manage"}

    assert get_cached_user_permissions(user_id) is None

    set_cached_user_permissions(user_id, perms, ttl_seconds=600)
    cached = get_cached_user_permissions(user_id)
    assert cached == perms

    stats = get_permission_cache_stats()
    assert stats["total_cached_users"] >= 1
    assert stats["active_entries"] >= 1


def test_permission_cache_expiration():
    """Khi hết hạn TTL, cache tự động bị loại bỏ và trả về None."""
    invalidate_permission_cache()

    user_id = 8888
    perms = {"audit:read"}

    # TTL 1 second
    set_cached_user_permissions(user_id, perms, ttl_seconds=1)
    assert get_cached_user_permissions(user_id) == perms

    # Sleep past expiration
    time.sleep(1.1)
    assert get_cached_user_permissions(user_id) is None


def test_invalidate_single_user_and_all_users():
    """Kiểm tra xóa cache cho từng user hoặc toàn bộ hệ thống."""
    invalidate_permission_cache()

    set_cached_user_permissions(101, {"p1"}, ttl_seconds=300)
    set_cached_user_permissions(102, {"p2"}, ttl_seconds=300)

    assert get_cached_user_permissions(101) == {"p1"}
    assert get_cached_user_permissions(102) == {"p2"}

    # Invalidate user 101 only
    cleared = invalidate_permission_cache(101)
    assert cleared == 1
    assert get_cached_user_permissions(101) is None
    assert get_cached_user_permissions(102) == {"p2"}

    # Invalidate all
    cleared_all = invalidate_permission_cache()
    assert cleared_all >= 1
    assert get_cached_user_permissions(102) is None


def test_get_user_permissions_caches_result(app):
    """get_user_permissions lưu cache sau lần truy vấn đầu tiên."""
    with app.app_context():
        invalidate_permission_cache()

        user = User.query.filter_by(email="student@test.com").first()
        assert user is not None

        # Verify not cached yet
        assert get_cached_user_permissions(user.id) is None

        perms = get_user_permissions(user)
        assert isinstance(perms, set)

        # Should now be in cache
        cached = get_cached_user_permissions(user.id)
        assert cached is not None
        assert cached == perms


def test_admin_user_has_wildcard_permission(app):
    """Admin có toàn quyền '*' và không bị phụ thuộc vào cache role."""
    with app.app_context():
        admin = User.query.filter_by(email="admin@test.com").first()
        assert admin is not None
        assert admin.is_admin is True

        perms = get_user_permissions(admin)
        assert perms == {"*"}
        assert has_permission(admin, "any:action") is True


def test_permission_cache_api_unauthorized(client, app):
    """Học viên bình thường không có quyền truy cập endpoint quản trị cache."""
    invalidate_permission_cache()
    set_cached_user_permissions(555, {"demo:read"}, ttl_seconds=900)

    login(client, "student@test.com", "user123")
    res_stats = client.get("/admin/system/permissions/cache-stats")
    assert res_stats.status_code == 403

    res_clear = client.post("/admin/system/permissions/clear-cache", json={})
    assert res_clear.status_code == 403


def test_permission_cache_api_admin(client, app):
    """Admin có thể xem thống kê và xóa cache qua REST API."""
    invalidate_permission_cache()
    set_cached_user_permissions(555, {"demo:read"}, ttl_seconds=900)

    login(client, "admin@test.com", "admin123")
    res_stats = client.get("/admin/system/permissions/cache-stats")
    assert res_stats.status_code == 200
    data = res_stats.get_json()
    assert data["success"] is True
    assert "stats" in data
    assert data["stats"]["total_cached_users"] >= 1

    # Admin can clear cache
    res_clear = client.post("/admin/system/permissions/clear-cache", json={})
    assert res_clear.status_code == 200
    clear_data = res_clear.get_json()
    assert clear_data["success"] is True
    assert clear_data["cleared_count"] >= 1

    # Verify cache is cleared
    assert get_cached_user_permissions(555) is None

