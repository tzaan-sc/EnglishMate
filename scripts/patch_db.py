"""
patch_db.py
===========
Công cụ đồng bộ cấu trúc và cập nhật các cột / bảng cơ sở dữ liệu SQLite & PostgreSQL.
"""

import sys
from pathlib import Path

# Ensure UTF-8 output on Windows console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app import create_app
from app.extensions import db


def patch_database_all():
    print("[*] Đang kiểm tra và cập nhật cấu trúc cơ sở dữ liệu...")
    app = create_app()
    with app.app_context():
        db.create_all()

        # Check and patch grammar_topic columns
        from sqlalchemy import inspect, text
        inspector = inspect(db.engine)
        if "grammar_topic" in inspector.get_table_names():
            columns = {col["name"] for col in inspector.get_columns("grammar_topic")}
            new_columns = [
                ("order_index", "INTEGER DEFAULT 0"),
                ("exam_targets", "VARCHAR(160) DEFAULT 'General English, TOEIC'"),
                ("toeic_parts", "VARCHAR(80)"),
                ("toeic_weight", "VARCHAR(20) DEFAULT 'Medium'"),
                ("importance", "VARCHAR(20) DEFAULT 'Medium'"),
            ]
            for col_name, col_type in new_columns:
                if col_name not in columns:
                    print(f"[*] Bổ sung cột '{col_name}' vào bảng 'grammar_topic'...")
                    db.session.execute(text(f"ALTER TABLE grammar_topic ADD COLUMN {col_name} {col_type}"))
            db.session.commit()

        print("[OK] Đã đồng bộ toàn bộ cấu trúc bảng từ Models!")


if __name__ == "__main__":
    patch_database_all()
