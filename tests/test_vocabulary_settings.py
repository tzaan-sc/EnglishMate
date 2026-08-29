from app.extensions import db
from app.modules.auth.models import User
from app.modules.learning.models import Vocabulary, VocabularyProgress


def login_student(client):
    return client.post("/auth/login", data={"email": "student@test.com", "password": "user123"}, follow_redirects=True)


def ensure_sample_vocabulary():
    v = Vocabulary.query.first()
    if not v:
        v = Vocabulary(
            word="diligent",
            pronunciation="/ˈdɪl.ə.dʒənt/",
            part_of_speech="adjective",
            meaning_vi="siêng năng, cần cù",
            example_en="She is a diligent student.",
            example_vi="Cô ấy là một học sinh cần cù.",
            topic="Personality",
            level="B2",
        )
        db.session.add(v)
        db.session.commit()
    return v


def test_vocabulary_settings_render(client):
    login_student(client)

    res = client.get("/vocabulary/settings")
    assert res.status_code == 200
    assert "Cài Đặt Từ Vựng Cá Nhân".encode("utf-8") in res.data
    assert "Giọng Mỹ (en-US)".encode("utf-8") in res.data


def test_save_vocabulary_settings(client):
    login_student(client)

    res = client.post(
        "/vocabulary/settings",
        data={
            "daily_vocab_goal": 30,
            "vocab_review_priority": "srs_level_asc",
            "vocab_auto_play_audio": "on",
            "vocab_accent": "en-GB",
            "vocab_display_mode": "flashcard",
            "vocab_review_time": "morning",
            "vocab_srs_algorithm": "aggressive",
            "vocab_notify_review_due": "on",
        },
        follow_redirects=True,
    )
    assert res.status_code == 200
    assert "Đã cập nhật các cài đặt".encode("utf-8") in res.data

    with client.application.app_context():
        user = User.query.filter_by(email="student@test.com").first()
        assert user is not None
        assert user.daily_vocab_goal == 30
        assert user.vocab_accent == "en-GB"
        assert user.vocab_srs_algorithm == "aggressive"
        assert user.vocab_review_time == "morning"


def test_srs_algorithm_intervals_impact(client):
    login_student(client)

    with client.application.app_context():
        v = ensure_sample_vocabulary()
        word_id = v.id

    # Set aggressive algorithm
    client.post(
        "/vocabulary/settings",
        data={"vocab_srs_algorithm": "aggressive"},
        follow_redirects=True,
    )

    # Submit review
    res = client.post(
        "/vocabulary/review/submit",
        data={"word_id": word_id, "rating": "good", "mode": "flashcard", "index": 0, "total_words": 1},
        follow_redirects=True,
    )
    assert res.status_code == 200

    with client.application.app_context():
        prog = VocabularyProgress.query.filter_by(vocabulary_id=word_id).first()
        assert prog is not None
        assert prog.srs_level == 2
