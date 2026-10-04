from datetime import datetime, timezone, timedelta
from app.extensions import db

now = lambda: datetime.now(timezone.utc)


class Permission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False, index=True)
    description = db.Column(db.String(255), nullable=True)
    category = db.Column(db.String(50), nullable=False, default="General")


class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)
    description = db.Column(db.String(255), nullable=True)
    is_custom = db.Column(db.Boolean, nullable=False, default=False)
    parent_id = db.Column(db.Integer, db.ForeignKey("role.id", ondelete="SET NULL"), nullable=True)

    parent = db.relationship("Role", remote_side=[id], backref=db.backref("children", lazy="dynamic"))
    permissions = db.relationship("RolePermission", backref="role", cascade="all, delete-orphan", lazy="joined")


class RolePermission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    role_id = db.Column(db.Integer, db.ForeignKey("role.id", ondelete="CASCADE"), nullable=False, index=True)
    permission_id = db.Column(db.Integer, db.ForeignKey("permission.id", ondelete="CASCADE"), nullable=False, index=True)

    permission = db.relationship("Permission", lazy="joined")

    __table_args__ = (db.UniqueConstraint("role_id", "permission_id"),)


class UserRole(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey("role.id", ondelete="CASCADE"), nullable=False, index=True)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=now, nullable=False)

    role = db.relationship("Role", lazy="joined")
    user = db.relationship("User", backref=db.backref("user_assigned_roles", cascade="all, delete-orphan", lazy="dynamic"))

    __table_args__ = (db.UniqueConstraint("user_id", "role_id"),)


class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="SET NULL"), nullable=True, index=True)
    action = db.Column(db.String(100), nullable=False, index=True)
    target_type = db.Column(db.String(50), nullable=True)
    target_id = db.Column(db.String(50), nullable=True)
    details = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=now, nullable=False, index=True)

    user = db.relationship("User", backref=db.backref("audit_logs", lazy="dynamic"))

    @property
    def created_at_vn(self):
        if not self.created_at:
            return None
        return self.created_at + timedelta(hours=7)


class SystemSetting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False, index=True)
    value = db.Column(db.Text, nullable=True)
    description = db.Column(db.String(255), nullable=True)
    updated_at = db.Column(db.DateTime(timezone=True), default=now, onupdate=now, nullable=False)

    @classmethod
    def get_setting(cls, key, default=None):
        try:
            item = cls.query.filter_by(key=key).first()
            return item.value if item and item.value is not None else default
        except Exception:
            return default

    @classmethod
    def get_bool_setting(cls, key, default=False):
        val = cls.get_setting(key, None)
        if val is None:
            return default
        return str(val).strip().lower() in ("true", "1", "yes", "on")

    @classmethod
    def get_int_setting(cls, key, default=None):
        val = cls.get_setting(key, None)
        if val is None:
            return default
        try:
            return int(val)
        except (ValueError, TypeError):
            return default

    @classmethod
    def set_setting(cls, key, value, description=None):
        item = cls.query.filter_by(key=key).first()
        if not item:
            item = cls(key=key, value=str(value) if value is not None else None, description=description)
            db.session.add(item)
        else:
            item.value = str(value) if value is not None else None
            if description:
                item.description = description
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise
        return item


class ImportHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="SET NULL"), nullable=True, index=True)
    filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50), nullable=False, index=True)  # VOCABULARY, GRAMMAR, LESSONS, QUESTIONS, EXAMS
    success_count = db.Column(db.Integer, default=0, nullable=False)
    error_count = db.Column(db.Integer, default=0, nullable=False)
    error_log = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=now, nullable=False, index=True)

    admin = db.relationship("User", backref=db.backref("import_histories", lazy="dynamic"))

    @property
    def created_at_vn(self):
        if not self.created_at:
            return None
        return self.created_at + timedelta(hours=7)


class SystemConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False, index=True)
    value = db.Column(db.Text, nullable=True)
    description = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    category = db.Column(db.String(50), default="GENERAL", nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=now, onupdate=now, nullable=False)

    @classmethod
    def get_config(cls, key: str, default: str = None) -> str:
        try:
            item = cls.query.filter_by(key=key).first()
            return item.value if item and item.value is not None else default
        except Exception:
            return default

    @classmethod
    def is_feature_enabled(cls, key: str, default: bool = True) -> bool:
        try:
            item = cls.query.filter_by(key=key).first()
            if item is not None:
                return bool(item.is_active)
            setting_val = SystemSetting.get_setting(key, None)
            if setting_val is not None:
                return str(setting_val).strip().lower() in ("true", "1", "yes", "on")
            return default
        except Exception:
            return default

    @classmethod
    def set_feature_status(cls, key: str, is_active: bool, description: str = None, category: str = None) -> "SystemConfig":
        item = cls.query.filter_by(key=key).first()
        if not item:
            item = cls(
                key=key,
                is_active=bool(is_active),
                description=description,
                category=category or "GENERAL"
            )
            db.session.add(item)
        else:
            item.is_active = bool(is_active)
            if description:
                item.description = description
            if category:
                item.category = category
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise
        return item


