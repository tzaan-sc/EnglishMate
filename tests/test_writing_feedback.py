import pytest
from app.extensions import db
from app.backend.learning.models import Lesson, WritingSubmission, LessonProgress
from app.backend.learning.grammar_checker import evaluate_writing_submission
from tests.conftest import login


def test_evaluate_writing_submission_engine():
    """Test AI essay grading engine with various text samples."""
    sample_essay = (
        "In modern society, learning foreign languages has become essential for personal development. "
        "Firstly, it opens up numerous career opportunities in international companies. "
        "Furthermore, speaking English enhances communication skills and cultural understanding. "
        "In conclusion, investing time in language learning provides significant long-term benefits."
    )
    result = evaluate_writing_submission(
        text=sample_essay,
        target_min=40,
        target_max=80,
        prompt="Discuss the benefits of learning English."
    )

    assert result["overall_score"] >= 7.0
    assert result["word_count"] >= 40
    assert "criteria" in result
    assert "task_response" in result["criteria"]
    assert "coherence_cohesion" in result["criteria"]
    assert "lexical_resource" in result["criteria"]
    assert "grammatical_accuracy" in result["criteria"]
    assert len(result["strengths"]) > 0
    assert len(result["improvements"]) > 0
    assert result["general_feedback"] != ""


def test_evaluate_writing_submission_empty():
    """Test evaluation engine with empty essay."""
    result = evaluate_writing_submission("")
    assert result["overall_score"] == 0.0
    assert result["word_count"] == 0
    assert "Chưa" in result["grade"]


def test_submit_writing_lesson_api(client):
    """Test submitting an essay via API endpoint."""
    login(client)

    with client.application.app_context():
        lesson = Lesson(
            title="My Favorite Hobby Essay",
            level="B1",
            skill="Writing",
            short_description="Write an essay about your favorite hobby.",
            content="Writing practice on hobbies and leisure activities.",
            examples="Reading books is fun.|Đọc sách rất thú vị.",
            skill_data={
                "target_min": 40,
                "target_max": 80,
                "writing_prompt": "Describe your favorite hobby and explain why you enjoy it."
            }
        )
        db.session.add(lesson)
        db.session.commit()
        lesson_id = lesson.id

    essay_text = (
        "My favorite hobby is reading books because it helps me expand my knowledge and relax after stressful study hours. "
        "First, I love reading science fiction novels. Furthermore, reading books improves my vocabulary and concentration. "
        "In summary, reading is a wonderful habit that everyone should cultivate."
    )

    # Submit essay via JSON
    res = client.post(
        f"/lessons/{lesson_id}/writing/submit",
        json={"content": essay_text}
    )
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    assert "evaluation" in data
    assert data["evaluation"]["overall_score"] >= 7.0
    assert data["xp_earned"] >= 30

    # Verify database record
    with client.application.app_context():
        sub = WritingSubmission.query.filter_by(lesson_id=lesson_id).first()
        assert sub is not None
        assert sub.word_count >= 40
        assert sub.score >= 7.0
        assert sub.status == "GRADED"

        prog = LessonProgress.query.filter_by(lesson_id=lesson_id).first()
        assert prog is not None


def test_submit_writing_lesson_empty(client):
    """Test submitting an empty essay returns error."""
    login(client)

    with client.application.app_context():
        lesson = Lesson(
            title="Empty Test Writing",
            level="A2",
            skill="Writing",
            short_description="Short desc",
            content="Content",
            examples="Example|Ví dụ"
        )
        db.session.add(lesson)
        db.session.commit()
        lesson_id = lesson.id

    res = client.post(
        f"/writing/{lesson_id}/submit",
        json={"content": "   "}
    )
    assert res.status_code == 400
    data = res.get_json()
    assert data["status"] == "error"


def test_submit_writing_lesson_unauthorized(client):
    """Test unauthorized access redirects or denies."""
    res = client.post(
        "/writing/1/submit",
        json={"content": "Some essay text"}
    )
    assert res.status_code in [302, 401]
