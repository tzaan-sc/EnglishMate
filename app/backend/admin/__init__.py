from flask import Blueprint

bp = Blueprint("admin", __name__, url_prefix="/admin")

from . import routes
from . import routes_system
from . import routes_errors
from . import routes_apm
from . import routes_monitoring

