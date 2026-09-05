from app.extensions import db
from app.modules.learning.models import Lesson, LessonProgress, LessonFavorite
from tests.conftest import login


def ensure_skill_lessons():
    skills_data = [
        ("A1", "Listening", "Listening A1 Demo", "Short audio conversation", "Audio content...", "Dialogue example"),
        ("A2", "Listening", "Airport Announcements", "Gate and boarding calls", "Airport audio...", "Flight VN123"),
        ("B1", "Reading", "Reading B1 Demo", "Short reading article", "Article text about travel...", "Reading sample"),
        ("B2", "Reading", "Workplace Business Email", "Professional inquiry", "Dear team...", "Best regards"),
        ("A1", "Speaking", "Speaking A1 Demo", "Self introduction", "Introduce yourself...", "My name is John"),
        ("B2", "Speaking", "Job Interview Prep", "Interview questions", "STAR method...", "Tell me about yourself"),
        ("A1", "Writing", "Writing A1 Demo", "Daily schedule note", "My day plan...", "First I wake up"),
        ("B2", "Writing", "Formal Request Letter", "Official service letter", "I am writing to...", "Sincerely"),
    ]

    lessons = []
    for level, skill, title, desc, content, ex in skills_data:
        lesson = Lesson.query.filter_by(title=title).first()
        if not lesson:
            lesson = Lesson(
                level=level,
                skill=skill,
                title=title,
                short_description=desc,
                content=content,
                examples=ex,
                is_active=True,
                view_count=10
            )
            db.session.add(lesson)
        lessons.append(lesson)
    db.session.commit()
    return lessons


def test_default_skill_all(client):
    login(client)
    with client.application.app_context():
        ensure_skill_lessons()

    res = client.get("/lessons")
    assert res.status_code == 200
    assert "Thư viện Bài học".encode("utf-8") in res.data
    assert "Luyện Nghe".encode("utf-8") in res.data
    assert "Đọc hiểu".encode("utf-8") in res.data
    assert "Luyện Nói".encode("utf-8") in res.data
    assert "Luyện Viết".encode("utf-8") in res.data
    assert "Listening A1 Demo".encode("utf-8") in res.data
    assert "Reading B1 Demo".encode("utf-8") in res.data


def test_listening_tab(client):
    login(client)
    with client.application.app_context():
        ensure_skill_lessons()

    res = client.get("/lessons?skill=Listening")
    assert res.status_code == 200
    assert "Luyện Nghe".encode("utf-8") in res.data
    assert "Listening A1 Demo".encode("utf-8") in res.data
    assert "Airport Announcements".encode("utf-8") in res.data
    # Should not include other skills
    assert "Reading B1 Demo".encode("utf-8") not in res.data
    assert "Speaking A1 Demo".encode("utf-8") not in res.data


def test_reading_tab(client):
    login(client)
    with client.application.app_context():
        ensure_skill_lessons()

    res = client.get("/lessons?skill=Reading")
    assert res.status_code == 200
    assert "Đọc hiểu".encode("utf-8") in res.data
    assert "Reading B1 Demo".encode("utf-8") in res.data
    assert "Workplace Business Email".encode("utf-8") in res.data
    assert "Listening A1 Demo".encode("utf-8") not in res.data


def test_speaking_tab(client):
    login(client)
    with client.application.app_context():
        ensure_skill_lessons()

    res = client.get("/lessons?skill=Speaking")
    assert res.status_code == 200
    assert "Luyện Nói".encode("utf-8") in res.data
    assert "Speaking A1 Demo".encode("utf-8") in res.data
    assert "Job Interview Prep".encode("utf-8") in res.data
    assert "Reading B1 Demo".encode("utf-8") not in res.data


def test_writing_tab(client):
    login(client)
    with client.application.app_context():
        ensure_skill_lessons()

    res = client.get("/lessons?skill=Writing")
    assert res.status_code == 200
    assert "Luyện Viết".encode("utf-8") in res.data
    assert "Writing A1 Demo".encode("utf-8") in res.data
    assert "Formal Request Letter".encode("utf-8") in res.data
    assert "Listening A1 Demo".encode("utf-8") not in res.data


def test_invalid_skill_fallback_to_all(client):
    login(client)
    with client.application.app_context():
        ensure_skill_lessons()

    res = client.get("/lessons?skill=NonExistentSkill123")
    assert res.status_code == 200
    assert "Thư viện Bài học".encode("utf-8") in res.data
    assert "Listening A1 Demo".encode("utf-8") in res.data


def test_skill_combined_with_level_filter(client):
    login(client)
    with client.application.app_context():
        ensure_skill_lessons()

    res = client.get("/lessons?skill=Listening&level=A2")
    assert res.status_code == 200
    assert "Airport Announcements".encode("utf-8") in res.data
    # A1 listening should not be in the list
    assert "Listening A1 Demo".encode("utf-8") not in res.data


def test_skill_search(client):
    login(client)
    with client.application.app_context():
        ensure_skill_lessons()

    res = client.get("/lessons?skill=Reading&search=Workplace")
    assert res.status_code == 200
    assert "Workplace Business Email".encode("utf-8") in res.data
    assert "Reading B1 Demo".encode("utf-8") not in res.data


def test_empty_state_display(client):
    login(client)
    with client.application.app_context():
        ensure_skill_lessons()

    res = client.get("/lessons?skill=Writing&search=NonExistentTermXYZ")
    assert res.status_code == 200
    assert "Không tìm thấy bài học phù hợp".encode("utf-8") in res.data


def test_statistics_calculation_per_skill(client):
    login(client)
    with client.application.app_context():
        lessons = ensure_skill_lessons()
        listening_lesson = next(l for l in lessons if l.skill == "Listening")
        
        # Mark as completed
        if not LessonProgress.query.filter_by(user_id=1, lesson_id=listening_lesson.id).first():
            db.session.add(LessonProgress(user_id=1, lesson_id=listening_lesson.id))
            db.session.commit()

    res = client.get("/lessons?skill=Listening")
    assert res.status_code == 200
    assert "Đã hoàn thành".encode("utf-8") in res.data
    assert "Thời lượng audio đã học".encode("utf-8") in res.data
