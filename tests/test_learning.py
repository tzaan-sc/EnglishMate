from app.models import Lesson, LessonProgress, QuizAttempt, Question
from tests.conftest import login


def test_view_lessons(client):
    login(client)
    response = client.get("/lessons")
    assert response.status_code == 200
    assert b"Test lesson" in response.data


def test_complete_lesson(client, app):
    login(client)
    with app.app_context():
        lesson_id = Lesson.query.first().id
    response = client.post(f"/lessons/{lesson_id}/complete", follow_redirects=True)
    assert response.status_code == 200
    with app.app_context():
        assert LessonProgress.query.count() == 1


def test_take_quiz_and_save_score(client, app):
    login(client)
    with app.app_context():
        ids = [str(q.id) for q in Question.query.all()]
    data = {"question_ids": ",".join(ids), "level": "A1", "topic": "Daily Life"}
    data.update({f"question_{qid}": "A" for qid in ids})
    response = client.post("/quiz", data=data, follow_redirects=True)
    assert response.status_code == 200
    assert b"100%" in response.data
    with app.app_context():
        attempt = QuizAttempt.query.one()
        assert attempt.score == 10
        assert len(attempt.answers) == 10


def test_all_learner_pages_render(client, app):
    login(client)
    with app.app_context():
        lesson_id = Lesson.query.first().id
    for path in ["/dashboard", "/lessons", f"/lessons/{lesson_id}", "/vocabulary",
                 "/flashcards", "/quiz", "/progress"]:
        response = client.get(path)
        assert response.status_code == 200, path
