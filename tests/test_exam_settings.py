import pytest
from app.extensions import db
from app.backend.auth.models import User
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

def test_exam_settings_toggle_sound_effects_off(client, app):
    login(client)
    response = client.post("/settings", data={
        "exam_default_type": "TOEIC",
        "exam_default_time_limit": "30",
        # Notice exam_sound_effects is not sent (switch off)
    }, follow_redirects=True)
    assert response.status_code == 200
    with app.app_context():
        user = User.query.filter_by(username="student").first()
        assert user.exam_sound_effects is False

def test_exam_sound_files_exist():
    import os
    sound_dir = os.path.join("app", "frontend", "static", "sounds")
    expected_sounds = ["tick.wav", "select.wav", "timeout.wav", "success.wav"]
    for sound in expected_sounds:
        sound_path = os.path.join(sound_dir, sound)
        assert os.path.exists(sound_path), f"Missing sound file: {sound_path}"
        assert os.path.getsize(sound_path) > 0, f"Sound file is empty: {sound_path}"

def test_exam_audio_js_exists():
    import os
    js_path = os.path.join("app", "frontend", "static", "js", "exam_audio.js")
    assert os.path.exists(js_path)
    with open(js_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "ExamSoundEffects" in content
    assert "playSelect" in content
    assert "playTick" in content
    assert "playTimeout" in content
    assert "playSubmit" in content

