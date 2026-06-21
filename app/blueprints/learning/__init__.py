from flask import Blueprint

bp = Blueprint("learning", __name__)

from . import routes

