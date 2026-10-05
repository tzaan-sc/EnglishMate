from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
from flasgger import Swagger

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
migrate = Migrate()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "60 per minute"],
    storage_uri="memory://",
    headers_enabled=True,
)
cors = CORS()
swagger = Swagger(
    template={
        "swagger": "2.0",
        "info": {
            "title": "EnglishMate REST API",
            "description": "Interactive OpenAPI/Swagger documentation for EnglishMate learning platform, vocabulary, lessons, and exam systems.",
            "version": "1.0.0",
            "contact": {
                "name": "EnglishMate Team",
                "email": "support@englishmate.vn"
            }
        },
        "basePath": "/api/v1",
        "schemes": ["http", "https"],
        "consumes": ["application/json"],
        "produces": ["application/json"],
    },
    config={
        "headers": [],
        "specs": [
            {
                "endpoint": "apispec_v1",
                "route": "/api/v1/apispec.json",
                "rule_filter": lambda rule: rule.endpoint.startswith("api_v1."),
                "model_filter": lambda tag: True,
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/api/v1/docs",
    }
)

