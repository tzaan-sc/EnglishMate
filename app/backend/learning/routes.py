"""
Master routes module for the Learning Blueprint.

This module re-exports all endpoints and helper functions from specialized submodules:
- routes_lessons.py: Lessons catalog, detail, notes, rating, speaking/writing AI evaluation, annotations.
- routes_vocab.py: Vocabulary catalog, flashcard sets, study mode, review, settings, notifications.
- routes_games.py: Learning game lobby, word match, speed quiz, spelling bee.
- routes_grammar.py: Grammar topics, exercises, reference handbook, PDF/DOCX export.
- routes_quiz.py: Quiz dashboard, test sessions, answer evaluation, results sharing, PDF report.
- routes_gamification.py: XP rewards, user badges, daily challenges, leaderboard.
"""

from .routes_gamification import *  # noqa: F401, F403
from .routes_quiz import *  # noqa: F401, F403
from .routes_grammar import *  # noqa: F401, F403
from .routes_games import *  # noqa: F401, F403
from .routes_vocab import *  # noqa: F401, F403
from .routes_lessons import *  # noqa: F401, F403

# Re-export internal helpers for backward-compatibility with tests & other modules
from .routes_lessons import _calculate_word_similarity, _render_lesson_page  # noqa: F401
from .routes_vocab import _clone_flashcard_set  # noqa: F401
