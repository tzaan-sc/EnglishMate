from app.extensions import db
from app.modules.learning.models import Vocabulary, VocabularyProgress


def login_student(client):
    return client.post("/auth/login", data={"email": "student@test.com", "password": "user123"}, follow_redirects=True)


def ensure_sample_vocabularies():
    v1 = Vocabulary.query.filter_by(word="meticulous").first()
    if not v1:
        v1 = Vocabulary(
            word="meticulous",
            pronunciation="/məˈtɪk.jə.ləs/",
            part_of_speech="adjective",
            meaning_vi="tỉ mỉ, cẩn thận từng chi tiết",
            example_en="He is meticulous about his work.",
            example_vi="Anh ấy rất tỉ mỉ trong công việc.",
            topic="Work",
            level="C1",
        )
        db.session.add(v1)

    v2 = Vocabulary.query.filter_by(word="pragmatic").first()
    if not v2:
        v2 = Vocabulary(
            word="pragmatic",
            pronunciation="/præɡˈmæt.ɪk/",
            part_of_speech="adjective",
            meaning_vi="thực tế, thực dụng",
            example_en="We need a pragmatic approach.",
            example_vi="Chúng ta cần một tiếp cận thực tế.",
            topic="Business",
            level="C1",
        )
        db.session.add(v2)

    db.session.commit()
    return v1, v2


def test_vocabulary_stats_render(client):
    login_student(client)

    with client.application.app_context():
        ensure_sample_vocabularies()

    res = client.get("/vocabulary/stats")
    assert res.status_code == 200
    assert "Thống Kê Từ Vựng Toàn Diện".encode("utf-8") in res.data
    assert "Biểu đồ tăng trưởng từ vựng".encode("utf-8") in res.data
    assert "Biểu đồ phân phối mức SRS Level".encode("utf-8") in res.data


def test_streak_and_metrics(client):
    login_student(client)

    with client.application.app_context():
        v1, _ = ensure_sample_vocabularies()
        prog = VocabularyProgress(user_id=1, vocabulary_id=v1.id, learned_count=3, review_count=5, srs_level=7)
        db.session.add(prog)
        db.session.commit()

    res = client.get("/vocabulary/stats")
    assert res.status_code == 200
    assert "Chuỗi học liên tiếp".encode("utf-8") in res.data
    assert "Tỷ lệ giữ lại từ vựng".encode("utf-8") in res.data


def test_topic_breakdown_and_timeline(client):
    login_student(client)

    with client.application.app_context():
        ensure_sample_vocabularies()

    res = client.get("/vocabulary/stats")
    assert res.status_code == 200
    assert "Phân tích độ thành thạo theo Chủ đề".encode("utf-8") in res.data
    assert "Timeline Từ đã thành thạo".encode("utf-8") in res.data
