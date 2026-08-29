from app.extensions import db
from app.modules.auth.models import User
from app.modules.learning.models import Lesson, LessonNote, LessonBookmark, LessonReport
from tests.conftest import login


def ensure_sample_lesson():
    l = Lesson.query.filter_by(title="Past Continuous Tense").first()
    if not l:
        l = Lesson(
            title="Past Continuous Tense",
            level="B1",
            skill="Grammar",
            short_description="Học thì quá khứ tiếp diễn.",
            content="Nội dung chi tiết thì quá khứ tiếp diễn...",
            examples="I was studying when he called.",
        )
        db.session.add(l)
        db.session.commit()
    return l


def test_lesson_detail_render(client):
    login(client)

    with client.application.app_context():
        l = ensure_sample_lesson()
        lesson_id = l.id

    res = client.get(f"/lessons/{lesson_id}")
    assert res.status_code == 200
    assert "Past Continuous Tense".encode("utf-8") in res.data
    assert "Ví dụ thực tế sử dụng".encode("utf-8") in res.data


def test_save_lesson_notes(client):
    login(client)

    with client.application.app_context():
        l = ensure_sample_lesson()
        lesson_id = l.id

    res = client.post(
        f"/lessons/{lesson_id}/notes",
        data={"note": "Cần nhớ cấu trúc Was/Were + V-ing"},
        follow_redirects=True,
    )
    assert res.status_code == 200
    assert "Đã lưu ghi chú bài học".encode("utf-8") in res.data

    with client.application.app_context():
        user = User.query.filter_by(email="student@test.com").first()
        note = LessonNote.query.filter_by(user_id=user.id, lesson_id=lesson_id).first()
        assert note is not None
        assert "Was/Were" in note.content


def test_toggle_lesson_bookmark(client):
    login(client)

    with client.application.app_context():
        l = ensure_sample_lesson()
        lesson_id = l.id

    res = client.post(
        f"/lessons/{lesson_id}/bookmark",
        json={"section_index": 2},
        headers={"X-Requested-With": "XMLHttpRequest"},
    )
    assert res.status_code == 200
    assert res.json["success"] is True
    assert res.json["is_bookmarked"] is True


def test_report_lesson_content(client):
    login(client)

    with client.application.app_context():
        l = ensure_sample_lesson()
        lesson_id = l.id

    res = client.post(
        f"/lessons/{lesson_id}/report",
        data={"reason": "Lỗi chính tả / Ngữ pháp", "details": "Sai chính tả ở ví dụ số 1"},
        follow_redirects=True,
    )
    assert res.status_code == 200
    assert "Đã gửi báo cáo nội dung".encode("utf-8") in res.data

    with client.application.app_context():
        report = LessonReport.query.filter_by(lesson_id=lesson_id).first()
        assert report is not None
        assert report.reason == "Lỗi chính tả / Ngữ pháp"
