from app.extensions import db
from app.modules.auth.models import User
from app.modules.learning.models import Question, Quiz, QuizAttempt
from tests.conftest import login


def ensure_quiz_and_question():
    q = Quiz.query.filter_by(title="Kiểm Tra Ngữ Pháp Tổng Hợp A1").first()
    if not q:
        q = Quiz(
            title="Kiểm Tra Ngữ Pháp Tổng Hợp A1",
            category="Grammar",
            level="A1",
            skill="Grammar",
            difficulty="Easy",
            description="Bài test A1.",
            question_count=5,
            duration_minutes=10
        )
        db.session.add(q)

    ques = Question.query.filter_by(level="A1").first()
    if not ques:
        ques = Question(
            level="A1",
            topic="Grammar",
            question_text="Choose the correct verb: She ___ to school every day.",
            option_a="go",
            option_b="goes",
            option_c="going",
            option_d="gone",
            correct_option="B",
            explanation="She là ngôi 3 số ít dùng 'goes'."
        )
        db.session.add(ques)

    db.session.commit()
    return q


def test_quiz_start_and_take_render(client):
    login(client)

    with client.application.app_context():
        quiz = ensure_quiz_and_question()
        quiz_id = quiz.id

    res_start = client.get(f"/quizzes/{quiz_id}/start", follow_redirects=True)
    assert res_start.status_code == 200
    assert "Kiểm Tra Ngữ Pháp Tổng Hợp A1".encode("utf-8") in res_start.data
    assert "Danh sách câu hỏi".encode("utf-8") in res_start.data
    assert "Hướng dẫn".encode("utf-8") in res_start.data
    assert "Tạm dừng".encode("utf-8") in res_start.data
    assert "Nộp bài".encode("utf-8") in res_start.data


def test_quiz_answer_and_mark_review(client):
    login(client)

    with client.application.app_context():
        quiz = ensure_quiz_and_question()
        quiz_id = quiz.id

    client.get(f"/quizzes/{quiz_id}/start", follow_redirects=True)

    # Save answer B for q_idx 0
    res_ans = client.post(f"/quizzes/{quiz_id}/answer", json={
        "q_idx": 0,
        "option": "B",
        "elapsed_seconds": 15
    })
    assert res_ans.status_code == 200
    json_ans = res_ans.get_json()
    assert json_ans["success"] is True
    assert json_ans["answers"]["0"] == "B"

    # Toggle mark review for q_idx 0
    res_mark = client.post(f"/quizzes/{quiz_id}/answer", json={
        "q_idx": 0,
        "toggle_mark": True,
        "elapsed_seconds": 20
    })
    assert res_mark.status_code == 200
    json_mark = res_mark.get_json()
    assert 0 in json_mark["marked_reviews"]


def test_quiz_pause_resume(client):
    login(client)

    with client.application.app_context():
        quiz = ensure_quiz_and_question()
        quiz_id = quiz.id

    client.get(f"/quizzes/{quiz_id}/start", follow_redirects=True)

    res_pause = client.post(f"/quizzes/{quiz_id}/pause", json={"is_paused": True, "elapsed_seconds": 45})
    assert res_pause.status_code == 200
    assert res_pause.get_json()["is_paused"] is True

    res_resume = client.post(f"/quizzes/{quiz_id}/pause", json={"is_paused": False, "elapsed_seconds": 46})
    assert res_resume.status_code == 200
    assert res_resume.get_json()["is_paused"] is False


def test_quiz_submit(client):
    login(client)

    with client.application.app_context():
        quiz = ensure_quiz_and_question()
        quiz_id = quiz.id

    client.get(f"/quizzes/{quiz_id}/start", follow_redirects=True)
    client.post(f"/quizzes/{quiz_id}/answer", json={"q_idx": 0, "option": "B", "elapsed_seconds": 30})

    res_sub = client.post(f"/quizzes/{quiz_id}/submit", data={"elapsed_seconds": 60}, follow_redirects=True)
    assert res_sub.status_code == 200
    assert "Chúc mừng bạn đã hoàn thành".encode("utf-8") in res_sub.data

    with client.application.app_context():
        user = User.query.filter_by(email="student@test.com").first()
        att = QuizAttempt.query.filter_by(user_id=user.id).order_by(QuizAttempt.id.desc()).first()
        assert att is not None
        assert att.duration_seconds == 60
