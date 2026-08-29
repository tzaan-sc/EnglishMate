from app.extensions import db
from app.modules.learning.models import Vocabulary, VocabularyProgress


def login_student(client):
    return client.post("/auth/login", data={"email": "student@test.com", "password": "user123"}, follow_redirects=True)


def ensure_sample_vocabularies():
    v1 = Vocabulary.query.filter_by(word="ambitious").first()
    if not v1:
        v1 = Vocabulary(
            word="ambitious",
            pronunciation="/æmˈbɪʃ.əs/",
            part_of_speech="adjective",
            meaning_vi="có nhiều hoài bão, tham vọng",
            example_en="He is an ambitious young lawyer.",
            example_vi="Anh ấy là một luật sư trẻ giàu tham vọng.",
            topic="Personality",
            level="B2",
        )
        db.session.add(v1)

    v2 = Vocabulary.query.filter_by(word="benevolent").first()
    if not v2:
        v2 = Vocabulary(
            word="benevolent",
            pronunciation="/bəˈnev.əl.ənt/",
            part_of_speech="adjective",
            meaning_vi="nhân từ, nhân ái",
            example_en="He was a benevolent employer.",
            example_vi="Ông ấy là một người chủ nhân từ.",
            topic="Personality",
            level="C1",
        )
        db.session.add(v2)

    db.session.commit()
    return v1, v2


def test_manage_vocabulary_render(client):
    login_student(client)

    with client.application.app_context():
        ensure_sample_vocabularies()

    res = client.get("/vocabulary/manage")
    assert res.status_code == 200
    assert "Quản Lý & Tra Cứu Từ Vựng".encode("utf-8") in res.data
    assert "Tất cả Level".encode("utf-8") in res.data


def test_search_english_and_vietnamese(client):
    login_student(client)

    with client.application.app_context():
        ensure_sample_vocabularies()

    # Search by English
    res_en = client.get("/vocabulary/manage?q=ambitious")
    assert res_en.status_code == 200
    assert "ambitious".encode("utf-8") in res_en.data

    # Search by Vietnamese
    res_vi = client.get("/vocabulary/manage?q=nhân%20từ")
    assert res_vi.status_code == 200
    assert "benevolent".encode("utf-8") in res_vi.data


def test_filters_and_sorting(client):
    login_student(client)

    with client.application.app_context():
        ensure_sample_vocabularies()

    # Filter by level B2
    res_lvl = client.get("/vocabulary/manage?level=B2")
    assert res_lvl.status_code == 200
    assert "ambitious".encode("utf-8") in res_lvl.data

    # Sort alpha_desc
    res_sort = client.get("/vocabulary/manage?sort=alpha_desc")
    assert res_sort.status_code == 200


def test_update_notes_and_custom_example(client):
    login_student(client)

    with client.application.app_context():
        v1, _ = ensure_sample_vocabularies()
        vocab_id = v1.id

    res = client.post(
        f"/vocabulary/{vocab_id}/notes",
        data={
            "personal_notes": "Từ vựng trọng tâm bài thi TOEIC 800+",
            "custom_example": "Ambition is key to success."
        },
        follow_redirects=True,
    )
    assert res.status_code == 200
    assert "Đã cập nhật ghi chú cá nhân".encode("utf-8") in res.data

    with client.application.app_context():
        prog = VocabularyProgress.query.filter_by(vocabulary_id=vocab_id).first()
        assert prog is not None
        assert "TOEIC 800+" in prog.personal_notes
        assert "Ambition" in prog.custom_example


def test_reset_and_delete_word_progress(client):
    login_student(client)

    with client.application.app_context():
        v1, _ = ensure_sample_vocabularies()
        vocab_id = v1.id

    # Test Reset Progress
    res_reset = client.post(f"/vocabulary/{vocab_id}/reset-progress", follow_redirects=True)
    assert res_reset.status_code == 200
    assert "Đã đặt lại tiến độ học".encode("utf-8") in res_reset.data

    # Test Delete Progress
    res_delete = client.post(f"/vocabulary/{vocab_id}/delete-progress", follow_redirects=True)
    assert res_delete.status_code == 200
    assert "Đã xóa".encode("utf-8") in res_delete.data


def test_bulk_operations(client):
    login_student(client)

    with client.application.app_context():
        v1, v2 = ensure_sample_vocabularies()
        v1_id, v2_id = v1.id, v2.id

    res = client.post(
        "/vocabulary/bulk-action",
        data={
            "bulk_action": "learn",
            "vocab_ids": [str(v1_id), str(v2_id)]
        },
        follow_redirects=True,
    )
    assert res.status_code == 200
    assert "Đã thực hiện thao tác hàng loạt".encode("utf-8") in res.data
