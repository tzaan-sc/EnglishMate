import sys
from pathlib import Path

from flask import Flask, render_template

from .config import Config
from .extensions import csrf, db, login_manager


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
                        if "vocab_reminder_enabled" not in cols:
                            conn.execute(text('ALTER TABLE "user" ADD COLUMN vocab_reminder_enabled BOOLEAN DEFAULT 1;'))
                            conn.commit()
                        if "vocab_reminder_time" not in cols:
                            conn.execute(text('ALTER TABLE "user" ADD COLUMN vocab_reminder_time VARCHAR(10) DEFAULT \'09:00\';'))
                            conn.commit()
                        if "vocab_push_subscription" not in cols:
                            conn.execute(text('ALTER TABLE "user" ADD COLUMN vocab_push_subscription TEXT;'))
                            conn.commit()
                    if "lesson_progress" in tables:
                        cols = [c["name"] for c in insp.get_columns("lesson_progress")]
                        if "duration_seconds" not in cols:
                            conn.execute(text("ALTER TABLE lesson_progress ADD COLUMN duration_seconds INTEGER DEFAULT 0;"))
                            conn.commit()
        except Exception:
            pass

    @app.context_processor
    def inject_streak_event():
        from flask import session
        return {"streak_activated_event": session.pop("streak_activated_popup", None)}

    @app.context_processor
    def inject_admin_notifications():
        from flask_login import current_user
        if not current_user.is_authenticated or not getattr(current_user, "is_admin", False):
            return {"admin_notif_data": None}
        try:
            from .backend.auth.models import User
            from .backend.learning.models import QuizAttempt
            from .backend.admin.models import AuditLog
            locked_users = User.query.filter((User.failed_login_attempts >= 5) | (User.is_active == False)).count()
            total_attempts = QuizAttempt.query.count()
            latest_audit = AuditLog.query.order_by(AuditLog.id.desc()).first()
            return {
                "admin_notif_data": {
                    "locked_users": locked_users,
                    "total_attempts": total_attempts,
                    "latest_audit": latest_audit,
                }
            }
        except Exception:
            return {"admin_notif_data": None}

    @app.errorhandler(403)
    def forbidden(_error):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("errors/404.html"), 404

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
