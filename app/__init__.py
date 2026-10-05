import sys
from pathlib import Path
import click

from flask import Flask, render_template, request, g
from sqlalchemy import event
from sqlalchemy.engine import Engine
import sqlite3

from .config import Config
from .extensions import csrf, db, login_manager


@event.listens_for(Engine, "connect")
def _set_sqlite_pragmas(dbapi_connection, connection_record):
    """Tối ưu hóa hiệu năng SQLite: WAL mode, memory temp_store, cache 64MB, fast synchronous."""
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA journal_mode=WAL")
        except Exception:
            pass
        try:
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA cache_size=-64000")  # 64MB Cache
            cursor.execute("PRAGMA temp_store=MEMORY")
            cursor.execute("PRAGMA mmap_size=268435456")  # 256MB memory-mapped IO
        except Exception:
            pass
        finally:
            cursor.close()


def create_app(config_object=Config):
    app = Flask(
        __name__,
        instance_relative_config=True,
        template_folder="frontend/templates",
        static_folder="frontend/static",
    )
    app.config.from_object(config_object)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Vui lòng đăng nhập để tiếp tục."
    login_manager.login_message_category = "warning"

    from .backend.auth.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    from .backend.main import bp as main_bp
    from .backend.auth import bp as auth_bp
    from .backend.learning import bp as learning_bp
    from .backend.admin import bp as admin_bp
    from .backend.exams import bp as exams_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(learning_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(exams_bp)

    with app.app_context():
        try:
            from sqlalchemy import inspect, text
            with db.engine.connect() as conn:
                is_pg = "postgresql" in str(db.engine.url)
                if is_pg:
                    conn.execute(text("ALTER TABLE exam ADD COLUMN IF NOT EXISTS part_distribution JSON;"))
                    conn.execute(text("ALTER TABLE lesson ADD COLUMN IF NOT EXISTS skill_data JSON;"))
                    conn.execute(text('ALTER TABLE "user" ADD COLUMN IF NOT EXISTS vocab_reminder_enabled BOOLEAN DEFAULT TRUE;'))
                    conn.execute(text('ALTER TABLE "user" ADD COLUMN IF NOT EXISTS vocab_reminder_time VARCHAR(10) DEFAULT \'09:00\';'))
                    conn.execute(text('ALTER TABLE "user" ADD COLUMN IF NOT EXISTS vocab_push_subscription TEXT;'))
                    conn.execute(text('ALTER TABLE "user" ADD COLUMN IF NOT EXISTS streak_freeze_count INTEGER DEFAULT 0;'))
                    conn.execute(text("ALTER TABLE lesson_progress ADD COLUMN IF NOT EXISTS duration_seconds INTEGER DEFAULT 0;"))
                    conn.commit()
                elif "sqlite" in str(db.engine.url):
                    insp = inspect(db.engine)
                    tables = insp.get_table_names()
                    if "exam" in tables:
                        cols = [c["name"] for c in insp.get_columns("exam")]
                        if "part_distribution" not in cols:
                            conn.execute(text("ALTER TABLE exam ADD COLUMN part_distribution JSON;"))
                            conn.commit()
                    if "lesson" in tables:
                        cols = [c["name"] for c in insp.get_columns("lesson")]
                        if "skill_data" not in cols:
                            conn.execute(text("ALTER TABLE lesson ADD COLUMN skill_data JSON;"))
                            conn.commit()
                    if "user" in tables:
                        cols = [c["name"] for c in insp.get_columns("user")]
                        if "streak_freeze_count" not in cols:
                            conn.execute(text('ALTER TABLE "user" ADD COLUMN streak_freeze_count INTEGER DEFAULT 0;'))
                            conn.commit()
                        if "vocab_reminder_enabled" not in cols:
                            conn.execute(text('ALTER TABLE "user" ADD COLUMN vocab_reminder_enabled BOOLEAN DEFAULT 1;'))
                            conn.commit()
                        if "vocab_reminder_time" not in cols:
                            conn.execute(text('ALTER TABLE "user" ADD COLUMN vocab_reminder_time VARCHAR(10) DEFAULT \'09:00\';'))
                            conn.commit()
                        if "vocab_push_subscription" not in cols:
                            conn.execute(text('ALTER TABLE "user" ADD COLUMN vocab_push_subscription TEXT;'))
                            conn.commit()
                        if "daily_goal_reminder_enabled" not in cols:
                            conn.execute(text('ALTER TABLE "user" ADD COLUMN daily_goal_reminder_enabled BOOLEAN DEFAULT 1;'))
                            conn.commit()
                        if "daily_goal_reminder_time" not in cols:
                            conn.execute(text('ALTER TABLE "user" ADD COLUMN daily_goal_reminder_time VARCHAR(10) DEFAULT \'20:00\';'))
                            conn.commit()
                        if "daily_goal_reminder_email" not in cols:
                            conn.execute(text('ALTER TABLE "user" ADD COLUMN daily_goal_reminder_email BOOLEAN DEFAULT 1;'))
                            conn.commit()
                        if "daily_goal_reminder_popup" not in cols:
                            conn.execute(text('ALTER TABLE "user" ADD COLUMN daily_goal_reminder_popup BOOLEAN DEFAULT 1;'))
                            conn.commit()
                        if "last_daily_goal_reminder_date" not in cols:
                            conn.execute(text('ALTER TABLE "user" ADD COLUMN last_daily_goal_reminder_date DATE;'))
                            conn.commit()
                    if "lesson_progress" in tables:
                        cols = [c["name"] for c in insp.get_columns("lesson_progress")]
                        if "duration_seconds" not in cols:
                            conn.execute(text("ALTER TABLE lesson_progress ADD COLUMN duration_seconds INTEGER DEFAULT 0;"))
                            conn.commit()
                    if "lesson_rating" not in tables:
                        from app.backend.learning.models import LessonRating
                        LessonRating.__table__.create(conn)
                        conn.commit()
                    if "system_setting" not in tables:
                        from app.backend.admin.models import SystemSetting
                        SystemSetting.__table__.create(conn)
                        conn.commit()
                    if "system_config" not in tables:
                        from app.backend.admin.models import SystemConfig
                        SystemConfig.__table__.create(conn)
                        conn.commit()
        except Exception:
            pass

    @app.before_request
    def check_maintenance_mode():
        """
        Intercepts incoming requests during System Maintenance Mode.
        - Allows Admin users (current_user.is_admin) to bypass and access the entire system.
        - Excludes static files, auth login/logout, health checks, and dev live reload.
        - Returns 503 Maintenance Page (or JSON error) for all other users.
        """
        from flask import request, render_template, g, jsonify
        from flask_login import current_user

        path = request.path
        if (
            path.startswith("/static/")
            or path.startswith("/auth/login")
            or path.startswith("/auth/logout")
            or path.startswith("/_dev_live_reload_check")
            or path == "/favicon.ico"
        ):
            return None

        is_admin = current_user.is_authenticated and (getattr(current_user, "is_admin", False) or getattr(current_user, "role", "") == "ADMIN")
        if is_admin:
            return None

        try:
            from .backend.admin.models import SystemSetting
            if not hasattr(g, "_is_maintenance_mode"):
                g._is_maintenance_mode = SystemSetting.get_bool_setting("MAINTENANCE_MODE", default=False)
                g._maintenance_message = SystemSetting.get_setting(
                    "MAINTENANCE_MESSAGE",
                    default="Hệ thống EnglishMate đang được bảo trì định kỳ để nâng cấp hiệu năng và cơ sở dữ liệu."
                )
                g._maintenance_estimated_end = SystemSetting.get_setting("MAINTENANCE_ESTIMATED_END", default="")

            if g._is_maintenance_mode:
                if request.is_json or path.startswith("/api/"):
                    return jsonify({
                        "error": "maintenance_mode",
                        "message": g._maintenance_message,
                        "estimated_end": g._maintenance_estimated_end
                    }), 503
                return render_template(
                    "errors/maintenance.html",
                    message=g._maintenance_message,
                    estimated_end=g._maintenance_estimated_end
                ), 503
        except Exception:
            pass

    @app.context_processor
    def inject_maintenance_mode():
        from flask import has_request_context, g
        if not has_request_context():
            return {"is_system_in_maintenance": False}
        if not hasattr(g, "_is_maintenance_mode"):
            try:
                from .backend.admin.models import SystemSetting
                g._is_maintenance_mode = SystemSetting.get_bool_setting("MAINTENANCE_MODE", default=False)
            except Exception:
                g._is_maintenance_mode = False
        return {"is_system_in_maintenance": g._is_maintenance_mode}

    @app.context_processor
    def inject_feature_flags():
        from .backend.admin.feature_flags import is_feature_enabled
        return {"is_feature_enabled": is_feature_enabled}

    @app.context_processor
    def inject_streak_event():
        from flask import has_request_context, session
        if not has_request_context():
            return {"streak_activated_event": None}
        return {"streak_activated_event": session.pop("streak_activated_popup", None)}

    @app.context_processor
    def inject_daily_goal_stat():
        from flask import has_request_context, g
        from flask_login import current_user
        if not has_request_context() or not current_user.is_authenticated or getattr(current_user, "is_admin", False):
            return {"daily_goal_stat": None}
        if not hasattr(g, "_cached_daily_goal_stat"):
            try:
                g._cached_daily_goal_stat = current_user.get_daily_goal_info()
            except Exception:
                g._cached_daily_goal_stat = None
        return {"daily_goal_stat": g._cached_daily_goal_stat}

    @app.context_processor
    def inject_admin_notifications():
        from flask import has_request_context, g
        from flask_login import current_user
        if not has_request_context() or not current_user.is_authenticated or not getattr(current_user, "is_admin", False):
            return {"admin_notif_data": None}
        if not hasattr(g, "_cached_admin_notif_data"):
            try:
                from .backend.auth.models import User
                from .backend.learning.models import QuizAttempt
                from .backend.admin.models import AuditLog
                locked_users = User.query.filter((User.failed_login_attempts >= 5) | (User.is_active == False)).count()
                total_attempts = QuizAttempt.query.count()
                latest_audit = AuditLog.query.order_by(AuditLog.id.desc()).first()
                g._cached_admin_notif_data = {
                    "locked_users": locked_users,
                    "total_attempts": total_attempts,
                    "latest_audit": latest_audit,
                }
            except Exception:
                g._cached_admin_notif_data = None
        return {"admin_notif_data": g._cached_admin_notif_data}

    @app.after_request
    def set_performance_headers(response):
        """Thiết lập Cache-Control cho file tĩnh để tăng tốc độ tải trang phía client dựa trên cấu hình hiệu năng."""
        from flask import request
        if request.path.startswith("/static/"):
            try:
                from .backend.admin.models import SystemConfig
                max_age = SystemConfig.get_int_config("STATIC_CACHE_MAX_AGE_SECONDS", default=86400)
            except Exception:
                max_age = 86400
            response.headers["Cache-Control"] = f"public, max-age={max_age if max_age is not None else 86400}"
        return response


    @app.cli.command("goal-reminders-check")
    def run_goal_reminders_cli():
        """Command to run automated Daily Goal email reminders for learners who have not completed daily goal."""
        from .backend.learning.goal_reminder import send_daily_goal_reminders
        stats = send_daily_goal_reminders(force=False)
        print(f"Goal reminders check finished: {stats}")

    @app.cli.command("cleanup-logs")
    @click.option("--days", default=None, type=int, help="Số ngày lưu trữ log (mặc định lấy từ cấu hình SystemSetting hoặc 90 ngày).")
    @click.option("--archive-path", default=None, type=str, help="Đường dẫn file CSV để xuất lưu trữ trước khi xóa.")
    @click.option("--dry-run", is_flag=True, default=False, help="Chỉ kiểm tra và đếm số bản ghi sẽ bị xóa mà không xóa thật.")
    def run_cleanup_logs_cli(days, archive_path, dry_run):
        """Tự động dọn dẹp hoặc lưu trữ các bản ghi nhật ký kiểm tra (Audit Logs) cũ."""
        from .backend.admin.log_service import cleanup_audit_logs
        res = cleanup_audit_logs(days=days, archive_path=archive_path, dry_run=dry_run)
        if res.get("dry_run"):
            click.echo(f"[DRY RUN] {res['message']} (Cutoff: {res['cutoff_date']})")
        else:
            click.echo(f"[SUCCESS] {res['message']}")
            if res.get("archived_file"):
                click.echo(f"  Archive saved to: {res['archived_file']}")

    @app.errorhandler(403)
    def forbidden(_error):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(503)
    def maintenance_error(_error):
        from .backend.admin.models import SystemSetting
        msg = SystemSetting.get_setting("MAINTENANCE_MESSAGE", "Hệ thống EnglishMate đang được bảo trì định kỳ.")
        est = SystemSetting.get_setting("MAINTENANCE_ESTIMATED_END", "")
        return render_template("errors/maintenance.html", message=msg, estimated_end=est), 503

    @app.route("/_dev_live_reload_check")
    def dev_live_reload_check():
        import os
        from flask import jsonify
        base = Path(__file__).resolve().parent
        max_mtime = 0
        for check_dir in [base / "frontend" / "templates", base / "frontend" / "static"]:
            for root, dirs, files in os.walk(check_dir):
                if "uploads" in root:
                    continue
                for f in files:
                    fp = os.path.join(root, f)
                    try:
                        mt = os.path.getmtime(fp)
                        if mt > max_mtime:
                            max_mtime = mt
                    except OSError:
                        pass
        return jsonify({"timestamp": max_mtime})

    return app
