"""Test suite for Data Quality & Profiling (Module 14.3)"""
import pytest
from app.backend.learning.models import Vocabulary, Question, Lesson
from app.extensions import db
from app.backend.admin.data_quality_service import (
    get_data_profiling,
    evaluate_vocab_quality,
    scan_data_quality_issues,
    autofill_vocab_data,
    batch_autofill_substandard_vocab,
)
from tests.conftest import login


def test_data_profiling_service_and_api(client):
    login(client, "admin@test.com", "admin123")

    with client.application.app_context():
        v1 = Vocabulary(word="perseverance", pronunciation="/ˌpɜː.sɪˈvɪə.rəns/", part_of_speech="noun",
                        meaning_vi="sự kiên trì", example_en="Perseverance leads to success.",
                        example_vi="Sự kiên trì mang lại thành công.", topic="Mindset", level="B2")
        q1 = Question(question_text="Choose the correct word:", option_a="Opt A", option_b="Opt B",
                      option_c="Opt C", option_d="Opt D", correct_option="A",
                      explanation="Explanation text here.", level="B2", topic="Mindset")
        l1 = Lesson(title="Mastering Resilience", level="B2", skill="Reading",
                    short_description="Learn how to develop perseverance.",
                    content="Content of the resilience lesson goes here with full explanations.",
                    examples="Example 1: Never give up.")
        db.session.add_all([v1, q1, l1])
        db.session.commit()

        profiling = get_data_profiling()
        assert profiling["vocabulary"]["total"] >= 1
        assert profiling["vocabulary"]["avg_word_length"] > 0
        assert "B2" in profiling["vocabulary"]["by_level"]
        assert profiling["questions"]["total"] >= 1
        assert profiling["lessons"]["total"] >= 1

    # API Endpoint check
    res = client.get("/admin/data-quality/api/profile")
    assert res.status_code == 200
    data = res.get_json()
    assert "vocabulary" in data
    assert "questions" in data
    assert "lessons" in data


def test_vocab_quality_metrics_evaluation(client):
    with client.application.app_context():
        # Complete vocab -> Grade A
        v_good = Vocabulary(word="comprehensive", pronunciation="/ˌkɒm.prɪˈhen.sɪv/", part_of_speech="adjective",
                            meaning_vi="toàn diện, bao hàm", example_en="A comprehensive study.",
                            example_vi="Một nghiên cứu toàn diện.", collocations="comprehensive guide",
                            synonyms="complete, thorough", topic="Academic", level="C1", image_url="https://example.com/img.jpg")
        eval_good = evaluate_vocab_quality(v_good)
        assert eval_good["score"] >= 85
        assert eval_good["grade"] == "A"
        assert eval_good["is_standard"] is True
        assert len(eval_good["missing"]) == 0

        # Substandard vocab -> Grade C or D
        v_bad = Vocabulary(word="testword", pronunciation="", part_of_speech="noun",
                           meaning_vi="", example_en="", example_vi="", topic="General", level="A1")
        eval_bad = evaluate_vocab_quality(v_bad)
        assert eval_bad["score"] < 70
        assert eval_bad["is_standard"] is False
        assert len(eval_bad["missing"]) > 0


def test_data_quality_monitoring_and_scanner(client):
    login(client, "admin@test.com", "admin123")

    with client.application.app_context():
        # Defective Question: duplicate options & invalid correct_option
        q_defect = Question(question_text="Defective question", option_a="Duplicate", option_b="Duplicate",
                            option_c="Option C", option_d="Option D", correct_option="Z",
                            explanation="", level="A1", topic="General")
        # Defective Lesson: content too short
        l_defect = Lesson(title="Short lesson", level="A1", skill="Grammar",
                          short_description="Short", content="Too short", examples="")
        db.session.add_all([q_defect, l_defect])
        db.session.commit()

        scan = scan_data_quality_issues()
        assert scan["summary"]["total_records"] > 0
        assert scan["summary"]["counts"]["question_issues"] >= 1
        assert scan["summary"]["counts"]["lesson_issues"] >= 1

    # Test Scan API
    res = client.post("/admin/data-quality/api/scan")
    assert res.status_code == 200
    data = res.get_json()
    assert data["ok"] is True
    assert "results" in data


def test_user_cannot_access_data_quality(client):
    login(client, "student@test.com", "user123")
    res_forbidden = client.get("/admin/data-quality")
    assert res_forbidden.status_code == 403


def test_admin_data_quality_dashboard_and_report_views(client):
    login(client, "admin@test.com", "admin123")
    res_dash = client.get("/admin/data-quality")
    assert res_dash.status_code == 200
    html = res_dash.data.decode("utf-8")
    assert "Chất lượng &amp; Phân tích Dữ liệu" in html or "Chất lượng & Phân tích Dữ liệu" in html
    assert "Độ Sức Khỏe Dữ liệu" in html

    # JSON report
    res_json = client.get("/admin/data-quality/report?format=json")
    assert res_json.status_code == 200
    data = res_json.get_json()
    assert "profiling" in data
    assert "scan_results" in data


def test_data_quality_improvement_autofill(client):
    login(client, "admin@test.com", "admin123")

    with client.application.app_context():
        v_missing = Vocabulary(word="diligent", pronunciation="", part_of_speech="adjective",
                               meaning_vi="chăm chỉ", example_en="", example_vi="", topic="Work", level="B1")
        db.session.add(v_missing)
        db.session.commit()
        v_id = v_missing.id

    # Single Autofill API
    res_single = client.post(f"/admin/data-quality/api/autofill/{v_id}")
    assert res_single.status_code == 200
    data_single = res_single.get_json()
    assert data_single["ok"] is True
    assert len(data_single["result"]["enriched_fields"]) > 0

    with client.application.app_context():
        updated_v = db.session.get(Vocabulary, v_id)
        assert updated_v.pronunciation.startswith("/")
        assert len(updated_v.example_en) > 5

    # Batch Autofill API
    res_batch = client.post("/admin/data-quality/api/batch-autofill", json={"limit": 5})
    assert res_batch.status_code == 200
    data_batch = res_batch.get_json()
    assert data_batch["ok"] is True
    assert "improved_count" in data_batch["result"]
