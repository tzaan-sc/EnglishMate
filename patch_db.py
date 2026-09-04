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
        ("exam_default_type", "VARCHAR(50) NOT NULL DEFAULT 'TOEIC'"),
        ("exam_default_time_limit", "INTEGER NOT NULL DEFAULT 120"),
        ("exam_show_timer", "BOOLEAN NOT NULL DEFAULT 1"),
        ("exam_allow_pause", "BOOLEAN NOT NULL DEFAULT 1"),
        ("exam_show_realtime_score", "BOOLEAN NOT NULL DEFAULT 0"),
        ("exam_auto_submit", "BOOLEAN NOT NULL DEFAULT 1"),
        ("exam_sound_effects", "BOOLEAN NOT NULL DEFAULT 1"),
        ("xp", "INTEGER NOT NULL DEFAULT 0"),
        ("level", "INTEGER NOT NULL DEFAULT 1"),
        ("level_start_date", "DATE"),
        ("daily_goal_xp", "INTEGER NOT NULL DEFAULT 50"),
        ("daily_reward_claimed_date", "DATE"),
    ]

    for col_name, col_type in new_cols:
        if col_name not in existing_cols:
            print(f"Adding column {col_name}...")
            cursor.execute(f"ALTER TABLE user ADD COLUMN {col_name} {col_type}")

    conn.commit()

    # Patch flashcard_progress table columns
    cursor.execute("PRAGMA table_info(flashcard_progress)")
    fp_cols = [row[1] for row in cursor.fetchall()]
    new_fp_cols = [
        ("srs_level", "INTEGER NOT NULL DEFAULT 1"),
        ("next_review_at", "DATETIME DEFAULT CURRENT_TIMESTAMP"),
    ]
    for col_name, col_type in new_fp_cols:
        if col_name not in fp_cols:
            print(f"Adding column {col_name} to flashcard_progress...")
            cursor.execute(f"ALTER TABLE flashcard_progress ADD COLUMN {col_name} {col_type}")

    conn.commit()

    # Patch vocabulary table columns
    cursor.execute("PRAGMA table_info(vocabulary)")
    vocab_cols = [row[1] for row in cursor.fetchall()]
    new_vocab_cols = [
        ("category", "VARCHAR(50) NOT NULL DEFAULT 'cefr'"),
        ("subcategory", "VARCHAR(100)"),
        ("lesson_unit", "VARCHAR(100)"),
    ]
    for col_name, col_type in new_vocab_cols:
        if col_name not in vocab_cols:
            print(f"Adding column {col_name} to vocabulary...")
            cursor.execute(f"ALTER TABLE vocabulary ADD COLUMN {col_name} {col_type}")

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

    # Ensure all columns exist on exam table
    cursor.execute("PRAGMA table_info(exam);")
    exam_columns = [column[1] for column in cursor.fetchall()]

    new_exam_columns = [
        ("duration_minutes", "INTEGER DEFAULT 15"),
        ("difficulty", "VARCHAR(20) DEFAULT 'Medium'"),
        ("question_bank", "VARCHAR(80) DEFAULT 'General'"),
        ("selection_type", "VARCHAR(20) DEFAULT 'random'"),
        ("selected_question_ids", "TEXT"),
        ("question_count", "INTEGER DEFAULT 10"),
        ("is_published", "BOOLEAN DEFAULT 1"),
        ("updated_at", "DATETIME")
    ]

    for col_name, col_type in new_exam_columns:
        if col_name not in exam_columns:
            cursor.execute(f"ALTER TABLE exam ADD COLUMN {col_name} {col_type};")

    conn.commit()

    # Create Gamification Tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS badge (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code VARCHAR(50) NOT NULL UNIQUE,
            name VARCHAR(100) NOT NULL,
            description VARCHAR(255) NOT NULL,
            icon VARCHAR(50) NOT NULL,
            category VARCHAR(50) NOT NULL DEFAULT 'GENERAL',
            xp_reward INTEGER NOT NULL DEFAULT 50,
            req_type VARCHAR(50) NOT NULL,
            req_value INTEGER NOT NULL DEFAULT 1,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_badge (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            badge_id INTEGER NOT NULL,
            unlocked_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES user (id),
            FOREIGN KEY (badge_id) REFERENCES badge (id),
            UNIQUE (user_id, badge_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS challenge (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code VARCHAR(50) NOT NULL UNIQUE,
            title VARCHAR(150) NOT NULL,
            description VARCHAR(255) NOT NULL,
            icon VARCHAR(50) NOT NULL DEFAULT '🎯',
            action_type VARCHAR(50) NOT NULL,
            target INTEGER NOT NULL DEFAULT 1,
            xp_reward INTEGER NOT NULL DEFAULT 30,
            period VARCHAR(20) NOT NULL DEFAULT 'DAILY',
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_challenge (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            challenge_id INTEGER NOT NULL,
            current_progress INTEGER NOT NULL DEFAULT 0,
            is_completed BOOLEAN NOT NULL DEFAULT 0,
            is_claimed BOOLEAN NOT NULL DEFAULT 0,
            period_date DATE NOT NULL,
            completed_at DATETIME,
            FOREIGN KEY (user_id) REFERENCES user (id),
            FOREIGN KEY (challenge_id) REFERENCES challenge (id),
            UNIQUE (user_id, challenge_id, period_date)
        )
    """)
    conn.commit()

    # Seed default badges if empty
    cursor.execute("SELECT COUNT(*) FROM badge")
    if cursor.fetchone()[0] == 0:
        default_badges = [
            ("FIRST_STEP", "Bước đầu tiên", "Hoàn thành bài học đầu tiên", "🎯", "LESSONS", 50, "lessons_count", 1),
            ("LESSON_5", "Chăm học", "Hoàn thành 5 bài học", "📖", "LESSONS", 100, "lessons_count", 5),
            ("LESSON_10", "Học bá", "Hoàn thành 10 bài học", "🎓", "LESSONS", 200, "lessons_count", 10),
            ("VOCAB_STARTER", "Khởi đầu từ vựng", "Đã học 10 từ vựng", "📚", "VOCABULARY", 50, "vocab_count", 10),
            ("VOCAB_MASTER", "Bậc thầy từ vựng", "Đã học 50 từ vựng", "👑", "VOCABULARY", 250, "vocab_count", 50),
            ("QUIZ_CHAMPION", "Vua trắc nghiệm", "Hoàn thành 5 bài kiểm tra Quiz", "🏆", "QUIZ", 100, "quiz_count", 5),
            ("PERFECT_SCORE", "Điểm tuyệt đối", "Đạt điểm 100% trong bài kiểm tra", "💯", "QUIZ", 150, "perfect_score", 1),
            ("STREAK_3", "Chăm chỉ 3 ngày", "Đạt chuỗi 3 ngày học liên tiếp", "🔥", "STREAK", 50, "streak_days", 3),
            ("STREAK_7", "Chiến binh 1 tuần", "Đạt chuỗi 7 ngày học liên tiếp", "⚡", "STREAK", 150, "streak_days", 7),
            ("STREAK_30", "Kiên trì 1 tháng", "Đạt chuỗi 30 ngày học liên tiếp", "🌟", "STREAK", 500, "streak_days", 30),
            ("FLASHCARD_FAN", "Tín đồ Flashcard", "Tạo hoặc ôn tập bộ thẻ flashcard", "🎴", "FLASHCARD", 50, "flashcard_count", 1),
            ("LEVEL_5", "Cao thủ Level 5", "Đạt cấp độ 5 trong hệ thống", "⭐", "LEVEL", 200, "level_reach", 5),
        ]
        cursor.executemany("INSERT INTO badge (code, name, description, icon, category, xp_reward, req_type, req_value) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", default_badges)
        conn.commit()

    # Seed default challenges if empty
    cursor.execute("SELECT COUNT(*) FROM challenge")
    if cursor.fetchone()[0] == 0:
        default_challenges = [
            ("DAILY_LESSON_1", "Bài học trong ngày", "Hoàn thành 1 bài học bất kỳ hôm nay", "📖", "lesson", 1, 30, "DAILY"),
            ("DAILY_VOCAB_10", "Luyện từ vựng", "Học hoặc ôn tập 10 từ vựng", "📚", "vocab", 10, 30, "DAILY"),
            ("DAILY_QUIZ_1", "Thử tài kiến thức", "Hoàn thành 1 bài Quiz hoặc bài tập", "🎯", "quiz", 1, 30, "DAILY"),
            ("DAILY_GAME_1", "Phản xạ nhanh", "Chơi 1 ván trò chơi từ vựng", "🎮", "game", 1, 20, "DAILY"),
            ("WEEKLY_STREAK_5", "Chiến binh kiên trì", "Duy trì chuỗi học 5 ngày trong tuần", "🔥", "streak", 5, 100, "WEEKLY"),
            ("WEEKLY_LESSONS_5", "Chinh phục bài học", "Hoàn thành 5 bài học trong tuần", "🎓", "lesson", 5, 120, "WEEKLY"),
            ("WEEKLY_EXAMS_2", "Luyện đề xuất sắc", "Hoàn thành 2 đề thi TOEIC / Kiểm tra", "🏆", "exam", 2, 150, "WEEKLY"),
        ]
        cursor.executemany("INSERT INTO challenge (code, title, description, icon, action_type, target, xp_reward, period) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", default_challenges)
        conn.commit()

    conn.close()
    print("Database patched successfully with Gamification enhancements!")
else:
    print("Database file not found at", db_path)
