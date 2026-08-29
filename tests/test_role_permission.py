from datetime import datetime, timedelta, timezone
from app.extensions import db
from app.modules.admin.models import AuditLog, Permission, Role, RolePermission, UserRole
from app.modules.admin.utils import has_permission, log_audit_action, permission_required
from app.modules.auth.models import User


def login_admin(client):
    return client.post("/auth/login", data={"email": "admin@test.com", "password": "admin123"}, follow_redirects=True)


def test_custom_role_creation_and_permissions(client):
    login_admin(client)

    res = client.post(
        "/admin/roles",
        data={"name": "CONTENT_EDITOR", "description": "Tập sự biên tập", "permissions": ["1", "2"]},
        follow_redirects=True,
    )
    assert res.status_code == 200
    assert "Đã khởi tạo vai trò tùy chỉnh 'CONTENT_EDITOR'".encode("utf-8") in res.data

    with client.application.app_context():
        role = Role.query.filter_by(name="CONTENT_EDITOR").first()
        assert role is not None
        assert role.is_custom is True
        assert len(role.permissions) >= 1


def test_role_inheritance(client):
    with client.application.app_context():
        p_parent = Permission.query.filter_by(name="lessons:delete").first()
        if not p_parent:
            p_parent = Permission(name="lessons:delete", description="Xóa bài học", category="Lessons")
            db.session.add(p_parent)
            db.session.commit()

        parent_role = Role(name="PARENT_MANAGER", description="Cha", is_custom=True)
        db.session.add(parent_role)
        db.session.commit()

        rp = RolePermission(role_id=parent_role.id, permission_id=p_parent.id)
        db.session.add(rp)
        db.session.commit()

        child_role = Role(name="CHILD_EDITOR", description="Con", is_custom=True, parent_id=parent_role.id)
        db.session.add(child_role)
        db.session.commit()

        user = User.query.filter_by(username="student").first()
        ur = UserRole(user_id=user.id, role_id=child_role.id)
        db.session.add(ur)
        db.session.commit()

        # Child role user inherits parent role's permission
        assert has_permission(user, "lessons:delete") is True


def ensure_default_roles_and_permissions():
    perm = Permission.query.filter_by(name="vocabulary:manage").first()
    if not perm:
        perm = Permission(name="vocabulary:manage", description="Quản lý từ vựng", category="Vocabulary")
        db.session.add(perm)
        db.session.commit()

    role = Role.query.filter_by(name="MODERATOR").first()
    if not role:
        role = Role(name="MODERATOR", description="Kiểm duyệt viên", is_custom=False)
        db.session.add(role)
        db.session.commit()

    rp = RolePermission.query.filter_by(role_id=role.id, permission_id=perm.id).first()
    if not rp:
        rp = RolePermission(role_id=role.id, permission_id=perm.id)
        db.session.add(rp)
        db.session.commit()

    return role


def test_temporary_role_assignment(client):
    with client.application.app_context():
        user = User.query.filter_by(username="student").first()
        role = ensure_default_roles_and_permissions()

        # Past expiry date (Expired temporary role)
        past_date = datetime.now(timezone.utc) - timedelta(days=2)
        ur_expired = UserRole(user_id=user.id, role_id=role.id, expires_at=past_date)
        db.session.add(ur_expired)
        db.session.commit()

        assert has_permission(user, "vocabulary:manage") is False

        # Future expiry date (Active temporary role)
        ur_expired.expires_at = datetime.now(timezone.utc) + timedelta(days=5)
        db.session.commit()

        assert has_permission(user, "vocabulary:manage") is True


def test_audit_logs_recording(client):
    login_admin(client)

    # Assign role via admin endpoint
    with client.application.app_context():
        student = User.query.filter_by(username="student").first()
        role = ensure_default_roles_and_permissions()
        student_id = student.id
        role_id = role.id

    res = client.post(
        f"/admin/users/{student_id}/assign-role",
        data={"role_id": str(role_id), "expires_at": "2028-12-31"},
        follow_redirects=True,
    )
    assert res.status_code == 200

    # View Audit Logs page
    res_logs = client.get("/admin/audit-logs")
    assert res_logs.status_code == 200
    assert "ASSIGN_ROLE".encode("utf-8") in res_logs.data
    assert "MODERATOR".encode("utf-8") in res_logs.data
