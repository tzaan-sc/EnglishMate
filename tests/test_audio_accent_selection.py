import pytest
import io
from app.extensions import db
from app.backend.learning.models import Lesson
from tests.conftest import login
from app.backend.admin.importer import parse_and_validate_csv, commit_import_records


def test_lesson_model_audio_fields(app):
    """Test that Lesson model stores audio_url and audio_url_uk properly."""
    with app.app_context():
        lesson = Lesson(
            title="Business Presentation Listening",
            level="B2",
            skill="Listening",
            short_description="Learn how to present effectively in English.",
            content="Audio transcript here...",
            examples="Speaker A: Welcome everyone.|Chào mọi người.",
            audio_url="https://example.com/audio_us.mp3",
            audio_url_uk="https://example.com/audio_uk.mp3",
            skill_data={
                "accent": "US",
                "audio_duration": "03:45",
                "audio_url": "https://example.com/audio_us.mp3",
                "audio_url_uk": "https://example.com/audio_uk.mp3",
                "transcript": "Speaker A: Welcome everyone."
            }
        )
        db.session.add(lesson)
        db.session.commit()

        saved = Lesson.query.filter_by(title="Business Presentation Listening").first()
        assert saved is not None
        assert saved.audio_url == "https://example.com/audio_us.mp3"
        assert saved.audio_url_uk == "https://example.com/audio_uk.mp3"
        assert saved.skill_data.get("audio_url_uk") == "https://example.com/audio_uk.mp3"


def test_admin_create_listening_lesson_with_dual_audio(client):
    """Test admin form submission creates lesson with US & UK audio URLs."""
    login(client, "admin@test.com", "admin123")
    res = client.post("/admin/lessons/new", data={
        "title": "Dual Audio Podcasting",
        "level": "B1",
        "skill": "Listening",
        "short_description": "A podcast conversation with US and UK accents.",
        "content": "Full text transcript...",
        "examples": "Line 1: Hello|Xin chào",
        "audio_url": "https://cdn.example.com/us_track.mp3",
        "audio_url_uk": "https://cdn.example.com/uk_track.mp3",
        "accent": "UK",
        "audio_duration": "04:12",
        "listening_transcript": "Host: Welcome to the show!"
    }, follow_redirects=True)

    assert res.status_code == 200
    with client.application.app_context():
        lesson = Lesson.query.filter_by(title="Dual Audio Podcasting").first()
        assert lesson is not None
        assert lesson.audio_url == "https://cdn.example.com/us_track.mp3"
        assert lesson.audio_url_uk == "https://cdn.example.com/uk_track.mp3"
        assert lesson.skill_data.get("accent") == "UK"
        assert lesson.skill_data.get("audio_url_uk") == "https://cdn.example.com/uk_track.mp3"


def test_admin_edit_listening_lesson_dual_audio(client):
    """Test admin editing a lesson to add UK audio URL."""
    login(client, "admin@test.com", "admin123")
    with client.application.app_context():
        lesson = Lesson(
            title="Editing Audio Track Lesson",
            level="A2",
            skill="Listening",
            short_description="Initial short desc",
            content="Initial content",
            examples="Line 1: Test",
            audio_url="https://cdn.example.com/orig_us.mp3"
        )
        db.session.add(lesson)
        db.session.commit()
        lesson_id = lesson.id

    res = client.post(f"/admin/lessons/{lesson_id}/edit", data={
        "title": "Editing Audio Track Lesson Updated",
        "level": "A2",
        "skill": "Listening",
        "short_description": "Updated desc",
        "content": "Updated content",
        "examples": "Line 1: Test",
        "audio_url": "https://cdn.example.com/updated_us.mp3",
        "audio_url_uk": "https://cdn.example.com/updated_uk.mp3",
        "accent": "US",
        "audio_duration": "02:30",
        "listening_transcript": "Speaker: Hi there!"
    }, follow_redirects=True)

    assert res.status_code == 200
    with client.application.app_context():
        updated = db.session.get(Lesson, lesson_id)
        assert updated.title == "Editing Audio Track Lesson Updated"
        assert updated.audio_url == "https://cdn.example.com/updated_us.mp3"
        assert updated.audio_url_uk == "https://cdn.example.com/updated_uk.mp3"


def test_importer_with_audio_url_uk(client):
    """Test importing lesson CSV data with audio_url_uk column."""
    login(client, email="admin@test.com", password="admin123")
    csv_content = (
        "title,level,skill,short_description,content,examples,audio_url,audio_url_uk,accent,audio_duration,listening_transcript\n"
        "Imported Listening Lesson,B1,Listening,Practice listening,Listening text,Sample: Hello,https://cdn.example.com/us.mp3,https://cdn.example.com/uk.mp3,US,03:00,John: Good morning\n"
    )
    file_stream = io.BytesIO(csv_content.encode("utf-8"))

    res = client.post(
        "/admin/import/validate",
        data={"content_type": "lessons", "file": (file_stream, "lessons.csv")},
        content_type="multipart/form-data"
    )
    assert res.status_code == 200
    json_data = res.get_json()
    assert json_data["success"] is True
    assert json_data["valid_count"] == 1
    rec_data = json_data["valid_records"][0]["data"]
    assert rec_data.get("audio_url") == "https://cdn.example.com/us.mp3"
    assert rec_data.get("audio_url_uk") == "https://cdn.example.com/uk.mp3"

    res_commit = client.post(
        "/admin/import/commit",
        json={"content_type": "lessons", "valid_records": json_data["valid_records"], "mode": "insert_or_update"}
    )
    assert res_commit.status_code == 200
    assert res_commit.get_json()["success"] is True

    with client.application.app_context():
        imported_lesson = Lesson.query.filter_by(title="Imported Listening Lesson").first()
        assert imported_lesson is not None
        assert imported_lesson.audio_url == "https://cdn.example.com/us.mp3"
        assert imported_lesson.audio_url_uk == "https://cdn.example.com/uk.mp3"


def test_listening_detail_page_renders_accent_switcher(client):
    """Test that listening detail page renders audio element and US/UK switcher buttons."""
    login(client)
    with client.application.app_context():
        lesson = Lesson(
            title="Coffee Shop Ordering Practice",
            level="A1",
            skill="Listening",
            short_description="Ordering drinks at a cafe.",
            content="Barista: What can I get you?\nCustomer: A latte please.",
            examples="What would you like?|Bạn muốn dùng gì?",
            audio_url="https://audio.example.com/cafe_us.mp3",
            audio_url_uk="https://audio.example.com/cafe_uk.mp3",
            skill_data={
                "accent": "US",
                "audio_duration": "02:15",
                "audio_url": "https://audio.example.com/cafe_us.mp3",
                "audio_url_uk": "https://audio.example.com/cafe_uk.mp3",
                "transcript": "Barista: What can I get you?\nCustomer: A latte please."
            },
            is_active=True
        )
        db.session.add(lesson)
        db.session.commit()
        lesson_id = lesson.id

    res = client.get(f"/listening/{lesson_id}")
    assert res.status_code == 200
    html = res.data.decode("utf-8")

    # Check for HTML5 audio element
    assert 'id="studioAudioElement"' in html

    # Check for Accent Switcher buttons [ US | UK ]
    assert 'id="btnAccentUS"' in html
    assert 'id="btnAccentUK"' in html
    assert '🇺🇸 US' in html
    assert '🇬🇧 UK' in html
    assert 'id="studioAccentBadge"' in html

    # Check that audio URLs are passed to JavaScript
    assert "https://audio.example.com/cafe_us.mp3" in html
    assert "https://audio.example.com/cafe_uk.mp3" in html
