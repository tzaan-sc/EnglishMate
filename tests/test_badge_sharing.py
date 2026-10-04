import pytest
from datetime import datetime
from app.extensions import db
from app.backend.auth.models import User
from app.backend.learning.models import Badge, UserBadge
from tests.conftest import login

@pytest.fixture
def badge_setup(app):
    with app.app_context():
        if Badge.query.count() == 0:
            b1 = Badge(code="FIRST_STEP", name="Bước đầu tiên", description="Hoàn thành bài học đầu tiên", icon="🎯", category="LESSONS", xp_reward=50, req_type="lessons_count", req_value=1)
            b2 = Badge(code="VOCAB_MASTER", name="Bậc thầy từ vựng", description="Học 50 từ vựng", icon="📚", category="VOCAB", xp_reward=100, req_type="vocab_count", req_value=50)
            db.session.add_all([b1, b2])
            db.session.commit()

def test_badge_share_modal_rendered_in_base(client, badge_setup):
    """Test that _badge_share_modal.html is included in pages for authenticated users."""
    login(client)
    res = client.get("/gamification")
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    
    # Check modal presence
    assert 'id="badgeUnlockModal"' in html
    assert 'id="btnDownloadBadgeCard"' in html
    assert 'id="btnShareBadgeFb"' in html
    assert 'id="btnShareBadgeTw"' in html
    assert 'id="btnCopyBadgeLink"' in html
    assert 'id="badgeCardPreview"' in html
    assert 'id="badgeConfettiCanvas"' in html

def test_unlocked_badge_has_share_button(client, app, badge_setup):
    """Test that unlocked badges display the 'Chia sẻ & Tải ảnh' button with data attributes."""
    with app.app_context():
        user = User.query.filter_by(email="student@test.com").first()
        badge = Badge.query.filter_by(code="FIRST_STEP").first()
        if badge and user:
            # Grant badge to user
            existing = UserBadge.query.filter_by(user_id=user.id, badge_id=badge.id).first()
            if not existing:
                ub = UserBadge(user_id=user.id, badge_id=badge.id, unlocked_at=datetime.utcnow())
                db.session.add(ub)
                db.session.commit()

    login(client, email="student@test.com", password="user123")
    res = client.get("/gamification?tab=badges")
    assert res.status_code == 200
    html = res.get_data(as_text=True)

    assert "btn-share-badge-card" in html
    assert 'data-badge-name="Bước đầu tiên"' in html
    assert "Chia sẻ &amp; Tải ảnh" in html or "Chia sẻ & Tải ảnh" in html

def test_badge_unlock_modal_template_standalone(app):
    """Test that badge_unlock_modal.html can be rendered standalone."""
    with app.app_context():
        from flask import render_template_string
        rendered = render_template_string('{% include "badge_unlock_modal.html" %}')
        assert 'id="badgeUnlockModal"' in rendered
        assert 'btnDownloadBadgeCard' in rendered
        assert 'btnShareBadgeFb' in rendered
