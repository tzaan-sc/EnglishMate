"""
Tests for Feature 8.1: IELTS Speaking Simulation Room (3-Part Standard)
"""

import pytest
from app.extensions import db
from app.backend.auth.models import User
from app.backend.exams.models import (
    IeltsSpeakingTest,
    IeltsSpeakingTopic,
    IeltsSpeakingSubmission,
    IeltsSpeakingAnswer
)
from app.seeds.ielts_speaking_seeds import seed_ielts_speaking_tests
from app.backend.exams.speaking_evaluator import evaluate_speaking_submission_ai, round_ielts_band
from tests.conftest import login


def test_seed_and_models(app):
    """Verify IELTS Speaking database models and seed data."""
    with app.app_context():
        seed_ielts_speaking_tests()
        tests = IeltsSpeakingTest.query.all()
        assert len(tests) >= 3

        test1 = IeltsSpeakingTest.query.first()
        assert test1 is not None
        assert len(test1.topics) == 3  # Part 1, Part 2, Part 3

        p1 = next((t for t in test1.topics if t.part == 1), None)
        p2 = next((t for t in test1.topics if t.part == 2), None)
        p3 = next((t for t in test1.topics if t.part == 3), None)

        assert p1 is not None
        assert p2 is not None
        assert p3 is not None
        assert p2.prep_time_seconds == 60
        assert p2.cue_card_prompt is not None


def test_speaking_evaluator_rubric():
    """Verify AI rubric evaluation logic for IELTS Speaking."""
    assert round_ielts_band(6.2) == 6.0
    assert round_ielts_band(6.25) == 6.5
    assert round_ielts_band(6.75) == 7.0

    mock_answers = [
        {
            "part": 1,
            "candidate_transcript": "I frequently utilize modern technology in my everyday routine, furthermore it is indispensable."
        },
        {
            "part": 2,
            "candidate_transcript": "I would like to talk about my smartphone. It is of paramount importance because it streamlines my daily communication. If I did not have it, collaborating would be challenging."
        },
        {
            "part": 3,
            "candidate_transcript": "From my perspective, artificial intelligence is ubiquitous and will foster profound transformations in society, although we must be vigilant."
        }
    ]

    result = evaluate_speaking_submission_ai(mock_answers)
    assert result["overall_band"] >= 6.0
    assert "detailed_analysis" in result
    assert "strengths" in result["detailed_analysis"]
    assert "upgraded_vocab" in result["detailed_analysis"]


def test_speaking_list_page(client):
    """Test IELTS Speaking test catalog page."""
    login(client)
    response = client.get("/exams/speaking")
    assert response.status_code == 200
    assert "IELTS SPEAKING" in response.get_data(as_text=True)

    # Test alternate route /ielts-speaking
    response_alt = client.get("/ielts-speaking")
    assert response_alt.status_code == 200

    # Test search filter
    response_search = client.get("/exams/speaking?q=Technology")
    assert response_search.status_code == 200
    assert "Technology" in response_search.get_data(as_text=True)


def test_speaking_simulation_flow(client, app):
    """Test complete flow: start test -> save answers -> submit -> view scorecard."""
    login(client)

    with app.app_context():
        seed_ielts_speaking_tests()
        test_obj = IeltsSpeakingTest.query.first()
        test_id = test_obj.id
        user = User.query.filter_by(email="student@test.com").first()
        user_id = user.id

    # 1. Start speaking test
    start_res = client.post(f"/exams/speaking/{test_id}/start", follow_redirects=True)
    assert start_res.status_code == 200

    with app.app_context():
        sub = IeltsSpeakingSubmission.query.filter_by(user_id=user_id, test_id=test_id).first()
        assert sub is not None
        assert sub.status == "IN_PROGRESS"
        sub_id = sub.id

    # 2. Access simulation room
    room_res = client.get(f"/exams/speaking/room/{sub_id}")
    assert room_res.status_code == 200
    assert "Bàn Thu Âm" in room_res.get_data(as_text=True)

    # 3. Save answers for Part 1 and Part 2 via AJAX
    save_p1 = client.post(f"/exams/speaking/room/{sub_id}/save-answer", json={
        "part": 1,
        "topic_id": 1,
        "question_index": 0,
        "question_text": "What device do you use?",
        "candidate_transcript": "I usually rely on my smartphone furthermore it is indispensable for daily work.",
        "candidate_notes": "",
        "audio_data_url": "data:audio/webm;base64,GkXfo59ChoEBQveBAULygQRC84EIQoK"
    })
    assert save_p1.status_code == 200
    assert save_p1.json["status"] == "success"

    save_p2 = client.post(f"/exams/speaking/room/{sub_id}/save-answer", json={
        "part": 2,
        "topic_id": 2,
        "question_index": 0,
        "question_text": "Describe a piece of technology",
        "candidate_transcript": "Today I will describe my laptop which is paramount for software engineering. Although it was expensive, it fosters my productivity.",
        "candidate_notes": "1. Laptop bought 2 years ago\n2. Work & code\n3. Indispensable",
        "audio_data_url": "data:audio/webm;base64,GkXfo59ChoEBQveBAULygQRC84EIQoK"
    })
    assert save_p2.status_code == 200

    # 4. Submit test
    submit_res = client.post(f"/exams/speaking/room/{sub_id}/submit", data={
        "time_spent": 720
    }, follow_redirects=True)
    assert submit_res.status_code == 200

    with app.app_context():
        completed_sub = db.session.get(IeltsSpeakingSubmission, sub_id)
        assert completed_sub.status == "COMPLETED"
        assert completed_sub.overall_band >= 5.0
        assert completed_sub.fluency_score >= 5.0
        assert completed_sub.time_spent == 720

    # 5. Result page verification
    result_res = client.get(f"/exams/speaking/result/{sub_id}")
    assert result_res.status_code == 200
    res_text = result_res.get_data(as_text=True)
    assert "IELTS SPEAKING OFFICIAL BAND SCORE" in res_text
    assert "Fluency & Coherence" in res_text
    assert "Lexical Resource" in res_text


def test_speaking_test_history_and_deletion(client, app):
    """Test speaking submissions appear in history and can be deleted."""
    login(client)

    with app.app_context():
        seed_ielts_speaking_tests()
        test_obj = IeltsSpeakingTest.query.first()
        user = User.query.filter_by(email="student@test.com").first()
        sub = IeltsSpeakingSubmission(
            user_id=user.id,
            test_id=test_obj.id,
            status="COMPLETED",
            overall_band=7.5,
            fluency_score=7.5,
            lexical_score=7.5,
            grammar_score=7.0,
            pronunciation_score=8.0,
            examiner_feedback="Excellent response",
            time_spent=900
        )
        db.session.add(sub)
        db.session.commit()
        sub_id = sub.id

    # Check test history
    history_res = client.get("/exams/history?type=IELTS")
    assert history_res.status_code == 200
    assert "Band 7.5" in history_res.get_data(as_text=True)

    # Delete via history endpoint
    del_res = client.post(f"/exams/history/speaking/{sub_id}/delete", follow_redirects=True)
    assert del_res.status_code == 200

    with app.app_context():
        deleted = db.session.get(IeltsSpeakingSubmission, sub_id)
        assert deleted is None
