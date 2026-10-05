from functools import wraps
from datetime import datetime, timezone
from flask import flash, redirect, request, url_for
from flask_login import current_user
from app.extensions import db
from .models import AuditLog, Permission, Role, RolePermission, UserRole


def get_role_permissions_recursive(role, visited=None):
    if visited is None:
        visited = set()
    if not role or role.id in visited:
        return set()
    visited.add(role.id)

    perms = {rp.permission.name for rp in role.permissions if rp.permission}
    if role.parent:
        perms.update(get_role_permissions_recursive(role.parent, visited))
    return perms


def is_role_active(expires_at):
    if expires_at is None:
        return True
    if expires_at.tzinfo is None:
        return expires_at > datetime.now()
    return expires_at > datetime.now(timezone.utc)


def get_user_permissions(user, force_refresh=False):
    """
    Tính toán và trả về toàn bộ quyền hạn (bao gồm kế thừa từ vai trò cha) của User.
    Sử dụng In-memory Permission Caching (TTL 15-30 phút) để tối ưu hiệu năng.
    """
    if not user or not getattr(user, 'is_authenticated', False):
        return set()
    if getattr(user, 'is_admin', False):
        return {"*"}

    from .permission_cache import get_cached_user_permissions, set_cached_user_permissions

    if not force_refresh:
        cached = get_cached_user_permissions(user.id)
        if cached is not None:
            return cached

    user_roles = UserRole.query.filter_by(user_id=user.id).all()
    active_roles = [ur.role for ur in user_roles if ur.role and is_role_active(ur.expires_at)]

    effective_perms = set()
    for role in active_roles:
        effective_perms.update(get_role_permissions_recursive(role))

    set_cached_user_permissions(user.id, effective_perms)
    return effective_perms


def has_permission(user, permission_name):
    if not user or not getattr(user, 'is_authenticated', False):
        return False
    if getattr(user, 'is_admin', False):
        return True

    perms = get_user_permissions(user)
    return permission_name in perms or "*" in perms


def permission_required(permission_name):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash("Vui lòng đăng nhập để tiếp tục.", "warning")
                return redirect(url_for("auth.login"))
            if not has_permission(current_user, permission_name):
                flash(f"Bạn không có quyền '{permission_name}' để thực hiện thao tác này.", "danger")
                return redirect(url_for("main.dashboard"))
            return f(*args, **kwargs)

        return decorated_function

    return decorator


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Vui lòng đăng nhập với tư cách Quản trị viên.", "warning")
            return redirect(url_for("auth.login"))
        if not current_user.is_admin:
            from flask import abort
            abort(403)
        return view(*args, **kwargs)
    return wrapped


def log_audit_action(user_id, action, target_type=None, target_id=None, details=None, ip_address=None):
    try:
        if not ip_address and request:
            ip_address = request.remote_addr
        log = AuditLog(
            user_id=user_id,
            action=action,
            target_type=target_type,
            target_id=str(target_id) if target_id else None,
            details=details,
            ip_address=ip_address or "127.0.0.1",
        )
        db.session.add(log)
        db.session.commit()
        return log
    except Exception as exc:
        print(f"Error writing audit log: {exc}")
        return None
