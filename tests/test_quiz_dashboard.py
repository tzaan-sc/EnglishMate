from datetime import datetime, timedelta
from app.extensions import db
from app.modules.auth.models import User
from app.modules.learning.models import QuizAttempt
from app.modules.learning.routes import calculate_quiz_dashboard_metrics
from tests.conftest import login


def ensure_sample_quiz_attempts(user_id):
    if QuizAttempt.query.filter_by(user_id=user_id).count() == 0:
        att1 = QuizAttempt(user_id=user_id, level="A1", topic="Grammar", score=10, total_questions=10, duration_seconds=120, created_at=datetime.utcnow() - timedelta(days=1))
        att2 = QuizAttempt(user_id=user_id, level="B1", topic="Vocabulary", score=4, total_questions=10, duration_seconds=180, created_at=datetime.utcnow())
        db.session.add_all([att1, att2])
        db.session.commit()


def test_quiz_dashboard_render(client):
    login(client)
    res = client.get("/quizzes/dashboard")
    assert res.status_code == 200
    assert "Bảng Điều Khiển Quiz & Đánh Giá".encode("utf-8") in res.data
    assert "Tổng điểm Quiz".encode("utf-8") in res.data
    assert "Tỷ lệ chính xác %".encode("utf-8") in res.data
    assert "Chuỗi ngày luyện Quiz".encode("utf-8") in res.data


def test_calculate_quiz_dashboard_metrics(client):
    login(client)

    with client.application.app_context():
        user = User.query.filter_by(email="student@test.com").first()
        ensure_sample_quiz_attempts(user.id)

        metrics = calculate_quiz_dashboard_metrics(user.id)

        assert metrics["total_quizzes_completed"] >= 2
        assert metrics["overall_score"] >= 14
        assert metrics["accuracy_rate"] > 0
        assert metrics["avg_time_seconds"] > 0
        assert metrics["quiz_streak"] >= 1

        # Check weak categories (Vocabulary accuracy is 40% < 60%)
        weak_names = [w["name"] for w in metrics["weak_categories"]]
        assert "Vocabulary" in weak_names
