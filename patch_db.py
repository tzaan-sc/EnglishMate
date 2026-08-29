import sqlite3
from pathlib import Path

db_path = Path(__file__).parent / "instance" / "englishmate.db"

if db_path.exists():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(user)")
    existing_cols = [row[1] for row in cursor.fetchall()]

    new_cols = [
        ("is_email_verified", "BOOLEAN NOT NULL DEFAULT 0"),
        ("email_verification_code", "VARCHAR(6)"),
        ("email_verification_expiry", "DATETIME"),
        ("oauth_provider", "VARCHAR(20)"),
        ("oauth_id", "VARCHAR(100)"),
        ("failed_login_attempts", "INTEGER NOT NULL DEFAULT 0"),
        ("lockout_until", "DATETIME"),
        ("last_login_at", "DATETIME"),
    ]

    for col_name, col_type in new_cols:
        if col_name not in existing_cols:
            print(f"Adding column {col_name}...")
            cursor.execute(f"ALTER TABLE user ADD COLUMN {col_name} {col_type}")

    conn.commit()
    conn.close()
    print("Database patched successfully!")
else:
    print("Database file not found at", db_path)
