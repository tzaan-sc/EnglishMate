from app.extensions import db
from app.modules.auth.models import User
from app.modules.learning.models import Lesson, LessonProgress, LessonFavorite
from tests.conftest import login


def ensure_sample_lessons():
    l1 = Lesson.query.filter_by(title="Present Simple Tense").first()
    if not l1:
        l1 = Lesson(
            title="Present Simple Tense",
            level="A1",
            skill="Grammar",
            short_description="Học thì hiện tại đơn trong tiếng Anh.",
            content="Nội dung thì hiện tại đơn...",
            examples="I work every day.",
            view_count=15
        )
        db.session.add(l1)

    l2 = Lesson.query.filter_by(title="Business Email Etiquette").first()
    if not l2:
        l2 = Lesson(
            title="Business Email Etiquette",
            level="B2",
            skill="Reading",
            short_description="Kỹ năng viết và đọc email công việc.",
            content="Nội dung email etiquette...",
            examples="Dear Mr. Smith...",
            view_count=50
        )
        db.session.add(l2)

    db.session.commit()
    return l1, l2


def test_lesson_list_render(client):
    login(client)

    with client.application.app_context():
        ensure_sample_lessons()

    res = client.get("/lessons")
    assert res.status_code == 200
    assert "Tìm theo Tiêu đề / Nội dung".encode("utf-8") in res.data
    assert "Cấp độ (CEFR)".encode("utf-8") in res.data


def test_search_by_title_and_content(client):
    login(client)

    with client.application.app_context():
        ensure_sample_lessons()

    res = client.get("/lessons?q=Business")
    assert res.status_code == 200
    assert "Business Email Etiquette".encode("utf-8") in res.data


def test_filter_by_level_skill_status(client):
    login(client)

    with client.application.app_context():
        l1, l2 = ensure_sample_lessons()
        user = User.query.filter_by(email="student@test.com").first()
        prog = LessonProgress(user_id=user.id, lesson_id=l1.id)
        db.session.add(prog)
        db.session.commit()

    res_completed = client.get("/lessons?status=completed")
    assert res_completed.status_code == 200
    assert "Present Simple Tense".encode("utf-8") in res_completed.data

    res_new = client.get("/lessons?status=new")
    assert res_new.status_code == 200
    assert "Business Email Etiquette".encode("utf-8") in res_new.data


def test_sort_by_popularity_and_difficulty(client):
    login(client)

    with client.application.app_context():
        ensure_sample_lessons()

    res_pop = client.get("/lessons?sort=popularity")
    assert res_pop.status_code == 200

    res_diff = client.get("/lessons?sort=difficulty_asc")
    assert res_diff.status_code == 200


def test_favorite_and_preview_endpoints(client):
    login(client)

    with client.application.app_context():
        l1, _ = ensure_sample_lessons()
        lesson_id = l1.id

    # Test favorite POST
    res_fav = client.post(f"/lessons/{lesson_id}/favorite", headers={"X-Requested-With": "XMLHttpRequest"})
    assert res_fav.status_code == 200
    assert res_fav.json["success"] is True
    assert res_fav.json["is_favorite"] is True

    # Test preview GET
    res_prev = client.get(f"/lessons/{lesson_id}/preview")
    assert res_prev.status_code == 200
    assert res_prev.json["title"] == "Present Simple Tense"
    assert res_prev.json["is_favorite"] is True
