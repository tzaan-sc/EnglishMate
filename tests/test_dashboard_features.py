import pytest
from datetime import date, timedelta
from app.extensions import db
from app.backend.auth.models import User, DailyActivity, record_daily_activity
from app.backend.learning.models import Lesson, LessonProgress, QuizAttempt, Vocabulary, VocabularyProgress
from tests.conftest import login

@pytest.fixture
def dashboard_setup(app):
    with app.app_context():
        user = User.query.filter_by(username="student").first()
        record_daily_activity(user, lessons_count=2)
        
        # Ensure sample activity for past days
        act = DailyActivity.query.filter_by(user_id=user.id, activity_date=date.today() - timedelta(days=2)).first()
        if not act:
            act = DailyActivity(user_id=user.id, activity_date=date.today() - timedelta(days=2), completed_lessons=3, goal_completed=True)
            db.session.add(act)
            
        # Add sample quiz attempt
        qa = QuizAttempt.query.filter_by(user_id=user.id).first()
        if not qa:
            qa = QuizAttempt(user_id=user.id, level="A1", topic="Vocabulary", score=8, total_questions=10)
            db.session.add(qa)
            
        db.session.commit()

def test_dashboard_renders_all_section_6_1_features(client, dashboard_setup):
    login(client)
    response = client.get("/dashboard")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    
    # 1. Skill-specific progress
    assert "Tiến độ theo kỹ năng" in html
    assert "Từ vựng" in html
    assert "Ngữ pháp" in html
    assert "Đọc hiểu" in html
    assert "Nghe hiểu" in html
    
    # 2. Time spent learning
    assert "HÔM NAY" in html
    assert "TUẦN NÀY" in html
    assert "TẤT CẢ" in html
    
    # 3. Activity Heatmap & Learning calendar
    assert "Bản đồ hoạt động (365 ngày qua)" in html
    assert "heatmap-grid" in html
    
    # 4. Performance trends
    assert "Xu hướng hiệu suất" in html
    
    # 5. Today's schedule
    assert "Lịch trình & Mục tiêu hôm nay" in html
    
    # 6. Today's achievements
    assert "XP hôm nay" in html
    assert "Chuỗi ngày:" in html
    
    # 7. Daily motivation quote & Quick actions
    assert "Học bài tiếp" in html or "Từ vựng" in html


def test_dashboard_streak_colors_gray_when_not_learned_and_orange_when_learned(client, app):
    login(client)
    today = date.today()
    with app.app_context():
        user = User.query.filter_by(username="student").first()
        # 1. Before completing today's lesson:
        # Reset today's activity
        DailyActivity.query.filter_by(user_id=user.id, activity_date=today).delete()
        user.last_activity_date = today - timedelta(days=1)
        user.current_streak = 3
        db.session.commit()

    # Request dashboard: should show gray / inactive state
    res = client.get("/dashboard")
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert "Chưa học hôm nay" in html
    assert "Hoàn thành 1 bài để giữ chuỗi!" in html
    # Gray flame icon in streak card
    assert "ph-bold ph-flame text-muted" in html

    # 2. Now user completes a lesson today:
    with app.app_context():
        user = User.query.filter_by(username="student").first()
        record_daily_activity(user, lessons_count=1)
        db.session.commit()

    # Request dashboard: should show orange / completed state
    res = client.get("/dashboard")
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert "✓ Đã học hôm nay" in html
    assert "Học liên tục để duy trì!" in html
    assert "streak-flame-lit" in html
    assert "streak-active" in html


def test_dashboard_activity_filters(client, dashboard_setup):
    login(client)

    # 1. Test 7 days filter
    res_7d = client.get("/dashboard?timeframe=7d")
    assert res_7d.status_code == 200
    html_7d = res_7d.get_data(as_text=True)
    assert "7 ngày qua" in html_7d
    assert "Bộ lọc: <strong class=\"text-primary\">7 ngày qua</strong>" in html_7d
    assert "heatmap-grid" in html_7d

    # 2. Test 30 days filter
    res_30d = client.get("/dashboard?timeframe=30d")
    assert res_30d.status_code == 200
    html_30d = res_30d.get_data(as_text=True)
    assert "30 ngày qua" in html_30d
    assert "Bộ lọc: <strong class=\"text-primary\">30 ngày qua</strong>" in html_30d

    # 3. Test quarter (90 days) filter
    res_quarter = client.get("/dashboard?timeframe=quarter")
    assert res_quarter.status_code == 200
    html_quarter = res_quarter.get_data(as_text=True)
    assert "Quý này" in html_quarter
    assert "90 ngày qua" in html_quarter

    # 4. Test custom date range filter
    today = date.today()
    from_date = (today - timedelta(days=15)).strftime("%Y-%m-%d")
    to_date = today.strftime("%Y-%m-%d")
    res_custom = client.get(f"/dashboard?timeframe=custom&from_date={from_date}&to_date={to_date}")
    assert res_custom.status_code == 200
    html_custom = res_custom.get_data(as_text=True)
    assert (today - timedelta(days=15)).strftime("%d/%m/%Y") in html_custom
    assert today.strftime("%d/%m/%Y") in html_custom

    # 5. Test specific year filter
    res_year = client.get("/dashboard?timeframe=year&year=2025")
    assert res_year.status_code == 200
    html_year = res_year.get_data(as_text=True)
    assert "Năm 2025" in html_year


