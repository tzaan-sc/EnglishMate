from app.models import Lesson, LessonProgress, QuizAttempt, Question
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
        assert client.get(endpoint).status_code == 200


def test_streak_mechanics(app):
    from datetime import date, timedelta
    from app.models import User, record_daily_activity, DailyActivity
    from app.extensions import db

    with app.app_context():
        user = User.query.first()
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
