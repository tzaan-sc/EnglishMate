from app.extensions import db
from app.backend.auth.models import User
from app.backend.learning.models import GrammarRule, GrammarRuleBookmark
from tests.conftest import login


def ensure_sample_grammar_rule():
    r = GrammarRule.query.filter_by(title="Quy tắc Thêm S/ES vào Động Từ & Danh Từ").first()
    if not r:
        r = GrammarRule(
            title="Quy tắc Thêm S/ES vào Động Từ & Danh Từ",
            category="Verbs & Nouns",
            summary="Các quy tắc phát âm và chính tả khi thêm s/es.",
            explanation="Quy tắc thêm es khi từ tận cùng s, sh, ch, x, z, o.",
            examples="watch -> watches",
            exceptions="photo -> photos",
            common_errors="playes -> plays",
            quick_table_html="<table><tr><td>-s</td><td>+es</td></tr></table>"
        )
        db.session.add(r)
        db.session.commit()
    return r


def test_grammar_reference_index_render(client):
    login(client)

    res = client.get("/grammar/reference")
    assert res.status_code == 200
    assert "Tài Liệu Tham Khảo Ngữ Pháp".encode("utf-8") in res.data
    assert "THƯ VIỆN TRA CỨU QUY TẮC CHUẨN".encode("utf-8") in res.data


def test_grammar_reference_search_and_filters(client):
    login(client)

    with client.application.app_context():
        ensure_sample_grammar_rule()

    res_q = client.get("/grammar/reference?q=Thêm+S/ES")
    assert res_q.status_code == 200
    assert "Quy tắc Thêm S/ES".encode("utf-8") in res_q.data

    res_cat = client.get("/grammar/reference?category=Verbs+%26+Nouns")
    assert res_cat.status_code == 200
    assert "Quy tắc Thêm S/ES".encode("utf-8") in res_cat.data


def test_grammar_rule_detail_render(client):
    login(client)

    with client.application.app_context():
        r = ensure_sample_grammar_rule()
        rule_id = r.id

    res = client.get(f"/grammar/reference/{rule_id}")
    assert res.status_code == 200
    assert "1. Giải thích Quy tắc Chi tiết".encode("utf-8") in res.data
    assert "2. Các Ví dụ Minh họa".encode("utf-8") in res.data
    assert "3. Bảng Tham Khảo Nhanh".encode("utf-8") in res.data
    assert "4. Trường hợp Ngoại lệ".encode("utf-8") in res.data
    assert "5. Các Lỗi thường gặp".encode("utf-8") in res.data


def test_bookmark_grammar_rule(client):
    login(client)

    with client.application.app_context():
        r = ensure_sample_grammar_rule()
        rule_id = r.id

    res_bm = client.post(f"/grammar/reference/{rule_id}/bookmark", follow_redirects=True)
    assert res_bm.status_code == 200
    assert "Đã bookmark quy tắc".encode("utf-8") in res_bm.data

    with client.application.app_context():
        user = User.query.filter_by(email="student@test.com").first()
        bm = GrammarRuleBookmark.query.filter_by(user_id=user.id, rule_id=rule_id).first()
        assert bm is not None


def test_grammar_rule_print_view(client):
    login(client)

    with client.application.app_context():
        r = ensure_sample_grammar_rule()
        rule_id = r.id

    res_p = client.get(f"/grammar/reference/{rule_id}/print")
    assert res_p.status_code == 200
    assert "Chế độ Xem In Ấn".encode("utf-8") in res_p.data
    assert "GIẢI THÍCH QUY TẮC".encode("utf-8") in res_p.data


def test_grammar_rule_export_pdf_and_docx(client):
    login(client)

    with client.application.app_context():
        r = ensure_sample_grammar_rule()
        rule_id = r.id

    # Test PDF export
    res_pdf = client.get(f"/grammar/reference/{rule_id}/export-pdf")
    assert res_pdf.status_code == 200
    assert res_pdf.mimetype == "application/pdf"
    assert res_pdf.data.startswith(b"%PDF")
    assert "attachment; filename=" in res_pdf.headers.get("Content-Disposition", "")

    # Test DOCX export
    res_docx = client.get(f"/grammar/reference/{rule_id}/export-docx")
    assert res_docx.status_code == 200
    assert res_docx.mimetype == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    assert len(res_docx.data) > 100
    assert "attachment; filename=" in res_docx.headers.get("Content-Disposition", "")


def test_grammar_handbook_export_pdf_and_docx(client):
    login(client)

    with client.application.app_context():
        ensure_sample_grammar_rule()

    # Test handbook PDF export
    res_pdf = client.get("/grammar/reference/export-pdf")
    assert res_pdf.status_code == 200
    assert res_pdf.mimetype == "application/pdf"
    assert res_pdf.data.startswith(b"%PDF")
    assert "attachment; filename=EnglishMate_So_Tay_Ngu_Phap.pdf" in res_pdf.headers.get("Content-Disposition", "")

    # Test handbook PDF export with category
    res_pdf_cat = client.get("/grammar/reference/export-pdf?category=Verbs+%26+Nouns")
    assert res_pdf_cat.status_code == 200
    assert res_pdf_cat.mimetype == "application/pdf"
    assert res_pdf_cat.data.startswith(b"%PDF")

    # Test handbook DOCX export
    res_docx = client.get("/grammar/reference/export-docx")
    assert res_docx.status_code == 200
    assert res_docx.mimetype == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    assert len(res_docx.data) > 100
    assert "attachment; filename=EnglishMate_So_Tay_Ngu_Phap.docx" in res_docx.headers.get("Content-Disposition", "")

