from datetime import date
from unittest.mock import patch

from app.backend.auth.models import DailyActivity, User
from app.backend.learning.goal_reminder import (
    check_user_goal_reminder_alert,
    get_user_daily_goal_status,
    send_daily_goal_reminders,
)
from app.extensions import db
from tests.conftest import login


def test_user_get_daily_goal_info(app):
    with app.app_context():
        user = User(username="goal_user_1", email="goal1@test.com", daily_goal_xp=60)
        user.set_password("pass123")
        db.session.add(user)
        db.session.commit()

        # No activity today
        info = user.get_daily_goal_info()
        assert info is not None
        assert info["target_xp"] == 60
        assert info["progress_xp"] == 0
        assert info["remaining_xp"] == 60
        assert info["is_completed"] is False
        assert info["is_claimed"] is False
        assert info["reminder_enabled"] is True

        # Add 1 lesson (20 XP)
        act = DailyActivity(user_id=user.id, activity_date=date.today(), completed_lessons=1, goal_completed=False)
        db.session.add(act)
        db.session.commit()

        info = user.get_daily_goal_info()
        assert info["progress_xp"] == 20
        assert info["remaining_xp"] == 40
        assert info["is_completed"] is False

        # Add 2 more lessons (total 3 = 60 XP >= target)
        act.completed_lessons = 3
        act.goal_completed = True
        db.session.commit()

        info = user.get_daily_goal_info()
        assert info["progress_xp"] == 60
        assert info["remaining_xp"] == 0
        assert info["is_completed"] is True


def test_check_user_goal_reminder_alert(app):
    with app.app_context():
        admin = User(username="admin_goal", email="admin_goal@test.com", role="ADMIN")
        admin.set_password("pass123")
        student = User(username="student_goal", email="student_goal@test.com", daily_goal_xp=50)
        student.set_password("pass123")
        db.session.add_all([admin, student])
        db.session.commit()

        # Admin excluded
        alert_admin = check_user_goal_reminder_alert(admin)
        assert alert_admin["should_remind"] is False

        # Student during morning (hour=10)
        alert_morning = check_user_goal_reminder_alert(student, force_hour=10)
        assert alert_morning["should_remind"] is True
        assert alert_morning["should_popup"] is False  # Not yet evening/reminder hour

        # Student in evening (hour=20)
        alert_evening = check_user_goal_reminder_alert(student, force_hour=20)
        assert alert_evening["should_remind"] is True
        assert alert_evening["should_popup"] is True

        # When goal is completed
        act = DailyActivity(user_id=student.id, activity_date=date.today(), completed_lessons=3, goal_completed=True)
        db.session.add(act)
        db.session.commit()

        alert_done = check_user_goal_reminder_alert(student, force_hour=21)
        assert alert_done["should_remind"] is False


def test_goal_notification_check_api(client, app):
    with app.app_context():
        user = User(username="api_student", email="api_student@test.com", daily_goal_xp=50)
        user.set_password("pass123")
        db.session.add(user)
        db.session.commit()

    # Must be logged in
    res = client.get("/api/goal/notification-check")
    assert res.status_code == 302

    login(client, email="api_student@test.com", password="pass123")
    res = client.get("/api/goal/notification-check?force_hour=21")
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert data["should_remind"] is True
    assert data["should_popup"] is True
    assert "remaining_xp" in data["status"]
    assert data["status"]["remaining_xp"] == 50


def test_goal_dismiss_popup_api(client, app):
    with app.app_context():
        user = User(username="dismiss_user", email="dismiss_user@test.com")
        user.set_password("pass123")
        db.session.add(user)
        db.session.commit()

    login(client, email="dismiss_user@test.com", password="pass123")
    res = client.post("/api/goal/dismiss-popup")
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True

    # Now notification-check should have should_popup == False
    res2 = client.get("/api/goal/notification-check?force_hour=21")
    data2 = res2.get_json()
    assert data2["should_popup"] is False
    assert data2["is_dismissed"] is True


def test_goal_update_settings_api(client, app):
    with app.app_context():
        user = User(username="settings_user", email="settings_user@test.com")
        user.set_password("pass123")
        db.session.add(user)
        db.session.commit()

    login(client, email="settings_user@test.com", password="pass123")
    res = client.post(
        "/api/goal/settings",
        json={
            "enabled": True,
            "reminder_time": "21:00",
            "email_enabled": False,
            "popup_enabled": True,
            "daily_goal_xp": 80,
        },
    )
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert data["settings"]["daily_goal_reminder_time"] == "21:00"
    assert data["settings"]["daily_goal_reminder_email"] is False
    assert data["settings"]["daily_goal_xp"] == 80


@patch("app.backend.learning.goal_reminder.send_email")
def test_send_daily_goal_reminders(mock_send_email, app):
    mock_send_email.return_value = True

    with app.app_context():
        u1 = User(
            username="remind_me",
            email="remind_me@test.com",
            daily_goal_xp=50,
            daily_goal_reminder_enabled=True,
            daily_goal_reminder_email=True,
        )
        u2 = User(
            username="already_done",
            email="already_done@test.com",
            daily_goal_xp=50,
            daily_goal_reminder_enabled=True,
            daily_goal_reminder_email=True,
        )
        u1.set_password("pass123")
        u2.set_password("pass123")
        db.session.add_all([u1, u2])
        db.session.commit()

        # u2 completes goal
        act2 = DailyActivity(user_id=u2.id, activity_date=date.today(), completed_lessons=3, goal_completed=True)
        db.session.add(act2)
        db.session.commit()

        # Send reminders
        res = send_daily_goal_reminders(force=False)
        recipients = [c.args[0] for c in mock_send_email.call_args_list]
        assert "remind_me@test.com" in recipients
        assert "already_done@test.com" not in recipients
        assert u1.last_daily_goal_reminder_date == date.today()

        # Running again for u1 without force should skip already notified user
        res2 = send_daily_goal_reminders(force=False, target_user_id=u1.id)
        assert res2["sent_count"] == 0
        assert res2["skipped_count"] == 1


@patch("app.backend.learning.goal_reminder.send_email")
def test_goal_send_test_reminder_api(mock_send_email, client, app):
    mock_send_email.return_value = True

    with app.app_context():
        user = User(username="test_btn_user", email="test_btn@test.com")
        user.set_password("pass123")
        db.session.add(user)
        db.session.commit()

    login(client, email="test_btn@test.com", password="pass123")
    res = client.post("/api/goal/send-test-reminder")
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert "sample_alert" in data
    mock_send_email.assert_called_once()


def test_gamification_tab_and_modal_rendered(client, app):
    with app.app_context():
        user = User(username="page_user", email="page_user@test.com")
        user.set_password("pass123")
        db.session.add(user)
        db.session.commit()

    login(client, email="page_user@test.com", password="pass123")
    res = client.get("/gamification?tab=challenges")
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert "goalReminderForm" in html
    assert "btnSaveGoalSettings" in html
    assert "btnTestGoalReminder" in html
    assert "goalReminderModal" in html
