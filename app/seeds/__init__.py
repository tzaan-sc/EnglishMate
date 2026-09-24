"""Database seeding package for EnglishMate.

Provides seed utilities for:
- Base demo lessons, questions, vocabularies, and user accounts.
- Complete TOEIC test suite (Listening & Reading full parts).
"""

from app.seeds.base import seed as seed_base
from app.seeds.toeic import seed_toeic

__all__ = ["seed_base", "seed_toeic"]
