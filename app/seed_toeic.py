"""Database seeding entry point for TOEIC practice test.

This file provides backward compatibility for CLI command:
    python -m app.seed_toeic
The actual seed logic is maintained in app.seeds.toeic.
"""

from app.seeds.toeic import seed_toeic

if __name__ == "__main__":
    seed_toeic()
