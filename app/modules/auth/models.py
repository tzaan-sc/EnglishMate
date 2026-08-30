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
    daily_vocab_goal = db.Column(db.Integer, nullable=False, default=20)
    vocab_review_priority = db.Column(db.String(20), nullable=False, default="due_date")
    vocab_auto_play_audio = db.Column(db.Boolean, nullable=False, default=True)
    vocab_accent = db.Column(db.String(10), nullable=False, default="en-US")
    vocab_display_mode = db.Column(db.String(20), nullable=False, default="flashcard")
    vocab_review_time = db.Column(db.String(20), nullable=False, default="anytime")
    vocab_srs_algorithm = db.Column(db.String(20), nullable=False, default="standard")
    vocab_notify_review_due = db.Column(db.Boolean, nullable=False, default=True)
    
    # Exam Settings
    exam_default_type = db.Column(db.String(50), nullable=False, default="TOEIC")
    exam_default_time_limit = db.Column(db.Integer, nullable=False, default=120)
    exam_show_timer = db.Column(db.Boolean, nullable=False, default=True)
    exam_allow_pause = db.Column(db.Boolean, nullable=False, default=True)
    exam_show_realtime_score = db.Column(db.Boolean, nullable=False, default=False)
    exam_auto_submit = db.Column(db.Boolean, nullable=False, default=True)
    exam_sound_effects = db.Column(db.Boolean, nullable=False, default=True)
    
    # Gamification
    xp = db.Column(db.Integer, nullable=False, default=0)
    level = db.Column(db.Integer, nullable=False, default=1)
    daily_goal_xp = db.Column(db.Integer, nullable=False, default=50)
    daily_reward_claimed_date = db.Column(db.Date, nullable=True)
    
    created_at = db.Column(db.DateTime(timezone=True), default=now, nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=now, onupdate=now, nullable=False)

    def get_level(self):
        LEVEL_TIERS = [
            (1, 0, 100, "Tân thủ"),
            (2, 100, 250, "Tập sự"),
            (3, 250, 500, "Chăm chỉ"),
            (4, 500, 1000, "Tiến bộ"),
            (5, 1000, 2000, "Cao thủ"),
            (6, 2000, 3500, "Chuyên gia"),
            (7, 3500, 6000, "Bậc thầy"),
            (8, 6000, 10000, "Huyền thoại"),
            (9, 10000, 999999, "Thần đồng"),
        ]
        xp_val = self.xp or 0
        lvl = 1
        for level_num, min_xp, max_xp, title in LEVEL_TIERS:
            if xp_val >= min_xp:
                lvl = level_num
            else:
                break
        if self.level != lvl:
            self.level = lvl
            try:
                db.session.commit()
            except Exception:
                pass
        return lvl

    def get_level_info(self):
        LEVEL_TIERS = [
            (1, 0, 100, "Tân thủ"),
            (2, 100, 250, "Tập sự"),
            (3, 250, 500, "Chăm chỉ"),
            (4, 500, 1000, "Tiến bộ"),
            (5, 1000, 2000, "Cao thủ"),
            (6, 2000, 3500, "Chuyên gia"),
            (7, 3500, 6000, "Bậc thầy"),
            (8, 6000, 10000, "Huyền thoại"),
            (9, 10000, 999999, "Thần đồng"),
        ]
        xp_val = self.xp or 0
        current_tier = LEVEL_TIERS[0]
        for tier in LEVEL_TIERS:
            if xp_val >= tier[1]:
                current_tier = tier
            else:
                break
        
        lvl, min_xp, max_xp, title = current_tier
        if max_xp == 999999:
            pct = 100
            needed = 0
        else:
            pct = min(100, max(0, int(((xp_val - min_xp) / (max_xp - min_xp)) * 100)))
            needed = max(0, max_xp - xp_val)
            
        return {
            "level": lvl,
            "title": title,
            "current_xp": xp_val,
            "min_xp": min_xp,
            "max_xp": max_xp,
            "progress_pct": pct,
            "needed_xp": needed
        }

    def add_xp(self, amount, reason=None):
        if amount <= 0:
            return 0
        self.xp = (self.xp or 0) + amount
        self.get_level()
        try:
            db.session.commit()
        except Exception:
            pass
        return amount

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

    user.add_xp(lessons_count * 20, reason="Hoàn thành bài học / Luyện tập")
    try:
        from ..learning.routes import update_challenge_progress
        update_challenge_progress(user, "lesson", lessons_count)
        update_challenge_progress(user, "streak", user.current_streak or 1)
    except Exception:
        pass

    db.session.commit()
    return activity


class UserSession(db.Model):
    id = db.Column(db.String(64), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    device_info = db.Column(db.String(100), nullable=True)
    last_activity = db.Column(db.DateTime(timezone=True), default=now, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=now, nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    user = db.relationship("User", backref=db.backref("user_sessions", cascade="all, delete-orphan", lazy="dynamic"))


def parse_device_info(user_agent_str):
    if not user_agent_str:
        return "Thiết bị không xác định"
    ua = user_agent_str.lower()
    browser = "Trình duyệt"
    if "chrome" in ua and "edg" not in ua:
        browser = "Chrome"
    elif "edg" in ua:
        browser = "Edge"
    elif "firefox" in ua:
        browser = "Firefox"
    elif "safari" in ua and "chrome" not in ua:
        browser = "Safari"

    os_name = "HĐH"
    if "windows" in ua:
        os_name = "Windows"
    elif "mac os" in ua or "macintosh" in ua:
        os_name = "macOS"
    elif "android" in ua:
        os_name = "Android"
    elif "iphone" in ua or "ipad" in ua:
        os_name = "iOS"
    elif "linux" in ua:
        os_name = "Linux"

    return f"{browser} trên {os_name}"


def create_or_update_user_session(user_id, session_id, ip_address, user_agent_str):
    if not session_id:
        return None
    user_sess = db.session.get(UserSession, session_id)
    device_info = parse_device_info(user_agent_str)
    if not user_sess:
        user_sess = UserSession(
            id=session_id,
            user_id=user_id,
            ip_address=ip_address or "127.0.0.1",
            user_agent=(user_agent_str or "")[:255],
            device_info=device_info,
            last_activity=datetime.now(timezone.utc),
            is_active=True,
        )
        db.session.add(user_sess)
    else:
        user_sess.last_activity = datetime.now(timezone.utc)
        user_sess.is_active = True
        user_sess.ip_address = ip_address or user_sess.ip_address
        user_sess.device_info = device_info
    db.session.commit()
    return user_sess
