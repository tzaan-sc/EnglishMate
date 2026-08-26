from pathlib import Path

from flask import Flask, render_template

from .config import Config
from .extensions import csrf, db, login_manager


def create_app(config_object=Config):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_object)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Vui lòng đăng nhập để tiếp tục."
    login_manager.login_message_category = "warning"

    from .modules.auth.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    from .modules.main import bp as main_bp
    from .modules.auth import bp as auth_bp
    from .modules.learning import bp as learning_bp
    from .modules.admin import bp as admin_bp
    from .modules.exams import bp as exams_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(learning_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(exams_bp)

    @app.errorhandler(403)
    def forbidden(_error):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("errors/404.html"), 404

    return app

