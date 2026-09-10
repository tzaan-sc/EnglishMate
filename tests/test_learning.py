from datetime import date, timedelta
from app.modules.learning.models import Lesson, LessonProgress, QuizAttempt, Question
from app.modules.auth.models import User
from tests.conftest import login


def test_view_lessons(client):
    login(client)
    response = client.get("/lessons")
    assert response.status_code == 200
    assert b"Test lesson" in response.data


def test_complete_lesson(client, app):
    login(client)
    with app.app_context():
        lesson_id = Lesson.query.first().id
    response = client.post(f"/lessons/{lesson_id}/complete", follow_redirects=True)
    assert response.status_code == 200
    with app.app_context():
        assert LessonProgress.query.count() == 1


def test_take_quiz_and_save_score(client, app):
    login(client)
    with app.app_context():
        ids = [str(q.id) for q in Question.query.all()]
    data = {"question_ids": ",".join(ids), "level": "A1", "topic": "Daily Life"}
    data.update({f"question_{qid}": "A" for qid in ids})
    response = client.post("/quiz", data=data, follow_redirects=True)
    assert response.status_code == 200
    assert b"100%" in response.data
    with app.app_context():
        attempt = QuizAttempt.query.one()
        assert attempt.score == 10
        assert len(attempt.answers) == 10


def test_all_learner_pages_render(client, app):
    login(client)
    with app.app_context():
        lesson_id = Lesson.query.first().id
    endpoints = [
        "/dashboard", "/lessons", f"/lessons/{lesson_id}", "/vocabulary",
        "/flashcards", "/quiz", "/toeic", "/progress"
    ]
    for endpoint in endpoints:
        assert client.get(endpoint, follow_redirects=True).status_code == 200


def test_streak_mechanics(app):
    from datetime import date, timedelta
    from app.modules.auth.models import User, record_daily_activity, DailyActivity
    from app.extensions import db

    with app.app_context():
        user = User.query.filter_by(email="student@test.com").first()
        today = date.today()

        # Rule 1: Initial streak is 0
        user.current_streak = 0
        user.longest_streak = 0
        user.last_activity_date = None
        db.session.commit()
        assert user.get_current_streak() == 0

        # Rule 2: Complete 1st lesson today -> streak becomes 1
        record_daily_activity(user)
        assert user.current_streak == 1
        assert user.longest_streak == 1
        assert user.last_activity_date == today

        # Rule 3: Complete multiple lessons on same day -> streak stays 1
        record_daily_activity(user)
        record_daily_activity(user)
        assert user.current_streak == 1

        # Rule 4: Consecutive day learning (simulate yesterday learning)
        yesterday = today - timedelta(days=1)
        user.last_activity_date = yesterday
        user.current_streak = 1
        # Clear today's activity record for test simulation
        DailyActivity.query.filter_by(user_id=user.id, activity_date=today).delete()
        db.session.commit()

        record_daily_activity(user)
        assert user.current_streak == 2
        assert user.longest_streak == 2
        assert user.last_activity_date == today

        # Rule 5: Missed days (simulate last activity 3 days ago)
        user.last_activity_date = today - timedelta(days=3)
        user.current_streak = 2
        DailyActivity.query.filter_by(user_id=user.id, activity_date=today).delete()
        db.session.commit()

        # Check lazy streak status before learning -> 0
        assert user.get_current_streak() == 0

        # Learning on 3rd day -> streak resets to 1
        record_daily_activity(user)
        assert user.current_streak == 1
        # Longest streak preserves record
        assert user.longest_streak == 2


def test_streak_status_four_states(app):
    from app.extensions import db
    with app.app_context():
        user = User.query.filter_by(email="student@test.com").first()
        today = date.today()
        yesterday = today - timedelta(days=1)

        # 1. State: not_started
        user.last_activity_date = None
        user.current_streak = 0
        user.longest_streak = 0
        db.session.commit()
        status = user.get_streak_status()
        assert status["state"] == "not_started"
        assert status["current_streak"] == 0
        assert status["is_learned_today"] is False

        # 2. State: active_today
        user.last_activity_date = today
        user.current_streak = 5
        user.longest_streak = 5
        db.session.commit()
        status = user.get_streak_status()
        assert status["state"] == "active_today"
        assert status["current_streak"] == 5
        assert status["is_learned_today"] is True
        assert "Đã duy trì" in status["status_badge"]

        # 3. State: pending_today (studied yesterday, haven't studied today)
        user.last_activity_date = yesterday
        user.current_streak = 5
        db.session.commit()
        status = user.get_streak_status()
        assert status["state"] == "pending_today"
        assert status["current_streak"] == 5
        assert status["is_learned_today"] is False
        assert "Chưa học hôm nay" in status["status_badge"]

        # 4. State: broken (missed yesterday or earlier)
        user.last_activity_date = today - timedelta(days=3)
        user.current_streak = 5
        user.longest_streak = 10
        db.session.commit()
        status = user.get_streak_status()
        assert status["state"] == "broken"
        assert status["current_streak"] == 0
        assert status["previous_streak"] == 5
        assert status["longest_streak"] == 10
        assert status["is_learned_today"] is False
        assert "Chuỗi đã kết thúc" in status["status_badge"]


def test_streak_activation_popup_event(client, app):
    from app.modules.auth.models import DailyActivity
    from app.extensions import db
    login(client)
    today = date.today()
    with app.app_context():
        user = User.query.filter_by(email="student@test.com").first()
        DailyActivity.query.filter_by(user_id=user.id, activity_date=today).delete()
        user.last_activity_date = today - timedelta(days=1)
        user.current_streak = 3
        db.session.commit()

    # Complete a lesson
    with app.app_context():
        lesson_id = Lesson.query.first().id

    response = client.post(f"/lessons/{lesson_id}/complete", follow_redirects=True)
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    # Modal HTML exists in page and was automatically triggered
    assert "streakActivatedModal" in html
    assert "CHUỖI HỌC TẬP ĐÃ KÍCH HOẠT" in html


def test_admin_excluded_from_level_and_streak(app):
    from app.modules.auth.models import User, record_daily_activity
    with app.app_context():
        admin = User.query.filter_by(role="ADMIN").first()
        assert admin is not None
        assert admin.is_admin is True

        # Rule: Admin has no level and cannot gain XP
        assert admin.get_level() is None
        assert admin.get_current_streak() == 0
        admin_status = admin.get_streak_status()
        assert admin_status["state"] == "admin"
        assert admin_status["current_streak"] == 0

        # Attempting to add XP or record activity should be no-op for admin
        assert admin.add_xp(100) == 0
        assert record_daily_activity(admin) is None


