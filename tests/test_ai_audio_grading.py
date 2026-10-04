"""
Unit & Integration Tests for AI Audio Grading Engine (Feature 8.3 / Section 8.6).
Tests:
- Speech-to-Text (STT) transcription pipeline
- 4-criteria IELTS Speaking audio grading (Pronunciation, Fluency, Lexical, Grammar)
- Essay grading engine (TR, CC, LR, GRA)
- Asynchronous grading queue worker & background processing
- End-to-end exam submission with audio recording
"""

import pytest
from app.extensions import db
from app.backend.auth.models import User
from app.backend.exams.models import Exam, ExamQuestion, ExamSubmission, ExamAnswerDetail
from app.backend.exams.ai_grading import (
    round_ielts_band,
    transcribe_audio_stt,
    grade_speaking_audio,
    grade_essay_text,
    async_grade_submission,
    trigger_ai_grading
)
from tests.conftest import login


def test_round_ielts_band():
    """Verify standard official IELTS band rounding rules."""
    assert round_ielts_band(0.0) == 0.0
    assert round_ielts_band(5.1) == 5.0
    assert round_ielts_band(5.24) == 5.0
    assert round_ielts_band(5.25) == 5.5
    assert round_ielts_band(5.6) == 5.5
    assert round_ielts_band(5.74) == 5.5
    assert round_ielts_band(5.75) == 6.0
    assert round_ielts_band(8.8) == 9.0


def test_transcribe_audio_stt_variations():
    """Verify STT handling of base64 data URLs, raw strings, and binary audio."""
    # Direct transcript
    text = "Good morning, today I would like to talk about sustainable technology."
    assert transcribe_audio_stt(None, fallback_text=text) == text

    # Base64 data URL
    data_url = "data:audio/webm;base64,GkXfo59ChoEBQveBAULygQRC84EIQoK"
    stt_res = transcribe_audio_stt(data_url, fallback_text="Smartphone is useful.")
    assert "Smartphone is useful." in stt_res

    # Binary audio
    raw_bytes = b"\x1a\x45\xdf\xa3" + (b"\x00" * 1500)
    stt_bytes = transcribe_audio_stt(raw_bytes)
    assert len(stt_bytes) > 0


def test_grade_speaking_audio_empty():
    """Verify grading behavior when no audio or transcript is present."""
    result = grade_speaking_audio(audio_data="", transcript="")
    assert result["overall_band"] == 3.0
    assert result["pronunciation_score"] == 3.0
    assert "Không nhận diện được giọng nói" in result["examiner_feedback"]


def test_grade_speaking_audio_high_band():
    """Verify rich IELTS Speaking evaluation with advanced collocations and complex grammar."""
    transcript = (
        "From my perspective, artificial intelligence is ubiquitous and of paramount importance. "
        "Furthermore, if governments implement sustainable policies, it will foster profound economic transformations, "
        "although we must remain vigilant regarding potential drawbacks."
    )
    result = grade_speaking_audio(
        audio_data=None,
        transcript=transcript,
        prompt_question="What are your thoughts on AI?",
        expected_topic="Technology",
        part=3,
        duration_seconds=15.0
    )

    assert result["overall_band"] >= 6.5
    assert result["pronunciation_score"] >= 6.0
    assert result["fluency_score"] >= 6.5
    assert result["lexical_score"] >= 6.5
    assert result["grammar_score"] >= 6.5

    assert "criteria_scores" in result
    assert result["criteria_scores"]["pronunciation"] == result["pronunciation_score"]

    detailed = result["detailed_analysis"]
    assert len(detailed["strengths"]) > 0
    assert len(detailed["tips"]) > 0
    assert len(detailed["upgraded_vocab"]) > 0
    assert "pronunciation_analysis" in detailed
    assert detailed["pronunciation_analysis"]["pace_wpm"] > 0


def test_grade_essay_text():
    """Verify 4-criteria IELTS Writing evaluation."""
    essay = (
        "In modern society, technological advancement has significantly transformed communication.\n\n"
        "First and foremost, digital devices allow individuals to interact across continents seamlessly. "
        "Furthermore, if workers utilize collaborative platforms, their overall productivity increases exponentially.\n\n"
        "On the other hand, excessive screen time can lead to detrimental sedentary habits and social isolation. "
        "Consequently, establishing a balanced routine is indispensable for maintaining mental well-being.\n\n"
        "In conclusion, although technology presents certain challenges, its profound benefits are of paramount importance."
    )
    result = grade_essay_text(essay_text=essay, prompt_question="Discuss advantages and disadvantages of technology.")
    
    assert result["overall_band"] >= 6.5
    assert result["task_response_score"] >= 6.0
    assert result["coherence_score"] >= 6.0
    assert result["lexical_score"] >= 6.5
    assert result["grammar_score"] >= 6.5
    assert "criteria_scores" in result
    assert "TR" in result["criteria_scores"]


def test_async_grade_submission_audio_record(app):
    """Verify asynchronous background grading for audio recording exam submissions."""
    with app.app_context():
        user = User.query.filter_by(email="student@test.com").first()
        
        exam = Exam(
            title="IELTS Speaking & Listening Test",
            category="IELTS",
            duration=30,
            question_count=1
        )
        db.session.add(exam)
        db.session.commit()

        q_audio = ExamQuestion(
            exam_id=exam.id,
            skill="SPEAKING",
            type="AUDIO_RECORD",
            question_text="Describe your favorite hobby and why it is indispensable."
        )
        db.session.add(q_audio)
        db.session.commit()

        submission = ExamSubmission(
            user_id=user.id,
            exam_id=exam.id,
            total_score=0.0,
            status="PENDING"
        )
        db.session.add(submission)
        db.session.commit()

        detail = ExamAnswerDetail(
            submission_id=submission.id,
            question_id=q_audio.id,
            user_response={
                "text": "From my perspective, playing musical instruments is of paramount importance because it alleviates stress and fosters creativity.",
                "audio_data_url": "data:audio/webm;base64,GkXfo59ChoEBQveBAULygQRC84EIQoK"
            },
            is_correct=None,
            score=0.0
        )
        db.session.add(detail)
        db.session.commit()
        sub_id = submission.id

    # Execute async grading directly
    async_grade_submission(app, sub_id, sleep_time=0.0)

    with app.app_context():
        completed_sub = db.session.get(ExamSubmission, sub_id)
        assert completed_sub.status == "COMPLETED"
        assert completed_sub.total_score > 0.0

        ans_detail = ExamAnswerDetail.query.filter_by(submission_id=sub_id).first()
        assert ans_detail.is_correct is True
        assert ans_detail.score > 0.0
        assert ans_detail.user_response.get("overall_band") is not None
        assert ans_detail.user_response.get("pronunciation_score") is not None
        assert ans_detail.user_response.get("fluency_score") is not None
        assert ans_detail.user_response.get("ai_feedback") is not None


def test_async_grade_submission_essay(app):
    """Verify asynchronous background grading for essay submissions."""
    with app.app_context():
        user = User.query.filter_by(email="student@test.com").first()
        
        exam = Exam(
            title="Writing Task 2 Academic",
            category="IELTS",
            duration=40,
            question_count=1
        )
        db.session.add(exam)
        db.session.commit()

        q_essay = ExamQuestion(
            exam_id=exam.id,
            skill="WRITING",
            type="ESSAY",
            question_text="Some people think that environmental protection is the government's job."
        )
        db.session.add(q_essay)
        db.session.commit()

        submission = ExamSubmission(
            user_id=user.id,
            exam_id=exam.id,
            total_score=0.0,
            status="PENDING"
        )
        db.session.add(submission)
        db.session.commit()

        detail = ExamAnswerDetail(
            submission_id=submission.id,
            question_id=q_essay.id,
            user_response={
                "text": "In recent years, environmental degradation has become a ubiquitous concern.\n\nFurthermore, government policies are of paramount importance to foster sustainable energy initiatives."
            },
            is_correct=None,
            score=0.0
        )
        db.session.add(detail)
        db.session.commit()
        sub_id = submission.id

    async_grade_submission(app, sub_id, sleep_time=0.0)

    with app.app_context():
        completed_sub = db.session.get(ExamSubmission, sub_id)
        assert completed_sub.status == "COMPLETED"
        assert completed_sub.total_score > 0.0

        ans_detail = ExamAnswerDetail.query.filter_by(submission_id=sub_id).first()
        assert ans_detail.is_correct is True
        assert ans_detail.user_response.get("ai_feedback") is not None


def test_trigger_ai_grading_spawns_thread(app):
    """Verify trigger_ai_grading successfully initiates a daemon thread."""
    with app.app_context():
        user = User.query.filter_by(email="student@test.com").first()
        exam = Exam(title="Quick Exam", category="General", duration=15)
        db.session.add(exam)
        db.session.commit()

        submission = ExamSubmission(user_id=user.id, exam_id=exam.id, status="PENDING")
        db.session.add(submission)
        db.session.commit()
        sub_id = submission.id

    # Trigger async thread
    trigger_ai_grading(app, sub_id)
    # Give brief moment for thread execution
    import time
    time.sleep(0.8)

    with app.app_context():
        sub = db.session.get(ExamSubmission, sub_id)
        assert sub.status == "COMPLETED"


def test_exam_attempt_submit_with_audio_and_result_view(client, app):
    """Test full HTTP workflow: submit exam containing AUDIO_RECORD question, run grading, view result page."""
    login(client)

    with app.app_context():
        user = User.query.filter_by(email="student@test.com").first()
        user_id = user.id

        exam = Exam(
            title="Comprehensive Audio Speaking Exam",
            category="IELTS",
            duration=20,
            question_count=2
        )
        db.session.add(exam)
        db.session.commit()

        q1 = ExamQuestion(
            exam_id=exam.id,
            skill="LISTENING",
            type="SINGLE_CHOICE",
            question_text="What is the capital of England?",
            option_a="London",
            option_b="Paris",
            option_c="Rome",
            option_d="Berlin",
            correct_answer="A"
        )
        q2 = ExamQuestion(
            exam_id=exam.id,
            skill="SPEAKING",
            type="AUDIO_RECORD",
            question_text="Talk about your favorite travel destination."
        )
        db.session.add_all([q1, q2])
        db.session.commit()

        submission = ExamSubmission(
            user_id=user_id,
            exam_id=exam.id,
            status="IN_PROGRESS"
        )
        db.session.add(submission)
        db.session.commit()
        sub_id = submission.id
        q1_id = q1.id
        q2_id = q2.id

    # Submit the exam via POST
    res = client.post(
        f"/exams/attempt/{sub_id}/submit",
        data={
            f"question_{q1_id}": "A",
            f"question_{q2_id}": "From my perspective, Da Nang is a paramount coastal destination with sustainable tourism.",
            f"question_{q2_id}_audio": "data:audio/webm;base64,GkXfo59ChoEBQveBAULygQRC84EIQoK"
        },
        follow_redirects=True
    )
    assert res.status_code == 200

    # Ensure background grading completes
    async_grade_submission(app, sub_id, sleep_time=0.0)

    # View result page
    res_result = client.get(f"/exams/result/{sub_id}")
    assert res_result.status_code == 200
    html = res_result.get_data(as_text=True)

    assert "Kết quả: Comprehensive Audio Speaking Exam" in html
    assert "AI Feedback" in html
    assert "Overall Band" in html
    assert "Pronunciation" in html
