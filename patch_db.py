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

    conn.close()
    print("Database patched successfully with RBAC tables and initial seed data!")
else:
    print("Database file not found at", db_path)
