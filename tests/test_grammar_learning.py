from app.extensions import db
from app.modules.auth.models import User
from app.modules.learning.models import GrammarTopic, GrammarProgress
from tests.conftest import login


def ensure_sample_grammar_topic():
    gt = GrammarTopic.query.filter_by(title="Thì Quá Khứ Đơn (Past Simple Tense)").first()
    if not gt:
        gt = GrammarTopic(
            title="Thì Quá Khứ Đơn (Past Simple Tense)",
            category="Các thì (Tenses)",
            level="A2",
            difficulty="Medium",
            summary="Cách chia động từ quá khứ có quy tắc và bất quy tắc.",
            rule_explanation="Cấu trúc: S + V2/ed. Phủ định: S + did not + V_inf.",
            examples_json="We visited Hanoi last year.|Chúng tôi đã thăm Hà Nội năm ngoái.",
            common_mistakes="Quên chia động từ.",
            tips_tricks="Học thuộc bảng động từ bất quy tắc.",
        )
        db.session.add(gt)
        db.session.commit()
    return gt


def test_grammar_overview_render(client):
    login(client)

    res = client.get("/grammar")
    assert res.status_code == 200
    assert "Chủ đề Ngữ pháp Tiếng Anh".encode("utf-8") in res.data
    assert "Tổng số chủ đề".encode("utf-8") in res.data


def test_grammar_search_and_filters(client):
    login(client)

    with client.application.app_context():
        ensure_sample_grammar_topic()

    res_q = client.get("/grammar?q=Quá+Khứ")
    assert res_q.status_code == 200
    assert "Thì Quá Khứ Đơn".encode("utf-8") in res_q.data

    res_lvl = client.get("/grammar?level=A2")
    assert res_lvl.status_code == 200
    assert "Thì Quá Khứ Đơn".encode("utf-8") in res_lvl.data


def test_grammar_detail_render(client):
    login(client)

    with client.application.app_context():
        gt = ensure_sample_grammar_topic()
        topic_id = gt.id

    res = client.get(f"/grammar/{topic_id}")
    assert res.status_code == 200
    assert "1. Quy tắc & Công thức Ngữ pháp".encode("utf-8") in res.data
    assert "2. Ví dụ minh họa & Giải thích chi tiết".encode("utf-8") in res.data
    assert "3. Các Lỗi thường gặp".encode("utf-8") in res.data
    assert "4. Mẹo ghi nhớ & Thủ thuật".encode("utf-8") in res.data


def test_grammar_complete_and_favorite(client):
    login(client)

    with client.application.app_context():
        gt = ensure_sample_grammar_topic()
        topic_id = gt.id

    # Test Complete POST
    res_comp = client.post(f"/grammar/{topic_id}/complete", follow_redirects=True)
    assert res_comp.status_code == 200
    assert "Đã đánh dấu hoàn thành".encode("utf-8") in res_comp.data

    with client.application.app_context():
        user = User.query.filter_by(email="student@test.com").first()
        prog = GrammarProgress.query.filter_by(user_id=user.id, topic_id=topic_id).first()
        assert prog is not None
        assert prog.is_completed is True

    # Test Favorite POST
    res_fav = client.post(f"/grammar/{topic_id}/favorite", follow_redirects=True)
    assert res_fav.status_code == 200
    assert "Đã thêm vào chủ đề ngữ pháp yêu thích".encode("utf-8") in res_fav.data

    with client.application.app_context():
        prog = GrammarProgress.query.filter_by(user_id=user.id, topic_id=topic_id).first()
        assert prog.is_favorite is True
