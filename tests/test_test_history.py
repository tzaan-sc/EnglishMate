from app.extensions import db
from app.modules.auth.models import User
from app.modules.learning.models import QuizAttempt
from app.modules.exams.models import Exam, ExamSubmission
from tests.conftest import login


def test_test_history_render(client):
    login(client)

    res = client.get("/exams/history")
    assert res.status_code == 200
    assert "Lịch Sử Kiểm Tra".encode("utf-8") in res.data
    assert "Tổng lượt làm bài".encode("utf-8") in res.data


def test_test_history_filtering_and_sorting(client):
    login(client)

    res_type = client.get("/exams/history?type=Quiz")
    assert res_type.status_code == 200

    res_sort = client.get("/exams/history?sort=score_desc")
    assert res_sort.status_code == 200

    res_range = client.get("/exams/history?min_score=50&max_score=100")
    assert res_range.status_code == 200


def test_test_history_review_redirect(client):
    login(client)

    with client.application.app_context():
        user = User.query.filter_by(email="student@test.com").first()
        attempt = QuizAttempt(user_id=user.id, level="A1", topic="Grammar Basics", score=8, total_questions=10)
        db.session.add(attempt)
        db.session.commit()
        attempt_id = attempt.id

    res = client.get(f"/exams/history/review/quiz/{attempt_id}", follow_redirects=True)
    assert res.status_code == 200


def test_test_history_compare(client):
    login(client)

    with client.application.app_context():
        user = User.query.filter_by(email="student@test.com").first()
        q_attempt = QuizAttempt(user_id=user.id, level="A1", topic="Quiz Test", score=9, total_questions=10)
        exam = Exam(title="Specialized Test", category="TOEFL", duration=30, question_count=15)
        db.session.add_all([q_attempt, exam])
        db.session.commit()

        sub = ExamSubmission(user_id=user.id, exam_id=exam.id, total_score=12, status="COMPLETED")
        db.session.add(sub)
        db.session.commit()

        q_id = q_attempt.id
        s_id = sub.id

    res = client.get(f"/exams/history/compare?ids=quiz_{q_id},submission_{s_id}")
    assert res.status_code == 200
    assert "So Sánh Tiến Độ Lượt Làm Bài Thi".encode("utf-8") in res.data


def test_test_history_export_csv(client):
    login(client)

    res = client.get("/exams/history/export")
    assert res.status_code == 200
    assert "text/csv" in res.headers["Content-Type"]
    assert "ID,Loai Bai Thi,Tieu De".encode("utf-8") in res.data


def test_test_history_delete(client):
    login(client)

    with client.application.app_context():
        user = User.query.filter_by(email="student@test.com").first()
        attempt = QuizAttempt(user_id=user.id, level="A1", topic="Temporary Quiz", score=5, total_questions=10)
        db.session.add(attempt)
        db.session.commit()
        att_id = attempt.id

    res = client.post(f"/exams/history/quiz/{att_id}/delete", follow_redirects=True)
    assert res.status_code == 200

    with client.application.app_context():
        deleted = db.session.get(QuizAttempt, att_id)
        assert deleted is None
