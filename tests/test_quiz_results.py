from datetime import datetime
from app.extensions import db
from app.modules.auth.models import User
from app.modules.learning.models import GrammarErrorLog, Question, QuizAttempt, QuizAttemptAnswer
from tests.conftest import login


def ensure_sample_attempt():
    user = User.query.filter_by(email="student@test.com").first()
    ques = Question.query.first()
    if not ques:
        ques = Question(
            level="A1",
            topic="Grammar",
            question_text="Sample Question",
            option_a="A",
            option_b="B",
            option_c="C",
            option_d="D",
            correct_option="A",
            explanation="Explanation"
        )
        db.session.add(ques)
        db.session.commit()

    att = QuizAttempt(
        user_id=user.id,
        level="A1",
        topic="Kiểm Tra Ngữ Pháp Tổng Hợp A1",
        score=1,
        total_questions=2,
        duration_seconds=120,
        created_at=datetime.utcnow()
    )
    db.session.add(att)
    db.session.commit()

    ans1 = QuizAttemptAnswer(attempt_id=att.id, question_id=ques.id, selected_option="A", is_correct=True)
    ans2 = QuizAttemptAnswer(attempt_id=att.id, question_id=ques.id, selected_option="B", is_correct=False)
    db.session.add_all([ans1, ans2])
    db.session.commit()
    return att


def test_quiz_results_render(client):
    login(client)

    with client.application.app_context():
        att = ensure_sample_attempt()
        att_id = att.id

    res = client.get(f"/quizzes/results/{att_id}")
    assert res.status_code == 200
    assert "Kiểm Tra Ngữ Pháp Tổng Hợp A1".encode("utf-8") in res.data
    assert "Tỷ lệ chính xác".encode("utf-8") in res.data
    assert "Số câu đúng".encode("utf-8") in res.data
    assert "Số câu sai".encode("utf-8") in res.data
    assert "Thời gian dùng".encode("utf-8") in res.data


def test_quiz_results_auto_error_log(client):
    login(client)

    with client.application.app_context():
        att = ensure_sample_attempt()
        att_id = att.id
        user_id = att.user_id

    client.get(f"/quizzes/results/{att_id}")

    with client.application.app_context():
        err_logs = GrammarErrorLog.query.filter_by(user_id=user_id, attempt_id=att_id).all()
        assert len(err_logs) > 0


def test_quiz_results_pdf_view(client):
    login(client)

    with client.application.app_context():
        att = ensure_sample_attempt()
        att_id = att.id

    res_pdf = client.get(f"/quizzes/results/{att_id}/pdf")
    assert res_pdf.status_code == 200
    assert "Báo Cáo Kết Quả Bài Test PDF".encode("utf-8") in res_pdf.data
    assert "TỔNG ĐIỂM".encode("utf-8") in res_pdf.data
