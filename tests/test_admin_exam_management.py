from app.extensions import db
from app.modules.auth.models import User
from app.modules.exams.models import Exam
from app.modules.learning.models import Question
from tests.conftest import login


def ensure_admin_user(client):
    login(client)
    with client.application.app_context():
        user = User.query.filter_by(email="student@test.com").first()
        if user:
            user.role = "ADMIN"
            db.session.commit()


def ensure_sample_exam():
    exam = Exam.query.filter_by(title="Test Admin Exam Configuration").first()
    if not exam:
        exam = Exam(
            title="Test Admin Exam Configuration",
            category="TOEIC",
            duration_minutes=30,
            difficulty="Medium",
            question_bank="TOEIC Bank",
            selection_type="random",
            question_count=10,
            is_published=True
        )
        db.session.add(exam)
        db.session.commit()
    return exam


def test_admin_exams_list_render(client):
    ensure_admin_user(client)

    res = client.get("/admin/exams")
    assert res.status_code == 200
    assert "Quản Lý Đề Thi".encode("utf-8") in res.data
    assert "Tạo Đề Thi Mới".encode("utf-8") in res.data
    assert "Tổng đề thi".encode("utf-8") in res.data


def test_admin_exam_create_and_edit(client):
    ensure_admin_user(client)

    # Create exam
    res_create = client.post("/admin/exams/new", data={
        "title": "Exam Created By Test Automated",
        "category": "IELTS",
        "duration_minutes": "45",
        "difficulty": "Hard",
        "question_bank": "IELTS Bank",
        "selection_type": "random",
        "question_count": "15",
        "is_published": "on"
    }, follow_redirects=True)
    assert res_create.status_code == 200
    assert "Exam Created By Test Automated".encode("utf-8") in res_create.data

    with client.application.app_context():
        ex = Exam.query.filter_by(title="Exam Created By Test Automated").first()
        assert ex is not None
        ex_id = ex.id

    # Edit exam
    res_edit = client.post(f"/admin/exams/{ex_id}/edit", data={
        "title": "Exam Created By Test Automated Updated",
        "category": "IELTS",
        "duration_minutes": "60",
        "difficulty": "Hard",
        "question_bank": "IELTS Bank",
        "selection_type": "random",
        "question_count": "20",
        "is_published": "on"
    }, follow_redirects=True)
    assert res_edit.status_code == 200
    assert "Exam Created By Test Automated Updated".encode("utf-8") in res_edit.data


def test_admin_exam_toggle_publish_and_delete(client):
    ensure_admin_user(client)

    with client.application.app_context():
        ex = ensure_sample_exam()
        ex_id = ex.id

    # Toggle publish
    res_pub = client.post(f"/admin/exams/{ex_id}/publish", follow_redirects=True)
    assert res_pub.status_code == 200

    # Delete exam
    res_del = client.post(f"/admin/exams/{ex_id}/delete", follow_redirects=True)
    assert res_del.status_code == 200

    with client.application.app_context():
        del_ex = Exam.query.filter_by(title="Test Admin Exam Configuration").first()
        assert del_ex is None


def test_admin_exam_preview_and_stats(client):
    ensure_admin_user(client)

    with client.application.app_context():
        ex = ensure_sample_exam()
        ex_id = ex.id

    res_prev = client.get(f"/admin/exams/{ex_id}/preview")
    assert res_prev.status_code == 200
    assert "CHẾ ĐỘ XEM TRƯỚC".encode("utf-8") in res_prev.data

    res_stats = client.get(f"/admin/exams/{ex_id}/stats")
    assert res_stats.status_code == 200
    assert "PHÂN TÍCH HIỆU SUẤT ĐỀ THI".encode("utf-8") in res_stats.data
