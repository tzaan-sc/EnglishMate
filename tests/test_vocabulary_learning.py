from app.extensions import db
from app.modules.learning.models import Vocabulary, VocabularyProgress, WordReport


def login_student(client):
    return client.post("/auth/login", data={"email": "student@test.com", "password": "user123"}, follow_redirects=True)


def ensure_sample_vocabulary():
    v = Vocabulary.query.first()
    if not v:
        v = Vocabulary(
            word="resilient",
            pronunciation="/rɪˈzɪl.jənt/",
            part_of_speech="adjective",
            meaning_vi="kiên cường, có khả năng phục hồi nhanh",
            example_en="She is a resilient person.",
            example_vi="Cô ấy là một người kiên cường.",
            topic="Personality",
            level="B2",
            collocations="resilient economy, highly resilient",
            synonyms="tough, adaptable",
            antonyms="fragile, weak",
        )
        db.session.add(v)
        db.session.commit()
    return v


def test_study_vocabulary_render(client):
    login_student(client)

    with client.application.app_context():
        ensure_sample_vocabulary()

    res = client.get("/vocabulary/study")
    assert res.status_code == 200
    assert "Học Từ Vựng Tương Tác".encode("utf-8") in res.data
    assert "Tự động đọc".encode("utf-8") in res.data
    assert "✓ Đã học từ này".encode("utf-8") in res.data


def test_favorite_word_toggle(client):
    login_student(client)

    with client.application.app_context():
        word = ensure_sample_vocabulary()
        word_id = word.id

    res = client.post(f"/vocabulary/{word_id}/favorite", follow_redirects=True)
    assert res.status_code == 200
    assert "Đã thêm".encode("utf-8") in res.data or "vào mục yêu thích".encode("utf-8") in res.data


def test_skip_word(client):
    login_student(client)

    with client.application.app_context():
        word = ensure_sample_vocabulary()
        word_id = word.id

    res = client.post(f"/vocabulary/{word_id}/skip", follow_redirects=True)
    assert res.status_code == 200
    assert "Đã bỏ qua".encode("utf-8") in res.data


def test_report_word(client):
    login_student(client)

    with client.application.app_context():
        word = ensure_sample_vocabulary()
        word_id = word.id

    res = client.post(
        f"/vocabulary/{word_id}/report",
        data={"reason": "Phiên âm IPA cần làm rõ hơn"},
        follow_redirects=True,
    )
    assert res.status_code == 200
    assert "Cảm ơn bạn đã báo cáo sai sót".encode("utf-8") in res.data

    with client.application.app_context():
        report = WordReport.query.filter_by(vocabulary_id=word_id).first()
        assert report is not None
        assert "IPA" in report.reason
