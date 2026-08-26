from flask import Blueprint

bp = Blueprint("exams", __name__)

from . import routes
