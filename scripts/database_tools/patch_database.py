"""
patch_database.py
=================
Công cụ vá cấu trúc và cập nhật các cột / bảng cơ sở dữ liệu SQLite & PostgreSQL.
"""

import sys
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from app import create_app
from app.extensions import db


def patch_database_all():
    print("[*] Đang kiểm tra và cập nhật cấu trúc cơ sở dữ liệu...")
    app = create_app()
    with app.app_context():
        # Khởi tạo toàn bộ các bảng trong models nếu chưa có
        db.create_all()
        print("[OK] Đã đồng bộ toàn bộ cấu trúc bảng từ Models!")


if __name__ == "__main__":
    patch_database_all()
