import sys
from pathlib import Path
import click

from flask import Flask, render_template, request, g
from sqlalchemy import event
from sqlalchemy.engine import Engine
import sqlite3

from .config import Config
from .extensions import cors, csrf, db, limiter, login_manager, migrate, swagger, cache, compress


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
    migrate.init_app(app, db, render_as_batch=True)
    compress.init_app(app)
    from .backend.admin.cache_service import cache_service
    cache_service.init_app(app)
    from .backend.admin.error_monitoring_service import init_error_monitoring
    init_error_monitoring(app)
    from .backend.admin.apm_service import init_apm
    init_apm(app)
    from .backend.admin.slow_query_logger import init_slow_query_logger
    init_slow_query_logger(app)
    limiter.init_app(app)
    cors.init_app(
        app,
        resources={
            r"/api/*": {"origins": getattr(config_object, "CORS_ALLOWED_ORIGINS", "*") or "*"},
            r"/static/*": {"origins": "*"},
        },
        supports_credentials=True,
    )
    swagger.init_app(app)
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
    from .backend.api import api_v1_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(learning_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(exams_bp)
    app.register_blueprint(api_v1_bp)

    # Exempt REST API endpoints from CSRF form requirement
    csrf.exempt(api_v1_bp)

    with app.app_context():
        try:
            from .backend.auth import models as _auth_models
            from .backend.learning import models as _learning_models
            from .backend.exams import models as _exams_models
            from .backend.admin import models as _admin_models
            db.create_all()
        except Exception:
            try:
                db.session.rollback()
            except Exception:
                pass

        try:
            from sqlalchemy import inspect, text
            with db.engine.connect() as conn:
                insp = inspect(db.engine)
                existing_tables = set(insp.get_table_names())
                is_pg = "postgresql" in str(db.engine.url)

                for table_key, table in db.metadata.tables.items():
                    t_name = table.name
                    matched_table = None
                    for et in existing_tables:
                        if et.lower() == t_name.lower():
                            matched_table = et
                            break
                    if not matched_table:
                        continue

                    existing_cols = {c["name"].lower() for c in insp.get_columns(matched_table)}
                    for col in table.columns:
                        if col.name.lower() not in existing_cols:
                            try:
                                col_type = col.type.compile(db.engine.dialect)
                                default_sql = ""
                                if col.default is not None and hasattr(col.default, "arg") and not callable(col.default.arg):
                                    default_val = col.default.arg
                                    if isinstance(default_val, bool):
                                        default_sql = f" DEFAULT {'TRUE' if default_val else 'FALSE' if is_pg else '1' if default_val else '0'}"
                                    elif isinstance(default_val, (int, float)):
                                        default_sql = f" DEFAULT {default_val}"
                                    elif isinstance(default_val, str):
                                        default_sql = f" DEFAULT '{default_val}'"

                                if is_pg:
                                    conn.execute(text(f'ALTER TABLE "{matched_table}" ADD COLUMN IF NOT EXISTS "{col.name}" {col_type}{default_sql};'))
                                else:
                                    conn.execute(text(f'ALTER TABLE "{matched_table}" ADD COLUMN "{col.name}" {col_type}{default_sql};'))
                                conn.commit()
                            except Exception:
                                pass
        except Exception:
            try:
                db.session.rollback()
            except Exception:
                pass

    @app.teardown_request
    def cleanup_db_session(exc=None):
        if exc is not None:
            try:
                db.session.rollback()
            except Exception:
                pass

    @app.before_request
    def check_network_security_and_ip_filtering():
        """Kiểm tra IP Blacklist, Admin IP Whitelist, Request Trace ID và Bắt buộc HTTPS (Mục 11.8 - 15.1)."""
        import time
        import uuid
        from flask import request, render_template, g
        g._req_start_time = time.time()

        # 15.1. Error Correlation: Assign unique Request Trace ID to correlate logs & errors
        trace_id = request.headers.get("X-Request-ID") or request.headers.get("X-Correlation-ID")
        if not trace_id:
            trace_id = f"REQ-{uuid.uuid4().hex[:10].upper()}"
        g.request_id = trace_id

        from .backend.admin.network_security import (
            get_client_ip,
            is_ip_blacklisted,
            is_admin_ip_allowed,
            handle_https_enforcement,
            record_blocked_request,
        )

        client_ip = get_client_ip(request)

        # Handle CORS Preflight OPTIONS requests
        if request.method == "OPTIONS":
            from flask import Response
            from .backend.admin.network_security import apply_cors_headers
            res = Response("", status=204)
            return apply_cors_headers(res, req=request)

        # 1. IP Blacklist check
        if is_ip_blacklisted(client_ip):
            record_blocked_request()
            return render_template("errors/403.html"), 403

        # 2. Admin IP Whitelist check
        if request.path.startswith("/admin") and not is_admin_ip_allowed(client_ip):
            record_blocked_request()
            return render_template("errors/403.html"), 403

        # 3. HTTPS Enforcement
        https_redirect = handle_https_enforcement(request)
        if https_redirect:
            return https_redirect

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
            try:
                db.session.rollback()
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
                try:
                    db.session.rollback()
                except Exception:
                    pass
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
                try:
                    db.session.rollback()
                except Exception:
                    pass
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
                try:
                    db.session.rollback()
                except Exception:
                    pass
                g._cached_admin_notif_data = None
        return {"admin_notif_data": g._cached_admin_notif_data}

    @app.context_processor
    def inject_request_trace_id():
        from flask import has_request_context, g
        if not has_request_context():
            return {"request_id": ""}
        return {"request_id": getattr(g, "request_id", "")}

    # Jinja2 Data Masking Template Filters (Mục 11.3)
    from .backend.admin.data_masking import mask_email, mask_ip_address, mask_phone, mask_text

    @app.template_filter("mask_email")
    def _filter_mask_email(val):
        return mask_email(val)

    @app.template_filter("mask_ip")
    def _filter_mask_ip(val, level="medium"):
        return mask_ip_address(val, mask_level=level)

    @app.template_filter("mask_phone")
    def _filter_mask_phone(val):
        return mask_phone(val)

    @app.template_filter("mask_text")
    def _filter_mask_text(val, visible_start=2, visible_end=2):
        return mask_text(val, visible_start=visible_start, visible_end=visible_end)

    @app.after_request
    def set_performance_and_security_headers(response):

        """Thiết lập Cache-Control và HTTP Security Headers bảo vệ an toàn toàn diện hệ thống."""
        from flask import request
        if request.path.startswith("/static/"):
            try:
                from .backend.admin.models import SystemConfig
                max_age = SystemConfig.get_int_config("STATIC_CACHE_MAX_AGE_SECONDS", default=86400)
            except Exception:
                max_age = 86400
            response.headers["Cache-Control"] = f"public, max-age={max_age if max_age is not None else 86400}"

        try:
            from .backend.admin.security_headers import apply_security_headers
            response = apply_security_headers(response, req=request)
        except Exception:
            pass

        try:
            import time
            from flask import g
            from .backend.admin.network_security import apply_cors_headers, record_network_traffic, get_client_ip
            response = apply_cors_headers(response, req=request)

            # 15.1. Attach Request Trace ID to HTTP Response Headers
            if hasattr(g, "request_id") and g.request_id:
                response.headers["X-Request-ID"] = g.request_id

            start_t = getattr(g, "_req_start_time", None)
            duration = ((time.time() - start_t) * 1000) if start_t else 0.0
            record_network_traffic(
                path=request.path,
                ip=get_client_ip(request),
                method=request.method,
                status_code=response.status_code,
                duration_ms=duration
            )
        except Exception:
            pass

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

    @app.cli.command("backup-db")
    @click.option("--type", default="AUTO", type=click.Choice(["AUTO", "DAILY", "WEEKLY", "MANUAL"], case_sensitive=False), help="Loại bản sao lưu (AUTO, DAILY, WEEKLY, MANUAL).")
    @click.option("--notes", default="Tự động sao lưu định kỳ qua CLI/Cron", type=str, help="Ghi chú cho bản sao lưu.")
    def run_backup_db_cli(type, notes):
        """Tự động tạo bản sao lưu CSDL (SQLite/PostgreSQL) nén Gzip qua dòng lệnh."""
        from .backend.admin.backup_service import create_database_backup
        res = create_database_backup(backup_type=type.upper(), notes=notes)
        if res.get("success"):
            click.echo(f"[SUCCESS] {res['message']} (File: {res.get('filename')})")
        else:
            click.echo(f"[ERROR] {res.get('message')}")

    @app.cli.command("restore-db")
    @click.option("--id", "backup_id", required=True, type=int, help="Mã ID của bản sao lưu CSDL cần khôi phục.")
    def run_restore_db_cli(backup_id):
        """Khôi phục CSDL an toàn từ bản sao lưu chỉ định."""
        from .backend.admin.backup_service import restore_database_backup
        res = restore_database_backup(backup_id=backup_id)
        if res.get("success"):
            click.echo(f"[SUCCESS] {res['message']} (Bản sao lưu an toàn tự động: {res.get('safety_backup')})")
        else:
            click.echo(f"[ERROR] {res.get('message')}")

    @app.cli.command("auto-backup-db")
    @click.option("--force", is_flag=True, default=False, help="Bắt buộc chạy sao lưu ngay bỏ qua kiểm tra lịch.")
    def run_auto_backup_db_cli(force):
        """Tác vụ tự động sao lưu CSDL định kỳ (Backup Automation) dùng cho Cron job / Task Scheduler."""
        from .backend.admin.database_service import check_and_run_auto_backup
        res = check_and_run_auto_backup(force=force)
        if res.get("skipped"):
            click.echo(f"[SKIPPED] {res.get('message')}")
        elif res.get("success"):
            click.echo(f"[SUCCESS] {res.get('message')}")
        else:
            click.echo(f"[ERROR] {res.get('message', res.get('error'))}")

    @app.cli.command("auto-restore-db")
    @click.option("--latest", is_flag=True, default=False, help="Tự động khôi phục từ bản sao lưu gần nhất.")
    @click.option("--id", "backup_id", type=int, default=None, help="Mã ID của bản sao lưu chỉ định.")
    @click.option("--confirm", is_flag=True, default=False, help="Xác nhận khôi phục ghi đè dữ liệu hiện tại.")
    def run_auto_restore_db_cli(latest, backup_id, confirm):
        """Kịch bản tự động khôi phục CSDL an toàn từ bản sao lưu (Restore Automation)."""
        if not confirm:
            click.echo("[ABORTED] Vui lòng sử dụng cờ --confirm để xác nhận phục hồi CSDL.")
            return

        from .backend.admin.database_service import auto_restore_database
        res = auto_restore_database(backup_id=backup_id, use_latest=latest)
        if res.get("success"):
            click.echo(f"[SUCCESS] {res.get('message')} (Safety Backup: {res.get('safety_backup')})")
        else:
            click.echo(f"[ERROR] {res.get('message', res.get('error'))}")

    @app.cli.command("db-migration-status")
    def run_db_migration_status_cli():
        """Hiển thị trạng thái phiên bản Migration CSDL (Flask-Migrate / Alembic)."""
        from .backend.admin.database_service import get_migration_status
        status = get_migration_status()
        click.echo(f"Initialized: {status['is_initialized']}")
        click.echo(f"Current DB Revision: {status['current_revision']}")
        click.echo(f"Head Revision: {status['head_revision']}")
        click.echo(f"Up to date: {status['is_up_to_date']}")
        click.echo(f"Total Versions: {status['total_versions']}")

    @app.cli.command("db-upgrade")
    @click.option("--revision", default="head", help="Mục tiêu revision migration cần nâng cấp tới.")
    def run_db_upgrade_cli(revision):
        """Nâng cấp CSDL lên phiên bản migration chỉ định."""
        from .backend.admin.database_service import run_database_upgrade
        res = run_database_upgrade(revision=revision)
        if res.get("success"):
            click.echo(f"[SUCCESS] {res.get('message')}")
        else:
            click.echo(f"[ERROR] {res.get('error')}")

    @app.cli.command("purge-inactive-users")

    @click.option("--days", default=180, type=int, help="Số ngày soft-deleted / không hoạt động để dọn dẹp vĩnh viễn.")
    @click.option("--dry-run", is_flag=True, default=False, help="Chế độ kiểm tra, không xóa thật.")
    def run_purge_inactive_users_cli(days, dry_run):
        """Dọn dẹp vĩnh viễn các tài khoản soft-delete đã quá hạn."""
        from .backend.admin.data_lifecycle_service import purge_soft_deleted_users
        res = purge_soft_deleted_users(days=days, dry_run=dry_run)
        if res.get("dry_run"):
            click.echo(f"[DRY RUN] {res['message']}")
        else:
            click.echo(f"[SUCCESS] {res['message']}")

    @app.cli.command("data-maintenance")
    def run_data_maintenance_cli():
        """Chạy tổng thể quy trình bảo trì vòng đời dữ liệu (Data Lifecycle Maintenance)."""
        from .backend.admin.data_lifecycle_service import run_data_lifecycle_maintenance_job
        res = run_data_lifecycle_maintenance_job()
        click.echo(f"[SUCCESS] {res['message']}")

    @app.cli.command("warm-cache")
    def run_warm_cache_cli():
        """Nạp trước dữ liệu tĩnh bảng xếp hạng, danh mục từ vựng, ngữ pháp vào bộ nhớ Cache."""
        from .backend.admin.cache_service import warm_up_cache
        res = warm_up_cache()
        if res.get("success"):
            click.echo(f"[SUCCESS] Đã nạp trước {res.get('warmed_items_count')} mục vào Cache trong {res.get('duration_ms')}ms.")
        else:
            click.echo(f"[ERROR] Lỗi khi nạp cache: {res.get('error')}")

    @app.cli.command("flush-cache")
    def run_flush_cache_cli():
        """Làm sạch toàn bộ dữ liệu Cache trong hệ thống."""
        from .backend.admin.cache_service import cache_service
        ok = cache_service.flush_all()
        if ok:
            click.echo("[SUCCESS] Đã xóa toàn bộ bộ nhớ Cache.")
        else:
            click.echo("[ERROR] Không thể làm sạch Cache.")

    @app.cli.command("rotate-logs")
    @click.option("--file", "filename", default="app.log", help="Tên file log cần xoay vòng và nén .gz.")
    def run_rotate_logs_cli(filename):
        """Xoay vòng và nén tệp nhật ký ứng dụng."""
        from .backend.admin.log_analysis_service import log_analysis_service
        res = log_analysis_service.rotate_log_file(filename)
        if res.get("success"):
            click.echo(f"[SUCCESS] {res.get('message')}")
        else:
            click.echo(f"[ERROR] {res.get('error')}")

    @app.cli.command("cleanup-system-logs")
    @click.option("--days", default=None, type=int, help="Số ngày lưu trữ tệp log nén.")
    def run_cleanup_system_logs_cli(days):
        """Tự động dọn dẹp các tệp nhật ký lưu trữ quá hạn."""
        from .backend.admin.log_analysis_service import log_analysis_service
        res = log_analysis_service.cleanup_expired_log_archives(retention_days=days)
        click.echo(f"[SUCCESS] {res.get('message')}")


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

    @app.errorhandler(429)
    def ratelimit_error(e):
        from flask import jsonify, request, render_template, g
        if request.path.startswith("/api/") or request.is_json:
            return jsonify({
                "success": False,
                "error": "Too Many Requests",
                "request_id": getattr(g, "request_id", ""),
                "message": f"Bạn đã gửi quá nhiều yêu cầu: {e.description}",
                "retry_after": getattr(e, "retry_after", 60),
            }), 429
        return render_template("errors/429.html", error=e), 429

    @app.errorhandler(500)
    def internal_server_error(error):
        from .backend.admin.error_monitoring_service import record_system_error
        from flask import jsonify, request, g, render_template
        record_system_error(
            exc=getattr(error, "original_exception", error),
            status_code=500,
            severity="CRITICAL",
            custom_message=str(error)
        )
        if request.path.startswith("/api/") or request.is_json:
            return jsonify({
                "success": False,
                "error": "InternalServerError",
                "request_id": getattr(g, "request_id", ""),
                "message": "Đã xảy ra sự cố nội bộ máy chủ. Đội ngũ kỹ thuật đã được thông báo tự động."
            }), 500
        return render_template("errors/500.html", error=error), 500

    @app.cli.command("system-recover")
    @click.option("--force", is_flag=True, default=False, help="Chạy khôi phục toàn diện tất cả dịch vụ.")
    def run_system_recover_cli(force):
        """Tự động kiểm tra và khôi phục hệ thống sau sự cố (Self-Healing Recovery)."""
        from .backend.admin.error_recovery_service import run_system_recovery_diagnostics
        res = run_system_recovery_diagnostics(force_recovery=force)
        click.echo(f"System Recovery Status: {res.get('status')} | DB: {res.get('database', {}).get('status')} | Zombie Tasks Recovered: {res.get('tasks', {}).get('recovered_count', 0)}")

    @app.route("/apidocs")
    @app.route("/api/docs")
    def api_docs_redirect():
        from flask import redirect
        return redirect("/api/v1/docs")

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
