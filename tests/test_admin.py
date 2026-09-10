from tests.conftest import login


def test_user_cannot_access_admin(client):
    login(client)
    assert client.get("/admin").status_code == 403


def test_admin_can_access_admin(client):
    login(client, "admin@test.com", "admin123")
    response = client.get("/admin")
    assert response.status_code == 200
    assert "Thống kê hệ thống".encode() in response.data


def test_all_admin_pages_render(client):
    login(client, "admin@test.com", "admin123")
    for path in ["/admin", "/admin/lessons", "/admin/lessons/new", "/admin/vocabulary",
                 "/admin/vocabulary/new", "/admin/users"]:
        response = client.get(path)
        assert response.status_code == 200, path


def test_admin_lessons_filtering(client):
    login(client, "admin@test.com", "admin123")
    # Test filtering with params
    res = client.get("/admin/lessons?search=test&skill=Writing&level=C2&status=active")
    assert res.status_code == 200
    assert "Quản lý Bài học".encode() in res.data


def test_admin_lesson_create_writing_c2_and_toggle_status(client, app):
    login(client, "admin@test.com", "admin123")
    # Create lesson with Writing skill and C2 level
    res = client.post("/admin/lessons/new", data={
        "title": "Advanced C2 Writing Essay Skills",
        "level": "C2",
        "skill": "Writing",
        "short_description": "Master advanced essay composition for C2 level.",
        "content": "<p>This is rich HTML content for essay writing.</p>",
        "examples": "Example 1: In light of the aforementioned evidence...\nExample 2: It is widely acknowledged that..."
    }, follow_redirects=True)
    assert res.status_code == 200
    assert "Đã thêm bài học mới".encode() in res.data

    with app.app_context():
        from app.modules.learning.models import Lesson
        lesson = Lesson.query.filter_by(title="Advanced C2 Writing Essay Skills").first()
        assert lesson is not None
        assert lesson.skill == "Writing"
        assert lesson.level == "C2"
        assert lesson.is_active is True
        lesson_id = lesson.id

    # Toggle status to hide
    toggle_res = client.post(f"/admin/lessons/{lesson_id}/toggle-status", follow_redirects=True)
    assert toggle_res.status_code == 200
    with app.app_context():
        from app.extensions import db
        lesson = db.session.get(Lesson, lesson_id)
        assert lesson.is_active is False

    # Toggle status to re-open
    reopen_res = client.post(f"/admin/lessons/{lesson_id}/toggle-status", follow_redirects=True)
    assert reopen_res.status_code == 200
    with app.app_context():
        lesson = db.session.get(Lesson, lesson_id)
        assert lesson.is_active is True


def test_admin_lesson_create_with_skill_data_json(client, app):
    login(client, "admin@test.com", "admin123")

    # 1. Create a Listening lesson with audio_url and accent
    res = client.post("/admin/lessons/new", data={
        "title": "Listening Studio Practice Lesson",
        "level": "B2",
        "skill": "Listening",
        "short_description": "Podcast about technology innovations.",
        "content": "Listen to the discussion and take notes.",
        "examples": "Example conversation line 1\nExample line 2",
        "audio_url": "https://example.com/podcast.mp3",
        "accent": "UK",
        "audio_duration": "03:45",
        "listening_transcript": "Host: Welcome to the show!\nGuest: Thank you for inviting me."
    }, follow_redirects=True)
    assert res.status_code == 200

    with app.app_context():
        from app.modules.learning.models import Lesson
        lesson = Lesson.query.filter_by(title="Listening Studio Practice Lesson").first()
        assert lesson is not None
        assert lesson.skill_data is not None
        assert lesson.skill_data.get("audio_url") == "https://example.com/podcast.mp3"
        assert lesson.skill_data.get("accent") == "UK"
        assert lesson.skill_data.get("audio_duration") == "03:45"
        lesson_id = lesson.id

    # Test that student view /listening/<id> loads this lesson properly
    student_res = client.get(f"/listening/{lesson_id}")
    assert student_res.status_code == 200
    assert "Listening Studio Practice Lesson".encode() in student_res.data


