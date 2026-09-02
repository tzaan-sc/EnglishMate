"""
setup_exams.py
==============
Khởi tạo cấu trúc bảng Đề thi (Exam tables) trong PostgreSQL / SQLite.
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app import create_app
from app.extensions import db
from app.modules.exams.models import Exam, ExamQuestion, ExamSubmission, ExamAnswerDetail


def setup_exams():
    app = create_app()
    with app.app_context():
        db.create_all()
        print("[OK] Toàn bộ các bảng cơ sở dữ liệu đã được khởi tạo/cập nhật thành công!")


if __name__ == "__main__":
    setup_exams()
