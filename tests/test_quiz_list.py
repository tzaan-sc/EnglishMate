from app.extensions import db
from app.modules.learning.models import Quiz
from tests.conftest import login


def ensure_sample_quiz():
    q = Quiz.query.filter_by(title="Kiểm Tra Ngữ Pháp Tổng Hợp A1").first()
    if not q:
        q = Quiz(
            title="Kiểm Tra Ngữ Pháp Tổng Hợp A1",
            category="Grammar",
            level="A1",
            skill="Grammar",
            difficulty="Easy",
            description="Bài kiểm tra ngữ pháp A1.",
            question_count=10,
            duration_minutes=10,
            view_count=50
        )
        db.session.add(q)
        db.session.commit()
    return q


def test_quiz_list_render(client):
    login(client)
    res = client.get("/quizzes/list")
    assert res.status_code == 200
    assert "Danh Sách Bài Quiz".encode("utf-8") in res.data
    assert "Kiểm Tra Ngữ Pháp Tổng Hợp A1".encode("utf-8") in res.data


def test_quiz_list_browse_and_filters(client):
    login(client)

    with client.application.app_context():
        ensure_sample_quiz()

    res_cat = client.get("/quizzes/list?category=Grammar")
    assert res_cat.status_code == 200
    assert "Kiểm Tra Ngữ Pháp".encode("utf-8") in res_cat.data

    res_level = client.get("/quizzes/list?level=A1")
    assert res_level.status_code == 200
    assert "Kiểm Tra Ngữ Pháp".encode("utf-8") in res_level.data

    res_diff = client.get("/quizzes/list?difficulty=Easy")
    assert res_diff.status_code == 200

    res_sort = client.get("/quizzes/list?sort=popularity")
    assert res_sort.status_code == 200


def test_quiz_detail_preview(client):
    login(client)

    with client.application.app_context():
        q = ensure_sample_quiz()
        quiz_id = q.id

    res = client.get(f"/quizzes/{quiz_id}/preview")
    assert res.status_code == 200
    json_data = res.get_json()
    assert json_data["success"] is True
    assert json_data["quiz"]["title"] == "Kiểm Tra Ngữ Pháp Tổng Hợp A1"
