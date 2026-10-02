from flask import Blueprint

bp = Blueprint("learning", __name__)

from . import routes_gamification
from . import routes_quiz
from . import routes_grammar
from . import routes_games
from . import routes_vocab
from . import routes_lessons
from . import routes
