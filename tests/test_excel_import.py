import io
import pytest
from openpyxl import Workbook
from app.extensions import db
from app.modules.learning.models import Vocabulary, GrammarTopic, Lesson, Question
from app.modules.exams.models import Exam, ExamQuestion
from tests.conftest import login


def create_mock_excel(headers, rows):
    wb = Workbook()
    ws = wb.active
    ws.append(headers)
    for r in rows:
        ws.append(r)
    stream = io.BytesIO()
    wb.save(stream)
    stream.seek(0)
    return stream


def test_import_hub_render(client):
    login(client, email="admin@test.com", password="admin123")
    res = client.get("/admin/import")
    assert res.status_code == 200
    assert "Trung tâm Import Dữ liệu Học tập".encode("utf-8") in res.data
    assert ".xlsx".encode("utf-8") in res.data
    assert ".json".encode("utf-8") in res.data


def test_download_templates(client):
    login(client, email="admin@test.com", password="admin123")
    for ctype in ["vocabulary", "grammar", "lessons", "questions", "exams"]:
        res = client.get(f"/admin/import/template/{ctype}")
        assert res.status_code == 200
        assert res.headers["Content-Type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def test_validate_vocabulary_excel_valid(client):
    login(client, email="admin@test.com", password="admin123")
    headers = [
        "word", "pronunciation", "part_of_speech", "meaning_vi",
        "example_en", "example_vi", "topic", "level", "image_url", "collocations", "synonyms", "antonyms"
    ]
    rows = [
        ["persevere", "/ˌpɜː.sɪˈvɪər/", "verb", "kiên trì, bền bỉ", "She persevered with her violin lessons.", "Cô ấy đã kiên trì với các buổi học violin.", "Daily Life", "B2", "", "", "persist", "give up"]
    ]
    excel_file = create_mock_excel(headers, rows)

    res = client.post(
        "/admin/import/validate",
        data={"content_type": "vocabulary", "file": (excel_file, "vocab.xlsx")},
        content_type="multipart/form-data"
    )
    assert res.status_code == 200
    json_data = res.get_json()
    assert json_data["success"] is True
    assert json_data["valid_count"] == 1
    assert json_data["error_count"] == 0
    assert json_data["valid_records"][0]["data"]["word"] == "persevere"


def test_validate_grammar_excel_with_errors(client):
    login(client, email="admin@test.com", password="admin123")
    headers = [
        "title", "category", "level", "difficulty", "summary",
        "rule_explanation", "examples_json"
    ]
    # Row 1 has invalid level "Z9", Row 2 has empty rule_explanation
    rows = [
        ["Chủ đề 1", "Tenses", "Z9", "Easy", "Tóm tắt", "Công thức", "Ex|Vd"],
        ["Chủ đề 2", "Tenses", "B1", "Easy", "Tóm tắt", "", "Ex|Vd"]
    ]
    excel_file = create_mock_excel(headers, rows)

    res = client.post(
        "/admin/import/validate",
        data={"content_type": "grammar", "file": (excel_file, "grammar.xlsx")},
        content_type="multipart/form-data"
    )
    assert res.status_code == 200
    json_data = res.get_json()
    assert json_data["success"] is True
    assert json_data["valid_count"] == 0
    assert json_data["error_count"] == 2
    assert "không hợp lệ" in json_data["error_records"][0]["errors"][0]


def test_commit_vocabulary_import(client):
    login(client, email="admin@test.com", password="admin123")
    valid_records = [
        {
            "row_number": 2,
            "data": {
                "word": "catalyst",
                "pronunciation": "/ˈkæt.əl.ɪst/",
                "part_of_speech": "noun",
                "meaning_vi": "chất xúc tác",
                "example_en": "The event served as a catalyst for reform.",
                "example_vi": "Sự kiện đóng vai trò như chất xúc tác cho cải cách.",
                "topic": "Science",
                "level": "C1",
                "image_url": "",
                "collocations": "serve as a catalyst",
                "synonyms": "trigger",
                "antonyms": ""
            }
        }
    ]

    res = client.post(
        "/admin/import/commit",
        json={"content_type": "vocabulary", "valid_records": valid_records, "mode": "insert_or_update"}
    )
    assert res.status_code == 200
    json_data = res.get_json()
    assert json_data["success"] is True
    assert json_data["inserted_count"] == 1

    with client.application.app_context():
        word = Vocabulary.query.filter_by(word="catalyst").first()
        assert word is not None
        assert word.meaning_vi == "chất xúc tác"
        assert word.level == "C1"


def test_commit_grammar_import(client):
    login(client, email="admin@test.com", password="admin123")
    valid_records = [
        {
            "row_number": 2,
            "data": {
                "title": "Mệnh Đề Danh Từ (Noun Clauses)",
                "category": "Mệnh đề (Clauses)",
                "level": "B2",
                "difficulty": "Hard",
                "summary": "Mệnh đề đóng vai trò như một danh từ trong câu.",
                "rule_explanation": "Bắt đầu bằng That, What, Where, When, Why, How, Whether/If...",
                "examples_json": "What he said surprised everyone.|Những gì anh ấy nói làm mọi người ngạc nhiên.",
                "common_mistakes": "Nhầm lẫn trật tự từ trong mệnh đề danh từ.",
                "tips_tricks": "Luôn dùng trật tự khẳng định S + V sau từ để hỏi."
            }
        }
    ]

    res = client.post(
        "/admin/import/commit",
        json={"content_type": "grammar", "valid_records": valid_records, "mode": "insert_or_update"}
    )
    assert res.status_code == 200
    json_data = res.get_json()
    assert json_data["success"] is True

    with client.application.app_context():
        topic = GrammarTopic.query.filter_by(title="Mệnh Đề Danh Từ (Noun Clauses)").first()
        assert topic is not None
        assert topic.category == "Mệnh đề (Clauses)"
        assert topic.difficulty == "Hard"


def test_commit_lessons_import(client):
    login(client, email="admin@test.com", password="admin123")
    valid_records = [
        {
            "row_number": 2,
            "data": {
                "title": "IELTS Academic Writing Task 1 Overview",
                "level": "B2",
                "skill": "Writing",
                "short_description": "Hướng dẫn cách viết bài mô tả biểu đồ Task 1.",
                "content": "### Introduction\nParaphrase the prompt using synonyms.",
                "examples": "The chart illustrates the consumption of...|Biểu đồ minh họa mức tiêu thụ của...",
                "thumbnail_url": ""
            }
        }
    ]

    res = client.post(
        "/admin/import/commit",
        json={"content_type": "lessons", "valid_records": valid_records, "mode": "insert_or_update"}
    )
    assert res.status_code == 200

    with client.application.app_context():
        lesson = Lesson.query.filter_by(title="IELTS Academic Writing Task 1 Overview").first()
        assert lesson is not None
        assert lesson.skill == "Writing"


def test_commit_questions_import(client):
    login(client, email="admin@test.com", password="admin123")
    valid_records = [
        {
            "row_number": 2,
            "data": {
                "question_text": "Hardly had I arrived _______ it started raining.",
                "option_a": "than",
                "option_b": "when",
                "option_c": "then",
                "option_d": "after",
                "correct_option": "B",
                "explanation": "Cấu trúc đảo ngữ: Hardly / Scarcely + had + S + V3/ed + WHEN + S + V2/ed.",
                "topic": "Inversion",
                "level": "C1"
            }
        }
    ]

    res = client.post(
        "/admin/import/commit",
        json={"content_type": "questions", "valid_records": valid_records, "mode": "insert_or_update"}
    )
    assert res.status_code == 200

    with client.application.app_context():
        q = Question.query.filter_by(question_text="Hardly had I arrived _______ it started raining.").first()
        assert q is not None
        assert q.correct_option == "B"


def test_download_json_templates(client):
    login(client, email="admin@test.com", password="admin123")
    for ctype in ["vocabulary", "grammar", "lessons", "questions", "exams"]:
        res = client.get(f"/admin/import/template/{ctype}?format=json")
        assert res.status_code == 200
        assert res.headers["Content-Type"] == "application/json"


def test_validate_vocabulary_json_valid(client):
    import json
    login(client, email="admin@test.com", password="admin123")
    json_data = [
        {
            "word": "resilience",
            "pronunciation": "/rɪˈzɪl.jəns/",
            "part_of_speech": "noun",
            "meaning_vi": "sự kiên cường, khả năng phục hồi",
            "example_en": "Courage and resilience helped her overcome difficulties.",
            "example_vi": "Lòng can đảm và sự kiên cường đã giúp cô ấy vượt qua khó khăn.",
            "topic": "Psychology",
            "level": "C1"
        }
    ]
    json_bytes = io.BytesIO(json.dumps(json_data).encode("utf-8"))

    res = client.post(
        "/admin/import/validate",
        data={"content_type": "vocabulary", "file": (json_bytes, "vocab.json")},
        content_type="multipart/form-data"
    )
    assert res.status_code == 200
    res_json = res.get_json()
    assert res_json["success"] is True
    assert res_json["valid_count"] == 1
    assert res_json["valid_records"][0]["data"]["word"] == "resilience"


def test_download_csv_templates(client):
    login(client, email="admin@test.com", password="admin123")
    for ctype in ["vocabulary", "grammar", "lessons", "questions", "exams"]:
        res = client.get(f"/admin/import/template/{ctype}?format=csv")
        assert res.status_code == 200
        assert "csv" in res.headers["Content-Type"].lower() or "text" in res.headers["Content-Type"].lower()


def test_validate_and_commit_csv(client):
    login(client, email="admin@test.com", password="admin123")
    csv_content = (
        "word,pronunciation,part_of_speech,meaning_vi,example_en,example_vi,topic,level\n"
        "benchmark,/ˈbentʃ.mɑːk/,noun,tiêu chuẩn so sánh,This serves as a benchmark for quality.,Đây là tiêu chuẩn so sánh chất lượng.,Business,B2\n"
    )
    csv_stream = io.BytesIO(csv_content.encode("utf-8-sig"))

    res = client.post(
        "/admin/import/validate",
        data={"content_type": "vocabulary", "file": (csv_stream, "test_vocab.csv")},
        content_type="multipart/form-data"
    )
    assert res.status_code == 200
    res_json = res.get_json()
    assert res_json["success"] is True
    assert res_json["valid_count"] == 1
    assert res_json["valid_records"][0]["data"]["word"] == "benchmark"

    # Commit the validated record
    commit_res = client.post(
        "/admin/import/commit",
        json={"content_type": "vocabulary", "valid_records": res_json["valid_records"], "mode": "insert_or_update"}
    )
    assert commit_res.status_code == 200
    commit_json = commit_res.get_json()
    assert commit_json["success"] is True
    assert commit_json["inserted_count"] == 1

    with client.application.app_context():
        word = Vocabulary.query.filter_by(word="benchmark").first()
        assert word is not None
        assert word.meaning_vi == "tiêu chuẩn so sánh"


def test_commit_lessons_with_skill_data(client):
    login(client, email="admin@test.com", password="admin123")
    valid_records = [
        {
            "row_number": 2,
            "data": {
                "title": "Listening to Workplace Negotiations",
                "level": "C1",
                "skill": "Listening",
                "short_description": "Advanced business audio practice.",
                "content": "Listen carefully to the exchange between managers.",
                "examples": "We could compromise on the budget.|Chúng ta có thể thỏa hiệp về ngân sách.",
                "audio_url": "https://example.com/negotiation.mp3",
                "accent": "US",
                "audio_duration": "04:15",
                "listening_transcript": "Speaker 1: What is your bottom line? Speaker 2: We need 10% discount.",
                "min_words": "120",
                "max_words": "200"
            }
        }
    ]

    res = client.post(
        "/admin/import/commit",
        json={"content_type": "lessons", "valid_records": valid_records, "mode": "insert_or_update"}
    )
    assert res.status_code == 200
    with client.application.app_context():
        lesson = Lesson.query.filter_by(title="Listening to Workplace Negotiations").first()
        assert lesson is not None
        assert lesson.skill_data is not None
        assert lesson.skill_data.get("audio_url") == "https://example.com/negotiation.mp3"
        assert lesson.skill_data.get("accent") == "US"
        assert lesson.skill_data.get("min_words") == 120


def test_commit_exams_with_toeic_part_distribution(client):
    login(client, email="admin@test.com", password="admin123")
    valid_records = [
        {
            "row_number": 2,
            "data": {
                "category": "TOEIC",
                "title": "TOEIC Full Practice Set 2026 Batch",
                "duration_minutes": "75",
                "difficulty": "Medium",
                "skill": "READING",
                "part": "Part 5",
                "question_text": "Ms. Davis _______ submitted her quarterly sales report.",
                "option_a": "promptly",
                "option_b": "prompt",
                "option_c": "promptness",
                "option_d": "prompting",
                "correct_answer": "A",
                "explanation": "Adverb modifying the verb submitted."
            }
        },
        {
            "row_number": 3,
            "data": {
                "category": "TOEIC",
                "title": "TOEIC Full Practice Set 2026 Batch",
                "duration_minutes": "75",
                "difficulty": "Medium",
                "skill": "READING",
                "part": "Part 6",
                "question_text": "Please review the memo below...",
                "option_a": "however",
                "option_b": "therefore",
                "option_c": "although",
                "option_d": "furthermore",
                "correct_answer": "B",
                "explanation": "Logical connector for result."
            }
        }
    ]

    res = client.post(
        "/admin/import/commit",
        json={"content_type": "exams", "valid_records": valid_records, "mode": "insert_or_update"}
    )
    assert res.status_code == 200
    with client.application.app_context():
        exam = Exam.query.filter_by(title="TOEIC Full Practice Set 2026 Batch").first()
        assert exam is not None
        assert exam.duration_minutes == 75
        assert exam.part_distribution is not None
        assert exam.part_distribution.get("part5") == 1
        assert exam.part_distribution.get("part6") == 1


def test_validate_exam_with_invalid_duration_and_answer(client):
    login(client, email="admin@test.com", password="admin123")
    headers = [
        "category", "title", "duration_minutes", "difficulty", "skill", "part",
        "question_text", "option_a", "option_b", "option_c", "option_d", "correct_answer", "explanation"
    ]
    # Row 1 has invalid duration "sixty mins" and invalid answer "Z"
    rows = [
        ["TOEIC", "Test Exam", "sixty mins", "Medium", "Reading", "Part 5", "Question text?", "A", "B", "C", "D", "Z", "Exp"]
    ]
    excel_file = create_mock_excel(headers, rows)

    res = client.post(
        "/admin/import/validate",
        data={"content_type": "exams", "file": (excel_file, "exam_err.xlsx")},
        content_type="multipart/form-data"
    )
    assert res.status_code == 200
    res_json = res.get_json()
    assert res_json["success"] is True
    assert res_json["error_count"] == 1
    err_msgs = " ".join(res_json["error_records"][0]["errors"])
    assert "Thời lượng bài thi" in err_msgs
    assert "Đáp án đúng" in err_msgs


