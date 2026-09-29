import pytest
from app.extensions import db
from app.backend.learning.models import Lesson
from app.backend.learning.routes import _calculate_word_similarity
from tests.conftest import login


def test_word_similarity_algorithm():
    """Test Levenshtein word similarity scoring helper."""
    assert _calculate_word_similarity("hello", "hello") == 1.0
    assert _calculate_word_similarity("Hello,", "hello") == 1.0
    assert _calculate_word_similarity("thank", "thanks") >= 0.8
    assert _calculate_word_similarity("good", "great") < 0.6
    assert _calculate_word_similarity("", "") == 1.0
    assert _calculate_word_similarity("word", "") == 0.0


def test_speaking_evaluate_api_perfect_match(client):
    """Test AI speaking evaluation endpoint with a high-accuracy match."""
    login(client)

    with client.application.app_context():
        lesson = Lesson(
            title="Airport Check-in Speaking Practice",
            level="B1",
            skill="Speaking",
            short_description="Learn check-in vocabulary and phrases.",
            content="Airport check-in conversations.",
            examples="Here is my passport.|Đây là hộ chiếu của tôi.",
            skill_data={
                "speaking_genre": "Giao tiếp du lịch",
                "sentences": [
                    {
                        "idx": 1,
                        "text": "Could you please tell me where the boarding gate is?",
                        "ipa": "/kʊd juː pliːz tel miː wer ðə ˈbɔːr.dɪŋ ɡeɪt ɪz/",
                        "vi": "Bạn có thể chỉ cho tôi cổng lên máy bay ở đâu không?"
                    }
                ]
            }
        )
        db.session.add(lesson)
        db.session.commit()
        lesson_id = lesson.id

    # POST evaluate with exact match
    res = client.post(
        f"/lessons/{lesson_id}/speaking/evaluate",
        json={
            "target_text": "Could you please tell me where the boarding gate is?",
            "spoken_text": "Could you please tell me where the boarding gate is?",
            "sentence_idx": 0
        }
    )
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    eval_data = data["evaluation"]
    assert eval_data["overall_score"] >= 95
    assert eval_data["grade"] == "Excellent"
    assert eval_data["completeness_score"] == 100
    assert all(w["status"] == "correct" for w in eval_data["word_analysis"])


def test_speaking_evaluate_api_partial_match(client):
    """Test AI speaking evaluation endpoint with partial accuracy and mispronounced words."""
    login(client)

    with client.application.app_context():
        lesson = Lesson(
            title="Restaurant Ordering Practice",
            level="A2",
            skill="Speaking",
            short_description="Ordering food at a restaurant.",
            content="Restaurant conversation sentences.",
            examples="I would like a coffee.|Tôi muốn gọi một ly cà phê.",
            skill_data={"speaking_genre": "Đời sống"}
        )
        db.session.add(lesson)
        db.session.commit()
        lesson_id = lesson.id

    # Spoken text missing some words or with different words
    res = client.post(
        f"/lessons/{lesson_id}/speaking/evaluate",
        json={
            "target_text": "I would like a table for two people please",
            "spoken_text": "I want a table for two",
            "sentence_idx": 0
        }
    )
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    eval_data = data["evaluation"]
    assert 30 <= eval_data["overall_score"] <= 85
    assert len(eval_data["word_analysis"]) == 9

    # Verify status breakdown
    statuses = [w["status"] for w in eval_data["word_analysis"]]
    assert "correct" in statuses
    assert "incorrect" in statuses
    assert eval_data["ai_feedback"] != ""
