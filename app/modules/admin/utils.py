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


def has_permission(user, permission_name):
    if not user or not user.is_authenticated:
        return False
    if user.is_admin:
        return True

    user_roles = UserRole.query.filter_by(user_id=user.id).all()
    active_roles = [ur.role for ur in user_roles if ur.role and is_role_active(ur.expires_at)]

    for role in active_roles:
        role_perms = get_role_permissions_recursive(role)
        if permission_name in role_perms or "*" in role_perms:
            return True

    return False


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
