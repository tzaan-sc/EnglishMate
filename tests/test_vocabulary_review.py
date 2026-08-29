from datetime import datetime, timedelta
from app.extensions import db
from app.modules.learning.models import Vocabulary, VocabularyProgress


def login_student(client):
    return client.post("/auth/login", data={"email": "student@test.com", "password": "user123"}, follow_redirects=True)


def ensure_sample_vocabularies():
    v1 = Vocabulary.query.filter_by(word="resilient").first()
    if not v1:
        v1 = Vocabulary(
            word="resilient",
            pronunciation="/rɪˈzɪl.jənt/",
            part_of_speech="adjective",
            meaning_vi="kiên cường, có khả năng phục hồi nhanh",
            example_en="She is a resilient person.",
            example_vi="Cô ấy là một người kiên cường.",
            topic="Personality",
            level="B2",
        )
        db.session.add(v1)

    v2 = Vocabulary.query.filter_by(word="persistent").first()
    if not v2:
        v2 = Vocabulary(
            word="persistent",
            pronunciation="/pəˈsɪs.tənt/",
            part_of_speech="adjective",
            meaning_vi="kiên trì, bền bỉ",
            example_en="He is persistent in his efforts.",
            example_vi="Anh ấy kiên trì trong các nỗ lực của mình.",
            topic="Personality",
            level="B2",
        )
        db.session.add(v2)

    db.session.commit()
    return v1, v2


def test_review_vocabulary_render(client):
    login_student(client)

    with client.application.app_context():
        ensure_sample_vocabularies()

    res = client.get("/vocabulary/review")
    assert res.status_code == 200
    assert "Ôn Tập Từ Vựng (SRS)".encode("utf-8") in res.data
    assert "SRS Level".encode("utf-8") in res.data
    assert "Dễ (+2 Level)".encode("utf-8") in res.data


def test_review_modes(client):
    login_student(client)

    with client.application.app_context():
        ensure_sample_vocabularies()

    for mode in ("flashcard", "meaning", "audio", "spelling"):
        res = client.get(f"/vocabulary/review?mode={mode}")
        assert res.status_code == 200


def test_review_submit_ratings(client):
    login_student(client)

    with client.application.app_context():
        v1, _ = ensure_sample_vocabularies()
        word_id = v1.id

    # Test Good (+1 Level)
    res = client.post(
        "/vocabulary/review/submit",
        data={"word_id": word_id, "rating": "good", "mode": "flashcard", "index": 0, "total_words": 2},
        follow_redirects=True,
    )
    assert res.status_code == 200

    with client.application.app_context():
        prog = VocabularyProgress.query.filter_by(vocabulary_id=word_id).first()
        assert prog is not None
        assert prog.srs_level == 2
        assert prog.review_count == 1

    # Test Easy (+2 Level) -> Should become level 4
    res = client.post(
        "/vocabulary/review/submit",
        data={"word_id": word_id, "rating": "easy", "mode": "flashcard", "index": 0, "total_words": 2},
        follow_redirects=True,
    )
    assert res.status_code == 200

    with client.application.app_context():
        prog = VocabularyProgress.query.filter_by(vocabulary_id=word_id).first()
        assert prog.srs_level == 4
        assert prog.review_count == 2


def test_review_summary_render(client):
    login_student(client)

    res = client.get("/vocabulary/review/summary")
    assert res.status_code == 200
    assert "Hoàn thành phiên ôn tập SRS!".encode("utf-8") in res.data
    assert "Tổng số từ đã ôn".encode("utf-8") in res.data
