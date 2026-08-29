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

    # Patch quiz_attempt table (duration_seconds)
    cursor.execute("PRAGMA table_info(quiz_attempt)")
    existing_quiz_cols = [row[1] for row in cursor.fetchall()]
    if "duration_seconds" not in existing_quiz_cols:
        cursor.execute("ALTER TABLE quiz_attempt ADD COLUMN duration_seconds INTEGER NOT NULL DEFAULT 0")

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

    # Create grammar_topic table if not exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS grammar_topic (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title VARCHAR(160) NOT NULL,
            category VARCHAR(80) NOT NULL,
            level VARCHAR(2) NOT NULL,
            difficulty VARCHAR(20) NOT NULL DEFAULT 'Easy',
            summary VARCHAR(280) NOT NULL,
            rule_explanation TEXT NOT NULL,
            examples_json TEXT NOT NULL,
            common_mistakes TEXT,
            tips_tricks TEXT,
            related_topic_ids VARCHAR(100),
            is_active BOOLEAN NOT NULL DEFAULT 1,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create grammar_progress table if not exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS grammar_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            topic_id INTEGER NOT NULL,
            is_completed BOOLEAN NOT NULL DEFAULT 0,
            is_favorite BOOLEAN NOT NULL DEFAULT 0,
            completed_at DATETIME,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES user (id),
            FOREIGN KEY (topic_id) REFERENCES grammar_topic (id),
            UNIQUE (user_id, topic_id)
        )
    """)

    # Create grammar_exercise_attempt table if not exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS grammar_exercise_attempt (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            topic_id INTEGER,
            difficulty VARCHAR(20) NOT NULL DEFAULT 'Easy',
            question_count INTEGER NOT NULL DEFAULT 10,
            score INTEGER NOT NULL DEFAULT 0,
            total_questions INTEGER NOT NULL DEFAULT 10,
            duration_seconds INTEGER NOT NULL DEFAULT 0,
            completed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES user (id),
            FOREIGN KEY (topic_id) REFERENCES grammar_topic (id)
        )
    """)

    # Create grammar_error_log table if not exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS grammar_error_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            question_id INTEGER NOT NULL,
            attempt_id INTEGER,
            user_answer VARCHAR(1) NOT NULL,
            correct_answer VARCHAR(1) NOT NULL,
            is_resolved BOOLEAN NOT NULL DEFAULT 0,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES user (id),
            FOREIGN KEY (question_id) REFERENCES question (id),
            FOREIGN KEY (attempt_id) REFERENCES grammar_exercise_attempt (id)
        )
    """)

    # Create grammar_rule table if not exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS grammar_rule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title VARCHAR(160) NOT NULL,
            category VARCHAR(80) NOT NULL,
            summary VARCHAR(280) NOT NULL,
            explanation TEXT NOT NULL,
            examples TEXT NOT NULL,
            exceptions TEXT,
            common_errors TEXT,
            quick_table_html TEXT,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create grammar_rule_bookmark table if not exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS grammar_rule_bookmark (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            rule_id INTEGER NOT NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES user (id),
            FOREIGN KEY (rule_id) REFERENCES grammar_rule (id),
            UNIQUE (user_id, rule_id)
        )
    """)

    # Create quiz table if not exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quiz (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title VARCHAR(160) NOT NULL,
            category VARCHAR(80) NOT NULL,
            level VARCHAR(2) NOT NULL,
            skill VARCHAR(30) NOT NULL,
            difficulty VARCHAR(20) NOT NULL DEFAULT 'Medium',
            description VARCHAR(280) NOT NULL,
            question_count INTEGER NOT NULL DEFAULT 10,
            duration_minutes INTEGER NOT NULL DEFAULT 15,
            view_count INTEGER NOT NULL DEFAULT 0,
            is_active BOOLEAN NOT NULL DEFAULT 1,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create exam table if not exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS exam (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title VARCHAR(160) NOT NULL,
            category VARCHAR(80) NOT NULL,
            duration_minutes INTEGER NOT NULL DEFAULT 15,
            difficulty VARCHAR(20) NOT NULL DEFAULT 'Medium',
            question_bank VARCHAR(80) NOT NULL DEFAULT 'General',
            selection_type VARCHAR(20) NOT NULL DEFAULT 'random',
            selected_question_ids TEXT,
            question_count INTEGER NOT NULL DEFAULT 10,
            is_published BOOLEAN NOT NULL DEFAULT 1,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()

    conn.close()
    print("Database patched successfully with Exam Management enhancements!")
else:
    print("Database file not found at", db_path)
