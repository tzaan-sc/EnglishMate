import pytest
from app.extensions import db
from app.modules.auth.models import User
from tests.conftest import login

def test_exam_settings_fields_defaults(app):
    with app.app_context():
        # Check that a default user has the correct default exam settings
        user = User(username="test_settings", email="settings@test.com")
        user.set_password("password")
        db.session.add(user)
        db.session.commit()
        
        assert user.exam_default_type == "TOEIC"
        assert user.exam_default_time_limit == 120
        assert user.exam_show_timer is True
        assert user.exam_allow_pause is True
        assert user.exam_show_realtime_score is False
        assert user.exam_auto_submit is True
        assert user.exam_sound_effects is True

def test_exam_settings_page_requires_login(client):
    response = client.get("/settings")
    assert response.status_code == 302

def test_exam_settings_get_success(client):
    login(client)
    response = client.get("/settings")
    assert response.status_code == 200
    assert "Cài Đặt Đề Thi Cá Nhân" in response.get_data(as_text=True)

def test_exam_settings_post_updates_db(client, app):
    login(client)
    # Post updates
    response = client.post("/settings", data={
        "exam_default_type": "IELTS",
        "exam_default_time_limit": "60",
        "exam_show_timer": "on",
        "exam_allow_pause": "off", # omitted/off means False
        "exam_show_realtime_score": "on",
        "exam_auto_submit": "off",
        "exam_sound_effects": "on"
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert "Cài đặt đề thi đã được cập nhật thành công!" in response.get_data(as_text=True)
    
    with app.app_context():
        user = User.query.filter_by(username="student").first()
        assert user.exam_default_type == "IELTS"
        assert user.exam_default_time_limit == 60
        assert user.exam_show_timer is True
        assert user.exam_allow_pause is False
        assert user.exam_show_realtime_score is True
        assert user.exam_auto_submit is False
        assert user.exam_sound_effects is True
