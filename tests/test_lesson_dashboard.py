from app.extensions import db
from app.modules.learning.models import Lesson, LessonProgress
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
        )
        db.session.add(l2)

    db.session.commit()
    return l1, l2


def test_lesson_dashboard_render(client):
    login(client)

    with client.application.app_context():
        ensure_sample_lessons()

    res = client.get("/lessons")
    assert res.status_code == 200
    assert "Bảng điều khiển bài học".encode("utf-8") in res.data
    assert "Tổng số bài học".encode("utf-8") in res.data
    assert "Tiến độ Bài học theo Cấp độ".encode("utf-8") in res.data


def test_lesson_counts_and_metrics(client):
    login(client)

    with client.application.app_context():
        l1, l2 = ensure_sample_lessons()
        prog = LessonProgress(user_id=1, lesson_id=l1.id)
        db.session.add(prog)
        db.session.commit()

    res = client.get("/lessons")
    assert res.status_code == 200
    assert "Đã hoàn thành".encode("utf-8") in res.data


def test_current_and_recommended_lesson(client):
    login(client)

    with client.application.app_context():
        l1, l2 = ensure_sample_lessons()

    res = client.get("/lessons")
    assert res.status_code == 200
    assert "BÀI HỌC ĐỀ XUẤT TIẾP THEO".encode("utf-8") in res.data
