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
        ("reset_token", "VARCHAR(100)"),
        ("reset_token_expiry", "DATETIME"),
        ("full_name", "VARCHAR(100)"),
        ("avatar", "VARCHAR(255) DEFAULT 'default_avatar.png'"),
        ("pending_email", "VARCHAR(120)"),
        ("pending_email_otp", "VARCHAR(6)"),
        ("pending_email_expiry", "DATETIME"),
        ("daily_vocab_goal", "INTEGER NOT NULL DEFAULT 20"),
        ("vocab_review_priority", "VARCHAR(20) NOT NULL DEFAULT 'due_date'"),
        ("vocab_auto_play_audio", "BOOLEAN NOT NULL DEFAULT 1"),
        ("vocab_accent", "VARCHAR(10) NOT NULL DEFAULT 'en-US'"),
        ("vocab_display_mode", "VARCHAR(20) NOT NULL DEFAULT 'flashcard'"),
        ("vocab_review_time", "VARCHAR(20) NOT NULL DEFAULT 'anytime'"),
        ("vocab_srs_algorithm", "VARCHAR(20) NOT NULL DEFAULT 'standard'"),
        ("vocab_notify_review_due", "BOOLEAN NOT NULL DEFAULT 1"),
    ]

    for col_name, col_type in new_cols:
        if col_name not in existing_cols:
            print(f"Adding column {col_name}...")
            cursor.execute(f"ALTER TABLE user ADD COLUMN {col_name} {col_type}")

    conn.commit()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_session (
        id VARCHAR(64) PRIMARY KEY,
        user_id INTEGER NOT NULL,
        ip_address VARCHAR(45),
        user_agent VARCHAR(255),
        device_info VARCHAR(100),
        last_activity DATETIME NOT NULL,
        created_at DATETIME NOT NULL,
        is_active BOOLEAN NOT NULL DEFAULT 1,
        FOREIGN KEY (user_id) REFERENCES user (id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS permission (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(64) UNIQUE NOT NULL,
        description VARCHAR(255),
        category VARCHAR(50) NOT NULL DEFAULT 'General'
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS role (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(50) UNIQUE NOT NULL,
        description VARCHAR(255),
        is_custom BOOLEAN NOT NULL DEFAULT 0,
        parent_id INTEGER,
        FOREIGN KEY (parent_id) REFERENCES role (id) ON DELETE SET NULL
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS role_permission (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        role_id INTEGER NOT NULL,
        permission_id INTEGER NOT NULL,
        FOREIGN KEY (role_id) REFERENCES role (id) ON DELETE CASCADE,
        FOREIGN KEY (permission_id) REFERENCES permission (id) ON DELETE CASCADE,
        UNIQUE(role_id, permission_id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_role (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        role_id INTEGER NOT NULL,
        expires_at DATETIME,
        created_at DATETIME NOT NULL,
        FOREIGN KEY (user_id) REFERENCES user (id) ON DELETE CASCADE,
        FOREIGN KEY (role_id) REFERENCES role (id) ON DELETE CASCADE,
        UNIQUE(user_id, role_id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        action VARCHAR(100) NOT NULL,
        target_type VARCHAR(50),
        target_id VARCHAR(50),
        details TEXT,
        ip_address VARCHAR(45),
        created_at DATETIME NOT NULL,
        FOREIGN KEY (user_id) REFERENCES user (id) ON DELETE SET NULL
    )
    """)
    conn.commit()

    # Seed default permissions if empty
    cursor.execute("SELECT COUNT(*) FROM permission")
    if cursor.fetchone()[0] == 0:
        default_permissions = [
            ("lessons:read", "Xem bài học", "Lessons"),
            ("lessons:write", "Tạo và sửa bài học", "Lessons"),
            ("lessons:delete", "Xóa bài học", "Lessons"),
            ("vocabulary:manage", "Quản lý từ vựng", "Vocabulary"),
            ("exams:manage", "Quản lý đề thi & bài tập", "Exams"),
            ("users:manage", "Quản lý người dùng & phân vai trò", "Users"),
            ("roles:manage", "Quản lý vai trò & quyền hạn", "Security"),
            ("audit:read", "Xem nhật ký kiểm tra hệ thống", "Security"),
        ]
        cursor.executemany("INSERT INTO permission (name, description, category) VALUES (?, ?, ?)", default_permissions)
        conn.commit()

    # Seed default roles if empty
    cursor.execute("SELECT COUNT(*) FROM role")
    if cursor.fetchone()[0] == 0:
        default_roles = [
            ("ADMIN", "Quản trị viên toàn quyền hệ thống", 0, None),
            ("MODERATOR", "Kiểm duyệt viên quản lý nội dung bài học & từ vựng", 0, None),
            ("USER", "Học viên thông thường", 0, None),
        ]
        cursor.executemany("INSERT INTO role (name, description, is_custom, parent_id) VALUES (?, ?, ?, ?)", default_roles)
        conn.commit()

        # Assign MODERATOR permissions (lessons:read, lessons:write, vocabulary:manage, exams:manage)
        cursor.execute("SELECT id FROM role WHERE name = 'MODERATOR'")
        mod_role_id = cursor.fetchone()[0]
        cursor.execute("SELECT id FROM permission WHERE name IN ('lessons:read', 'lessons:write', 'vocabulary:manage', 'exams:manage')")
        mod_perms = [row[0] for row in cursor.fetchall()]
        cursor.executemany("INSERT INTO role_permission (role_id, permission_id) VALUES (?, ?)", [(mod_role_id, p_id) for p_id in mod_perms])
        conn.commit()

    # Patch vocabulary table columns
    cursor.execute("PRAGMA table_info(vocabulary)")
    vocab_cols = [row[1] for row in cursor.fetchall()]
    new_vocab_cols = [
        ("image_url", "VARCHAR(255)"),
        ("collocations", "VARCHAR(300)"),
        ("synonyms", "VARCHAR(200)"),
        ("antonyms", "VARCHAR(200)"),
    ]
    for col_name, col_type in new_vocab_cols:
        if col_name not in vocab_cols:
            cursor.execute(f"ALTER TABLE vocabulary ADD COLUMN {col_name} {col_type}")

    # Patch vocabulary_progress table columns
    cursor.execute("PRAGMA table_info(vocabulary_progress)")
    vp_cols = [row[1] for row in cursor.fetchall()]
    new_vp_cols = [
        ("is_favorite", "BOOLEAN NOT NULL DEFAULT 0"),
        ("is_skipped", "BOOLEAN NOT NULL DEFAULT 0"),
        ("srs_level", "INTEGER NOT NULL DEFAULT 1"),
        ("next_review_at", "DATETIME DEFAULT CURRENT_TIMESTAMP"),
        ("personal_notes", "TEXT"),
        ("custom_example", "TEXT"),
    ]
    for col_name, col_type in new_vp_cols:
        if col_name not in vp_cols:
            cursor.execute(f"ALTER TABLE vocabulary_progress ADD COLUMN {col_name} {col_type}")

    # Create word_report table if not exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS word_report (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            vocabulary_id INTEGER NOT NULL,
            reason VARCHAR(255) NOT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES user (id),
            FOREIGN KEY (vocabulary_id) REFERENCES vocabulary (id)
        )
    """)

    # Patch lesson table (thumbnail_url, view_count)
    cursor.execute("PRAGMA table_info(lesson)")
    existing_lesson_cols = [row[1] for row in cursor.fetchall()]
    if "thumbnail_url" not in existing_lesson_cols:
        cursor.execute("ALTER TABLE lesson ADD COLUMN thumbnail_url VARCHAR(255)")
    if "view_count" not in existing_lesson_cols:
        cursor.execute("ALTER TABLE lesson ADD COLUMN view_count INTEGER NOT NULL DEFAULT 0")

    # Create lesson_favorite table if not exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lesson_favorite (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            lesson_id INTEGER NOT NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES user (id),
            FOREIGN KEY (lesson_id) REFERENCES lesson (id),
            UNIQUE (user_id, lesson_id)
        )
    """)

    # Create lesson_note table if not exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lesson_note (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            lesson_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES user (id),
            FOREIGN KEY (lesson_id) REFERENCES lesson (id),
            UNIQUE (user_id, lesson_id)
        )
    """)

    # Create lesson_bookmark table if not exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lesson_bookmark (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            lesson_id INTEGER NOT NULL,
            section_index INTEGER NOT NULL DEFAULT 1,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES user (id),
            FOREIGN KEY (lesson_id) REFERENCES lesson (id),
            UNIQUE (user_id, lesson_id, section_index)
        )
    """)

    # Create lesson_report table if not exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lesson_report (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            lesson_id INTEGER NOT NULL,
            reason VARCHAR(100) NOT NULL,
            details TEXT,
            status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES user (id),
            FOREIGN KEY (lesson_id) REFERENCES lesson (id)
        )
    """)
    conn.commit()

    conn.close()
    print("Database patched successfully with Vocabulary Learning & Lesson Content enhancements!")
else:
    print("Database file not found at", db_path)
