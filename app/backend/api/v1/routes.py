"""
Facade module re-exporting all API v1 endpoints and handlers.
Ensures 100% backward compatibility with test suites and external integrations.
"""
from .routes_meta import api_meta, api_health, api_ping
from .routes_lessons import (
    api_get_lessons,
    api_get_lesson_detail,
    api_get_lesson_skills,
    api_get_lesson_levels,
)
from .routes_vocab import (
    api_get_vocabulary,
    api_get_vocab_detail,
    api_get_vocab_topics,
    api_get_random_vocabulary,
)
from .routes_quizzes import (
    api_get_quizzes,
    api_get_quiz_questions,
    api_get_quiz_topics,
)
from .routes_stats import (
    api_get_platform_stats,
    api_get_user_stats,
)

__all__ = [
    "api_meta",
    "api_health",
    "api_ping",
    "api_get_lessons",
    "api_get_lesson_detail",
    "api_get_lesson_skills",
    "api_get_lesson_levels",
    "api_get_vocabulary",
    "api_get_vocab_detail",
    "api_get_vocab_topics",
    "api_get_random_vocabulary",
    "api_get_quizzes",
    "api_get_quiz_questions",
    "api_get_quiz_topics",
    "api_get_platform_stats",
    "api_get_user_stats",
]
