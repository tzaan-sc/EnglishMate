import pytest
from datetime import date
from app.extensions import db
from app.modules.auth.models import User, DailyActivity, record_daily_activity
from app.modules.learning.models import Badge, UserBadge, Challenge, UserChallenge, Lesson, LessonProgress
from app.modules.learning.routes import check_user_badges, get_or_create_user_challenges, update_challenge_progress
from tests.conftest import login

@pytest.fixture
def gamification_setup(app):
    with app.app_context():
        # Ensure badges exist
        if Badge.query.count() == 0:
            b1 = Badge(code="FIRST_STEP", name="Bước đầu tiên", description="Hoàn thành bài học đầu tiên", icon="🎯", category="LESSONS", xp_reward=50, req_type="lessons_count", req_value=1)
            b2 = Badge(code="STREAK_3", name="Chăm chỉ 3 ngày", description="Đạt chuỗi 3 ngày học liên tiếp", icon="🔥", category="STREAK", xp_reward=50, req_type="streak_days", req_value=3)
            db.session.add_all([b1, b2])
            
        if Challenge.query.count() == 0:
            c1 = Challenge(code="DAILY_LESSON_1", title="Bài học trong ngày", description="Hoàn thành 1 bài học bất kỳ hôm nay", icon="📖", action_type="lesson", target=1, xp_reward=30, period="DAILY")
            c2 = Challenge(code="WEEKLY_STREAK_5", title="Chiến binh kiên trì", description="Duy trì chuỗi học 5 ngày trong tuần", icon="🔥", action_type="streak", target=5, xp_reward=100, period="WEEKLY")
            db.session.add_all([c1, c2])
            
        db.session.commit()

def test_user_level_and_xp_progression(app):
    with app.app_context():
        user = User(username="gametest", email="gametest@test.com")
        user.set_password("pass123")
        db.session.add(user)
        db.session.commit()
        
        # Initial state
        assert user.xp == 0
        assert user.get_level() == 1
        info = user.get_level_info()
        assert info["level"] == 1
        assert info["title"] == "Tân thủ"
        assert info["progress_pct"] == 0
        
        # Add XP to reach Level 2 (100+ XP)
        user.add_xp(120)
        assert user.xp == 120
        assert user.get_level() == 2
        info = user.get_level_info()
        assert info["level"] == 2
        assert info["title"] == "Tập sự"
        
        # Add XP to reach Level 5 (1000+ XP)
        user.add_xp(1000)
        assert user.get_level() == 5
        assert user.get_level_info()["title"] == "Cao thủ"

def test_gamification_hub_requires_login(client):
    response = client.get("/gamification")
    assert response.status_code == 302

def test_gamification_hub_page_success(client, gamification_setup):
    login(client)
    response = client.get("/gamification")
    assert response.status_code == 200
    assert "Bảng Xếp Hạng" in response.get_data(as_text=True)
    assert "Huy Hiệu Thành Tích" in response.get_data(as_text=True)
    assert "Thử Thách & Mục Tiêu" in response.get_data(as_text=True)

def test_badge_auto_unlock(app, gamification_setup):
    with app.app_context():
        user = User.query.filter_by(username="student").first()
        
        # Initially user might not have FIRST_STEP badge
        initial_badge_cnt = UserBadge.query.filter_by(user_id=user.id).count()
        
        # Add a lesson progress to trigger lessons_count >= 1
        lesson = Lesson.query.first()
        if not LessonProgress.query.filter_by(user_id=user.id, lesson_id=lesson.id).first():
            lp = LessonProgress(user_id=user.id, lesson_id=lesson.id)
            db.session.add(lp)
            db.session.commit()
            
        unlocked = check_user_badges(user)
        # Verify that FIRST_STEP badge is now unlocked
        badge = Badge.query.filter_by(code="FIRST_STEP").first()
        user_badge = UserBadge.query.filter_by(user_id=user.id, badge_id=badge.id).first()
        assert user_badge is not None

def test_challenges_progress_and_claim(client, app, gamification_setup):
    login(client)
    with app.app_context():
        user = User.query.filter_by(username="student").first()
        initial_xp = user.xp or 0
        
        # Initialize challenges
        challenges = get_or_create_user_challenges(user)
        assert len(challenges) > 0
        
        # Update challenge progress for lesson
        update_challenge_progress(user, "lesson", 1)
        
        lesson_uc = [uc for uc in user.user_challenges if uc.challenge.action_type == "lesson"][0]
        assert lesson_uc.is_completed is True
        assert lesson_uc.is_claimed is False
        uc_id = lesson_uc.id
        reward = lesson_uc.challenge.xp_reward

    # Claim challenge reward via endpoint
    response = client.post(f"/gamification/claim-challenge/{uc_id}", follow_redirects=True)
    assert response.status_code == 200
    assert f"+{reward} XP" in response.get_data(as_text=True)
    
    with app.app_context():
        user = User.query.filter_by(username="student").first()
        assert user.xp >= initial_xp + reward
        lesson_uc = db.session.get(UserChallenge, uc_id)
        assert lesson_uc.is_claimed is True

def test_claim_daily_goal_reward(client, app):
    login(client)
    with app.app_context():
        user = User.query.filter_by(username="student").first()
        user.daily_reward_claimed_date = None
        user.xp = 100
        db.session.commit()
        initial_xp = user.xp
        
    response = client.post("/gamification/claim-daily-goal", follow_redirects=True)
    assert response.status_code == 200
    assert "+50 XP" in response.get_data(as_text=True)
    
    with app.app_context():
        user = User.query.filter_by(username="student").first()
        assert user.xp == initial_xp + 50
        assert user.daily_reward_claimed_date == date.today()
