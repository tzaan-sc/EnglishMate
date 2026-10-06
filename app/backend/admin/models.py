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
    def get_int_config(cls, key: str, default: int = None) -> int:
        val = cls.get_config(key, None)
        if val is None:
            return default
        try:
            return int(val)
        except (ValueError, TypeError):
            return default

    @classmethod
    def get_float_config(cls, key: str, default: float = None) -> float:
        val = cls.get_config(key, None)
        if val is None:
            return default
        try:
            return float(val)
        except (ValueError, TypeError):
            return default

    @classmethod
    def set_config(cls, key: str, value, description: str = None, category: str = None, is_active: bool = True) -> "SystemConfig":
        item = cls.query.filter_by(key=key).first()
        if not item:
            item = cls(
                key=key,
                value=str(value) if value is not None else None,
                description=description,
                category=category or "GENERAL",
                is_active=is_active
            )
            db.session.add(item)
        else:
            item.value = str(value) if value is not None else None
            if description is not None:
                item.description = description
            if category is not None:
                item.category = category
            if is_active is not None:
                item.is_active = is_active
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise
        return item

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


class DatabaseBackup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False, unique=True, index=True)
    file_path = db.Column(db.String(500), nullable=False)
    file_size_bytes = db.Column(db.BigInteger, default=0, nullable=False)
    backup_type = db.Column(db.String(50), default="MANUAL", nullable=False, index=True)  # MANUAL, DAILY, WEEKLY, AUTO
    db_type = db.Column(db.String(50), default="SQLITE", nullable=False)  # SQLITE, POSTGRESQL
    is_compressed = db.Column(db.Boolean, default=True, nullable=False)
    status = db.Column(db.String(50), default="SUCCESS", nullable=False)  # SUCCESS, FAILED
    notes = db.Column(db.String(255), nullable=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at = db.Column(db.DateTime(timezone=True), default=now, nullable=False, index=True)

    created_by = db.relationship("User", backref=db.backref("created_backups", lazy="dynamic"))

    @property
    def created_at_vn(self):
        if not self.created_at:
            return None
        return self.created_at + timedelta(hours=7)

    @property
    def file_size_display(self):
        bytes_val = self.file_size_bytes or 0
        if bytes_val < 1024:
            return f"{bytes_val} B"
        elif bytes_val < 1024 * 1024:
            return f"{round(bytes_val / 1024, 1)} KB"
        elif bytes_val < 1024 * 1024 * 1024:
            return f"{round(bytes_val / (1024 * 1024), 2)} MB"
        else:
            return f"{round(bytes_val / (1024 * 1024 * 1024), 2)} GB"


# ---------------------------------------------------------------------------
# EMAIL SYSTEM MODELS (MỤC 12.4)
# ---------------------------------------------------------------------------

class EmailLog(db.Model):
    """Lưu vết tất cả email được gửi đi, tracking trạng thái mở/click và bounce."""
    id = db.Column(db.Integer, primary_key=True)
    tracking_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    recipient = db.Column(db.String(255), nullable=False, index=True)
    subject = db.Column(db.String(255), nullable=False)
    email_type = db.Column(db.String(50), default="NOTIFICATION", nullable=False, index=True)
    status = db.Column(db.String(50), default="QUEUED", nullable=False, index=True)  # QUEUED, SENDING, SENT, OPENED, CLICKED, BOUNCED, FAILED
    error_message = db.Column(db.Text, nullable=True)
    bounce_reason = db.Column(db.String(255), nullable=True)
    open_count = db.Column(db.Integer, default=0, nullable=False)
    click_count = db.Column(db.Integer, default=0, nullable=False)
    opened_at = db.Column(db.DateTime(timezone=True), nullable=True)
    clicked_at = db.Column(db.DateTime(timezone=True), nullable=True)
    scheduled_at = db.Column(db.DateTime(timezone=True), nullable=True, index=True)
    sent_at = db.Column(db.DateTime(timezone=True), nullable=True, index=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at = db.Column(db.DateTime(timezone=True), default=now, nullable=False, index=True)

    created_by = db.relationship("User", backref=db.backref("sent_emails", lazy="dynamic"))

    @property
    def created_at_vn(self):
        if not self.created_at:
            return None
        return self.created_at + timedelta(hours=7)

    @property
    def sent_at_vn(self):
        if not self.sent_at:
            return None
        return self.sent_at + timedelta(hours=7)

    @property
    def opened_at_vn(self):
        if not self.opened_at:
            return None
        return self.opened_at + timedelta(hours=7)


class EmailTemplate(db.Model):
    """Mẫu HTML email có thể tùy chỉnh động qua giao diện quản trị Admin."""
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False, index=True)
    name = db.Column(db.String(150), nullable=False)
    subject = db.Column(db.String(255), nullable=False)
    html_content = db.Column(db.Text, nullable=False)
    text_content = db.Column(db.Text, nullable=True)
    variables_json = db.Column(db.Text, nullable=True)  # JSON list string e.g. ["username", "otp_code"]
    description = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=now, onupdate=now, nullable=False)

    @property
    def variables_list(self) -> list:
        if not self.variables_json:
            return []
        try:
            parsed = json.loads(self.variables_json)
            return parsed if isinstance(parsed, list) else []
        except Exception:
            return []

    def render(self, context: dict = None) -> tuple:
        """Render tiêu đề và nội dung HTML email với các biến context truyền vào."""
        ctx = context or {}
        rendered_subject = self.subject
        rendered_html = self.html_content
        rendered_text = self.text_content or ""

        for k, v in ctx.items():
            placeholder = "{{" + f" {k} " + "}}"
            placeholder_no_space = "{{" + k + "}}"
            rendered_subject = rendered_subject.replace(placeholder, str(v)).replace(placeholder_no_space, str(v))
            rendered_html = rendered_html.replace(placeholder, str(v)).replace(placeholder_no_space, str(v))
            rendered_text = rendered_text.replace(placeholder, str(v)).replace(placeholder_no_space, str(v))

        return rendered_subject, rendered_html, rendered_text


class EmailBounce(db.Model):
    """Danh sách các địa chỉ email không tồn tại hoặc bị từ chối (Bounce List)."""
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    bounce_type = db.Column(db.String(50), default="HARD_BOUNCE", nullable=False)  # HARD_BOUNCE, SOFT_BOUNCE, SYNTAX_ERROR
    reason = db.Column(db.String(255), nullable=True)
    is_blocked = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=now, nullable=False, index=True)

    @property
    def created_at_vn(self):
        if not self.created_at:
            return None
        return self.created_at + timedelta(hours=7)


class BackgroundTask(db.Model):
    """Bảng ghi nhận và quản lý tiến trình tác vụ nền (Task Queue & Scheduled Jobs - Mục 12.5)."""
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    name = db.Column(db.String(150), nullable=False, index=True)
    task_type = db.Column(db.String(50), default="ASYNC_JOB", nullable=False, index=True)  # ASYNC_JOB, SCHEDULED_CRON, MAINTENANCE
    priority = db.Column(db.Integer, default=5, nullable=False, index=True)  # 1: LOW, 5: NORMAL, 10: HIGH
    status = db.Column(db.String(50), default="PENDING", nullable=False, index=True)  # PENDING, RUNNING, COMPLETED, FAILED, RETRYING, CANCELLED
    params_json = db.Column(db.Text, nullable=True)
    result_json = db.Column(db.Text, nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    retry_count = db.Column(db.Integer, default=0, nullable=False)
    max_retries = db.Column(db.Integer, default=3, nullable=False)
    retry_delay_seconds = db.Column(db.Integer, default=5, nullable=False)
    timeout_seconds = db.Column(db.Integer, default=300, nullable=False)
    scheduled_at = db.Column(db.DateTime(timezone=True), nullable=True, index=True)
    started_at = db.Column(db.DateTime(timezone=True), nullable=True)
    completed_at = db.Column(db.DateTime(timezone=True), nullable=True)
    duration_ms = db.Column(db.Float, default=0.0, nullable=False)
    memory_start_mb = db.Column(db.Float, default=0.0, nullable=False)
    memory_end_mb = db.Column(db.Float, default=0.0, nullable=False)
    memory_peak_mb = db.Column(db.Float, default=0.0, nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="SET NULL"), nullable=True, index=True)
    created_at = db.Column(db.DateTime(timezone=True), default=now, nullable=False, index=True)

    @property
    def priority_label(self) -> str:
        if self.priority >= 10:
            return "Cao (High)"
        elif self.priority >= 5:
            return "Trung bình (Normal)"
        return "Thấp (Low)"

    @property
    def priority_badge_class(self) -> str:
        if self.priority >= 10:
            return "bg-danger-subtle text-danger border border-danger-subtle"
        elif self.priority >= 5:
            return "bg-primary-subtle text-primary border border-primary-subtle"
        return "bg-secondary-subtle text-secondary border border-secondary-subtle"

    @property
    def status_badge_class(self) -> str:
        mapping = {
            "COMPLETED": "bg-success-subtle text-success border border-success-subtle",
            "RUNNING": "bg-info-subtle text-info border border-info-subtle",
            "PENDING": "bg-warning-subtle text-warning border border-warning-subtle",
            "RETRYING": "bg-warning-subtle text-warning border border-warning-subtle",
            "FAILED": "bg-danger-subtle text-danger border border-danger-subtle",
            "CANCELLED": "bg-secondary-subtle text-secondary border border-secondary-subtle",
        }
        return mapping.get(self.status, "bg-light text-dark")

    @property
    def duration_formatted(self) -> str:
        if self.duration_ms < 1000:
            return f"{round(self.duration_ms, 1)} ms"
        return f"{round(self.duration_ms / 1000, 2)} s"

    @property
    def memory_diff_mb(self) -> float:
        return round(max(0.0, (self.memory_end_mb or 0.0) - (self.memory_start_mb or 0.0)), 2)

    @property
    def created_at_vn(self):
        return (self.created_at + timedelta(hours=7)) if self.created_at else None

    @property
    def started_at_vn(self):
        return (self.started_at + timedelta(hours=7)) if self.started_at else None

    @property
    def completed_at_vn(self):
        return (self.completed_at + timedelta(hours=7)) if self.completed_at else None

    @property
    def params_dict(self) -> dict:
        if not self.params_json:
            return {}
        try:
            return json.loads(self.params_json)
        except Exception:
            return {}

    @property
    def result_dict(self) -> dict:
        if not self.result_json:
            return {}
        try:
            return json.loads(self.result_json)
        except Exception:
            return {}


# ===========================================================================
# 12.7. ERROR LOGGING & MONITORING MODEL
# ===========================================================================
class SystemErrorLog(db.Model):
    """
    Lưu trữ và phân tích lỗi hệ thống (Error Analysis & Monitoring).
    Gom nhóm theo Fingerprint (Exception Type + Location), theo dõi tần suất,
    bắt lỗi Sentry và quản lý trạng thái xử lý lỗi (Resolved / Open).
    """
    __tablename__ = "system_error_log"

    id = db.Column(db.Integer, primary_key=True)
    error_id = db.Column(db.String(36), unique=True, nullable=False, index=True)
    fingerprint = db.Column(db.String(64), nullable=False, index=True)
    exception_type = db.Column(db.String(120), nullable=False, default="InternalServerError", index=True)
    error_message = db.Column(db.Text, nullable=False)
    status_code = db.Column(db.Integer, default=500, nullable=False, index=True)
    severity = db.Column(db.String(20), default="ERROR", nullable=False, index=True)  # CRITICAL, ERROR, WARNING, INFO
    route = db.Column(db.String(255), nullable=True, index=True)
    http_method = db.Column(db.String(10), nullable=True, default="GET")
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="SET NULL"), nullable=True, index=True)
    ip_address = db.Column(db.String(64), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    traceback_text = db.Column(db.Text, nullable=True)
    request_params_json = db.Column(db.Text, nullable=True)
    is_resolved = db.Column(db.Boolean, default=False, nullable=False, index=True)
    resolved_at = db.Column(db.DateTime(timezone=True), nullable=True)
    resolved_by_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="SET NULL"), nullable=True)
    resolution_notes = db.Column(db.Text, nullable=True)
    sentry_event_id = db.Column(db.String(64), nullable=True)
    occurrence_count = db.Column(db.Integer, default=1, nullable=False)
    first_seen_at = db.Column(db.DateTime(timezone=True), default=now, nullable=False)
    last_seen_at = db.Column(db.DateTime(timezone=True), default=now, nullable=False, index=True)
    created_at = db.Column(db.DateTime(timezone=True), default=now, nullable=False, index=True)

    @property
    def severity_badge_class(self) -> str:
        mapping = {
            "CRITICAL": "bg-danger text-white",
            "ERROR": "bg-danger-subtle text-danger border border-danger-subtle",
            "WARNING": "bg-warning-subtle text-warning border border-warning-subtle",
            "INFO": "bg-info-subtle text-info border border-info-subtle",
        }
        return mapping.get(self.severity.upper(), "bg-secondary-subtle text-secondary")

    @property
    def status_code_badge_class(self) -> str:
        if self.status_code >= 500:
            return "bg-danger-subtle text-danger border border-danger-subtle"
        elif self.status_code >= 400:
            return "bg-warning-subtle text-warning border border-warning-subtle"
        return "bg-success-subtle text-success border border-success-subtle"

    @property
    def short_message(self) -> str:
        if not self.error_message:
            return ""
        return self.error_message[:120] + ("..." if len(self.error_message) > 120 else "")

    @property
    def created_at_vn(self):
        return (self.created_at + timedelta(hours=7)) if self.created_at else None

    @property
    def last_seen_at_vn(self):
        return (self.last_seen_at + timedelta(hours=7)) if self.last_seen_at else None

    @property
    def first_seen_at_vn(self):
        return (self.first_seen_at + timedelta(hours=7)) if self.first_seen_at else None



# ---------------------------------------------------------------------------
# AUTOMATIC PERMISSION CACHE INVALIDATION HOOKS (MỤC 11.2)
# ---------------------------------------------------------------------------
from sqlalchemy import event


def _on_user_role_change(mapper, connection, target):
    from .permission_cache import invalidate_permission_cache
    if hasattr(target, "user_id") and target.user_id:
        invalidate_permission_cache(target.user_id)


def _on_role_perm_change(mapper, connection, target):
    from .permission_cache import invalidate_permission_cache
    invalidate_permission_cache()


event.listen(UserRole, "after_insert", _on_user_role_change)
event.listen(UserRole, "after_update", _on_user_role_change)
event.listen(UserRole, "after_delete", _on_user_role_change)

event.listen(RolePermission, "after_insert", _on_role_perm_change)
event.listen(RolePermission, "after_update", _on_role_perm_change)
event.listen(RolePermission, "after_delete", _on_role_perm_change)

event.listen(Role, "after_update", _on_role_perm_change)
event.listen(Role, "after_delete", _on_role_perm_change)

