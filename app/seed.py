"""Database seeding entry point for base demo data.

This file provides backward compatibility for CLI command:
    python -m app.seed
The actual seed logic is maintained in app.seeds.base.
"""

from app.seeds.base import seed, LESSONS, VOCAB_GROUPS, build_vocabulary

if __name__ == "__main__":
    seed()
