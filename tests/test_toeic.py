import pytest
from app.extensions import db
from app.models import ToeicTest, ToeicQuestion, ToeicAttempt, ToeicAttemptAnswer
from tests.conftest import login

@pytest.fixture
def toeic_setup(app):
    with app.app_context():
        # Setup a sample TOEIC test
        test = ToeicTest(title="TOEIC Test 1")
        db.session.add(test)
        db.session.flush()

        # Add 3 questions
        q1 = ToeicQuestion(
            test_id=test.id, part=5, question_number=101,
            question_text="He _______ to school every day.",
            option_a="go", option_b="goes", option_c="going", option_d="went",
            correct_option="B", explanation="Subject is third person singular."
        )
        q2 = ToeicQuestion(
            test_id=test.id, part=5, question_number=102,
            question_text="We leave _______ noon.",
            option_a="at", option_b="on", option_c="in", option_d="for",
            correct_option="A", explanation="Use at before noon."
        )
        q3 = ToeicQuestion(
            test_id=test.id, part=6, question_number=131,
            question_text="131.",
            option_a="recent", option_b="constant", option_c="early", option_d="late",
            correct_option="A", explanation="Context requires recent."
        )
        db.session.add_all([q1, q2, q3])
        db.session.commit()
        return test.id

def test_toeic_list_requires_login(client):
    response = client.get("/toeic")
    assert response.status_code == 302
    assert "login" in response.headers["Location"]

def test_toeic_list_success(client, app, toeic_setup):
    login(client)
    response = client.get("/toeic")
    assert response.status_code == 200
    assert b"TOEIC Test 1" in response.data

def test_toeic_start_attempt(client, app, toeic_setup):
    login(client)
    # Start attempt
    response = client.post(f"/toeic/{toeic_setup}/start", follow_redirects=False)
    assert response.status_code == 302
    assert "attempt" in response.headers["Location"]

    with app.app_context():
        attempt = ToeicAttempt.query.first()
        assert attempt is not None
        assert attempt.test_id == toeic_setup
        assert attempt.is_submitted is False

def test_toeic_attempt_page(client, app, toeic_setup):
    login(client)
    # Start the test
    client.post(f"/toeic/{toeic_setup}/start")
    
    with app.app_context():
        attempt_id = ToeicAttempt.query.first().id
        
    response = client.get(f"/toeic/attempt/{attempt_id}")
    assert response.status_code == 200
    assert b"TOEIC Test 1" in response.data
    assert b"101" in response.data

def test_toeic_submit_and_result(client, app, toeic_setup):
    login(client)
    client.post(f"/toeic/{toeic_setup}/start")
    
    with app.app_context():
        attempt = ToeicAttempt.query.first()
        attempt_id = attempt.id
        questions = ToeicQuestion.query.filter_by(test_id=toeic_setup).all()
        q_map = {q.question_number: q.id for q in questions}

    # Submit correct answers for q101 and q102, wrong for q131
    data = {
        f"question_{q_map[101]}": "B",  # Correct
        f"question_{q_map[102]}": "A",  # Correct
        f"question_{q_map[131]}": "B",  # Incorrect (Correct is A)
        "time_spent": "120"
    }
    
    response = client.post(f"/toeic/attempt/{attempt_id}/submit", data=data, follow_redirects=True)
    assert response.status_code == 200
    assert "Kết quả" in response.data.decode('utf-8')
    assert b"2/3" in response.data or b"2" in response.data
    
    with app.app_context():
        final_attempt = db.session.get(ToeicAttempt, attempt_id)
        assert final_attempt.is_submitted is True
        assert final_attempt.score == 2
        assert final_attempt.time_spent == 120
        
        # Verify answers saved
        answers = ToeicAttemptAnswer.query.filter_by(attempt_id=attempt_id).all()
        assert len(answers) == 3
        # Check q101 answer
        ans_101 = [a for a in answers if a.question.question_number == 101][0]
        assert ans_101.selected_option == "B"
        assert ans_101.is_correct is True
