from app.extensions import db
from app.modules.auth.models import User
from app.modules.learning.models import Vocabulary, VocabularyProgress


def login_student(client):
    return client.post("/auth/login", data={"email": "student@test.com", "password": "user123"}, follow_redirects=True)


def test_vocabulary_dashboard_stats(client):
    login_student(client)

    res = client.get("/vocabulary")
    assert res.status_code == 200
    assert "Thư viện Từ vựng & Flashcards".encode("utf-8") in res.data
    assert "Tổng từ vựng".encode("utf-8") in res.data
    assert "Mục tiêu ngày".encode("utf-8") in res.data


def test_level_vocabulary_progress(client):
    login_student(client)

    res = client.get("/vocabulary")
    assert res.status_code == 200
    assert "CEFR (A0-C2)".encode("utf-8") in res.data
    assert "TOEIC".encode("utf-8") in res.data


def test_set_vocab_goal(client):
    login_student(client)

    res = client.post("/vocabulary/set-goal", data={"goal": "30"}, follow_redirects=True)
    assert res.status_code == 200
    assert "Đã cập nhật mục tiêu học từ vựng hàng ngày thành 30 từ/ngày".encode("utf-8") in res.data

    with client.application.app_context():
        user = User.query.filter_by(email="student@test.com").first()
        assert user.daily_vocab_goal == 30


def test_today_learned_count_tracking(client):
    login_student(client)

    with client.application.app_context():
        v = Vocabulary.query.first()
        if not v:
            v = Vocabulary(word="apple", pronunciation="ˈæp.əl", part_of_speech="noun", meaning_vi="quả táo", example_en="An apple a day", example_vi="Một quả táo mỗi ngày", topic="Food", level="A1")
            db.session.add(v)
            db.session.commit()
        word_id = v.id

    res_learn = client.post(f"/vocabulary/{word_id}/learn", follow_redirects=True)
    assert res_learn.status_code == 200

    res_dash = client.get("/vocabulary")
    assert res_dash.status_code == 200
    assert "Đã học".encode("utf-8") in res_dash.data
