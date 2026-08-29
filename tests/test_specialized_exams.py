from app.extensions import db
from app.modules.exams.models import Exam
from tests.conftest import login


def test_specialized_exams_hub_render(client):
    login(client)

    res = client.get("/specialized")
    assert res.status_code == 200
    assert "Trung Tâm Đề Thi Chuyên Biệt".encode("utf-8") in res.data
    assert "TOEIC Simulation".encode("utf-8") in res.data
    assert "IELTS Practice".encode("utf-8") in res.data
    assert "TOEFL Preparation".encode("utf-8") in res.data
    assert "Placement Tests".encode("utf-8") in res.data


def test_specialized_placement_shortcut(client):
    login(client)

    res = client.get("/specialized/placement", follow_redirects=True)
    assert res.status_code == 200


def test_specialized_progress_shortcut(client):
    login(client)

    res = client.get("/specialized/progress", follow_redirects=True)
    assert res.status_code == 200


def test_specialized_timed_practice_config_and_launch(client):
    login(client)

    # GET config page
    res_get = client.get("/specialized/timed-practice")
    assert res_get.status_code == 200
    assert "Cài Đặt Phiên Luyện Tập Có Giới Hạn Thời Gian".encode("utf-8") in res_get.data

    # POST create timed session
    res_post = client.post("/specialized/timed-practice", data={
        "duration": "15",
        "question_count": "10",
        "difficulty": "Medium",
        "skill": "Grammar"
    }, follow_redirects=True)
    assert res_post.status_code == 200

    with client.application.app_context():
        timed_ex = Exam.query.filter_by(category="Timed").order_by(Exam.id.desc()).first()
        assert timed_ex is not None
        assert timed_ex.duration == 15


def test_specialized_category_filtering(client):
    login(client)

    res_toeic = client.get("/specialized?category=TOEIC")
    assert res_toeic.status_code == 200

    res_ielts = client.get("/specialized?category=IELTS")
    assert res_ielts.status_code == 200
