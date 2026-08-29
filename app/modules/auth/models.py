import random
import secrets
from datetime import date, datetime, timedelta, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db


def now():
    return datetime.now(timezone.utc)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(40), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(10), nullable=False, default="USER")
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    is_email_verified = db.Column(db.Boolean, nullable=False, default=False)
    email_verification_code = db.Column(db.String(6), nullable=True)
    email_verification_expiry = db.Column(db.DateTime(timezone=True), nullable=True)
    oauth_provider = db.Column(db.String(20), nullable=True)
    oauth_id = db.Column(db.String(100), nullable=True)
    failed_login_attempts = db.Column(db.Integer, nullable=False, default=0)
    lockout_until = db.Column(db.DateTime(timezone=True), nullable=True)
    last_login_at = db.Column(db.DateTime(timezone=True), nullable=True)
    reset_token = db.Column(db.String(100), nullable=True)
    reset_token_expiry = db.Column(db.DateTime(timezone=True), nullable=True)
    full_name = db.Column(db.String(100), nullable=True)
    avatar = db.Column(db.String(255), nullable=True, default="default_avatar.png")
    pending_email = db.Column(db.String(120), nullable=True)
    pending_email_otp = db.Column(db.String(6), nullable=True)
    pending_email_expiry = db.Column(db.DateTime(timezone=True), nullable=True)
    current_streak = db.Column(db.Integer, nullable=False, default=0)
    longest_streak = db.Column(db.Integer, nullable=False, default=0)
    last_activity_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=now, nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=now, onupdate=now, nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_verification_code(self):
        self.email_verification_code = f"{random.randint(100000, 999999)}"
        self.email_verification_expiry = datetime.now(timezone.utc) + timedelta(minutes=15)
        return self.email_verification_code

    def verify_email_code(self, code):
        if not self.email_verification_code or not self.email_verification_expiry:
            return False
        current_time = datetime.now(timezone.utc)
        expiry = self.email_verification_expiry
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
        if current_time > expiry:
            return False
        if self.email_verification_code == code.strip():
            self.is_email_verified = True
            self.email_verification_code = None
            self.email_verification_expiry = None
            return True
        return False

    def is_locked_out(self):
        if not self.lockout_until:
            return False, 0
        current_time = datetime.now(timezone.utc)
        lockout = self.lockout_until
        if lockout.tzinfo is None:
            lockout = lockout.replace(tzinfo=timezone.utc)
        if current_time < lockout:
            diff_seconds = (lockout - current_time).total_seconds()
            remaining_mins = max(1, int(diff_seconds // 60) + (1 if diff_seconds % 60 > 0 else 0))
            return True, remaining_mins
        return False, 0

    def record_failed_login(self):
        self.failed_login_attempts = (self.failed_login_attempts or 0) + 1
        if self.failed_login_attempts >= 5:
            self.lockout_until = datetime.now(timezone.utc) + timedelta(minutes=15)
        return self.failed_login_attempts

    def record_successful_login(self):
        self.failed_login_attempts = 0
        self.lockout_until = None
        self.last_login_at = datetime.now(timezone.utc)

    def generate_reset_token(self):
        self.reset_token = secrets.token_urlsafe(32)
        self.reset_token_expiry = datetime.now(timezone.utc) + timedelta(hours=1)
        return self.reset_token

    def verify_reset_token(self, token):
        if not self.reset_token or not self.reset_token_expiry:
            return False
        if self.reset_token != token:
            return False
        current_time = datetime.now(timezone.utc)
        expiry = self.reset_token_expiry
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
        return current_time <= expiry

    def generate_pending_email_otp(self, new_email):
        self.pending_email = new_email.strip().lower()
        self.pending_email_otp = f"{random.randint(100000, 999999)}"
        self.pending_email_expiry = datetime.now(timezone.utc) + timedelta(minutes=15)
        return self.pending_email_otp

    def verify_pending_email_otp(self, code):
        if not self.pending_email or not self.pending_email_otp or not self.pending_email_expiry:
            return False
        current_time = datetime.now(timezone.utc)
        expiry = self.pending_email_expiry
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
        if current_time > expiry:
            return False
        if self.pending_email_otp == code.strip():
            self.email = self.pending_email
            self.pending_email = None
            self.pending_email_otp = None
            self.pending_email_expiry = None
            return True
        return False

    @property
    def is_admin(self):
        return self.role == "ADMIN"

    def get_current_streak(self):
        """
        Returns active streak count.
        Resets current_streak to 0 if last_activity_date was before yesterday.
        """
        if not self.last_activity_date:
            return 0
        today = date.today()
        yesterday = today - timedelta(days=1)
        if self.last_activity_date < yesterday:
            if self.current_streak != 0:
                self.current_streak = 0
                db.session.commit()
            return 0
        return self.current_streak


class DailyActivity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    activity_date = db.Column(db.Date, nullable=False, default=date.today, index=True)
    completed_lessons = db.Column(db.Integer, nullable=False, default=0)
    goal_completed = db.Column(db.Boolean, nullable=False, default=False)

    user = db.relationship("User", backref=db.backref("daily_activities", lazy="dynamic"))

    __table_args__ = (db.UniqueConstraint("user_id", "activity_date"),)


def record_daily_activity(user, lessons_count=1):
    """
    Records lesson completion activity for the user today.
    Enforces streak business rules:
    - 1 lesson completed -> goal_completed = True
    - Multiple lessons same day -> streak increments only once
    - Consecutive day -> streak += 1
    - Missed day -> streak = 1
    - longest_streak tracks max record
    """
    today = date.today()
    yesterday = today - timedelta(days=1)

    activity = DailyActivity.query.filter_by(user_id=user.id, activity_date=today).first()
    if not activity:
        activity = DailyActivity(user_id=user.id, activity_date=today, completed_lessons=0, goal_completed=False)
        db.session.add(activity)

    activity.completed_lessons += lessons_count

    if activity.completed_lessons >= 1 and not activity.goal_completed:
        activity.goal_completed = True

        if user.last_activity_date == yesterday:
            user.current_streak = (user.current_streak or 0) + 1
        elif user.last_activity_date == today:
            pass  # Already counted today
        else:
            user.current_streak = 1

        user.last_activity_date = today
        if user.current_streak > (user.longest_streak or 0):
            user.longest_streak = user.current_streak

    db.session.commit()
    return activity
