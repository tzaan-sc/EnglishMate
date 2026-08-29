from app.extensions import db
from app.modules.auth.models import User
from app.modules.learning.models import GrammarExerciseAttempt, GrammarErrorLog, Question
from tests.conftest import login


def ensure_grammar_questions():
    if Question.query.filter_by(topic="Grammar").count() == 0:
        q = Question(
            question_text="She ______ at a technology company.",
            option_a="work",
            option_b="works",
            option_c="working",
            option_d="worked",
            correct_option="B",
            explanation="Hiện tại đơn ngôi 3 số ít.",
            level="A1",
            topic="Grammar"
        )
        db.session.add(q)
        db.session.commit()


def test_grammar_exercises_setup_render(client):
    login(client)
    res = client.get("/grammar/exercises")
    assert res.status_code == 200
    assert "Thiêt lập bài tập".encode("utf-8") in res.data
    assert "Bắt đầu bài tập".encode("utf-8") in res.data


def test_start_and_do_grammar_exercise(client):
    login(client)

    with client.application.app_context():
        ensure_grammar_questions()

    # Start exercise session
    res_start = client.post(
        "/grammar/exercises/start",
        data={"difficulty": "Easy", "question_count": 5},
        follow_redirects=True,
    )
    assert res_start.status_code == 200
    assert "Đang làm bài tập ngữ pháp".encode("utf-8") in res_start.data
    assert "Câu 1 /".encode("utf-8") in res_start.data


def test_submit_and_summary_grammar_exercise(client):
    login(client)

    with client.application.app_context():
        ensure_grammar_questions()

    client.post(
        "/grammar/exercises/start",
        data={"difficulty": "Easy", "question_count": 5},
        follow_redirects=True,
    )

    with client.session_transaction() as sess:
        q_ids = sess.get("grammar_exercise", {}).get("question_ids", [])

    form_data = {f"q_{qid}": "X" for qid in q_ids}

    # Submit answers (wrong answer X for all)
    res_sub = client.post(
        "/grammar/exercises/submit",
        data=form_data,
        follow_redirects=True,
    )
    assert res_sub.status_code == 200
    assert "Kết Quả Bài Tập Ngữ Pháp".encode("utf-8") in res_sub.data

    with client.application.app_context():
        user = User.query.filter_by(email="student@test.com").first()
        attempt = GrammarExerciseAttempt.query.filter_by(user_id=user.id).order_by(GrammarExerciseAttempt.completed_at.desc()).first()
        assert attempt is not None
        assert attempt.score == 0

        errs = GrammarErrorLog.query.filter_by(user_id=user.id, attempt_id=attempt.id).all()
        assert len(errs) == len(q_ids)


def test_retry_incorrect_grammar_exercise(client):
    login(client)

    with client.application.app_context():
        ensure_grammar_questions()
        user = User.query.filter_by(email="student@test.com").first()
        q = Question.query.filter_by(topic="Grammar").first()

        attempt = GrammarExerciseAttempt(
            user_id=user.id,
            difficulty="Easy",
            question_count=1,
            score=0,
            total_questions=1,
            duration_seconds=30
        )
        db.session.add(attempt)
        db.session.commit()

        err = GrammarErrorLog(
            user_id=user.id,
            question_id=q.id,
            attempt_id=attempt.id,
            user_answer="A",
            correct_answer="B"
        )
        db.session.add(err)
        db.session.commit()
        att_id = attempt.id

    res_retry = client.post(f"/grammar/exercises/retry/{att_id}", follow_redirects=True)
    assert res_retry.status_code == 200
    assert "Đã mở chế độ Thử lại các câu sai!".encode("utf-8") in res_retry.data
