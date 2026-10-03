"""
Tests for Feature 8.2: THPT Exam - 50-Question National High School Graduation Mock Exam
"""

import pytest
from app.extensions import db
from app.backend.exams.models import Exam, ExamQuestion, ExamSubmission, ExamAnswerDetail
from app.seeds.thpt_seeds import seed_thpt_exams, THPT_50_QUESTIONS
from tests.conftest import login


def test_thpt_seed_and_questions_structure(app):
    """Verify THPT exam model and 50 questions with all standard parts."""
    with app.app_context():
        exam = seed_thpt_exams()
        assert exam is not None
        assert exam.category == "THPT"
        assert exam.duration == 60
        assert exam.question_count == 50

        questions = ExamQuestion.query.filter_by(exam_id=exam.id).order_by(ExamQuestion.id).all()
        assert len(questions) == 50

        # Check part categories
        parts = {q.part for q in questions}
        assert any("Ngữ âm" in p for p in parts)
        assert any("Trọng âm" in p for p in parts)
        assert any("Ngữ pháp" in p for p in parts)
        assert any("Giao tiếp" in p for p in parts)
        assert any("đồng nghĩa" in p.lower() for p in parts)
        assert any("trái nghĩa" in p.lower() for p in parts)
        assert any("Điền từ" in p for p in parts)
        assert any("Đọc hiểu" in p for p in parts)
        assert any("Tìm lỗi sai" in p for p in parts)
        assert any("Biến đổi câu" in p or "Kết hợp câu" in p for p in parts)

        # Every question must have question_text, 4 options, a valid correct_answer, and explanation
        for q in questions:
            assert q.question_text is not None and len(q.question_text) > 0
            assert q.option_a is not None and len(q.option_a) > 0
            assert q.option_b is not None and len(q.option_b) > 0
            assert q.option_c is not None and len(q.option_c) > 0
            assert q.option_d is not None and len(q.option_d) > 0
            assert q.correct_answer in ["A", "B", "C", "D"]
            assert q.explanation is not None and len(q.explanation) > 0


def test_thpt_exam_list_and_hub_views(client, app):
    """Verify THPT exam appears in Exam List and Specialized Hub."""
    with app.app_context():
        seed_thpt_exams()

    login(client)

    # Check Exam List with THPT filter
    res = client.get("/exam?category=THPT")
    assert res.status_code == 200
    assert "THPT Quốc Gia" in res.get_data(as_text=True)
    assert "Đề Thi Thử Tốt Nghiệp THPT Quốc Gia" in res.get_data(as_text=True)

    # Check Specialized Hub
    res_hub = client.get("/specialized")
    assert res_hub.status_code == 200
    assert "Đề Thi THPT Quốc Gia" in res_hub.get_data(as_text=True)

    # Check Direct Start Route
    res_start = client.get("/specialized/thpt", follow_redirects=False)
    assert res_start.status_code == 302
    assert "/start" in res_start.headers["Location"]


def test_thpt_exam_full_attempt_flow(client, app):
    """Verify user can start THPT exam, submit answers, and receive detailed results."""
    with app.app_context():
        exam = seed_thpt_exams()
        exam_id = exam.id

    login(client)

    # Start exam
    res_start = client.post(f"/exam/{exam_id}/start", data={"mode": "real"}, follow_redirects=True)
    assert res_start.status_code == 200
    html = res_start.get_data(as_text=True)
    assert "Đề Thi Thử Tốt Nghiệp THPT Quốc Gia" in html
    assert "Câu 50" in html

    # Get created submission
    with app.app_context():
        sub = ExamSubmission.query.filter_by(exam_id=exam_id).order_by(ExamSubmission.id.desc()).first()
        assert sub is not None
        submission_id = sub.id
        questions = ExamQuestion.query.filter_by(exam_id=exam_id).order_by(ExamQuestion.id).all()

        # Prepare form answers: Answer first 40 correctly, leave rest blank
        form_data = {}
        for i, q in enumerate(questions):
            if i < 40:
                form_data[f"question_{q.id}"] = q.correct_answer

    # Submit exam
    res_submit = client.post(f"/exam/attempt/{submission_id}/submit", data=form_data, follow_redirects=True)
    assert res_submit.status_code == 200
    result_html = res_submit.get_data(as_text=True)
    assert "Kết quả: Đề Thi Thử Tốt Nghiệp THPT Quốc Gia" in result_html
    assert "40" in result_html
    assert "50" in result_html

    with app.app_context():
        sub_updated = db.session.get(ExamSubmission, submission_id)
        assert sub_updated.status == "COMPLETED"
        assert sub_updated.total_score == 40
        details = ExamAnswerDetail.query.filter_by(submission_id=submission_id).all()
        assert len(details) == 50
        correct_count = sum(1 for d in details if d.is_correct)
        assert correct_count == 40
