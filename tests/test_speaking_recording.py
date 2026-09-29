import pytest
from app.extensions import db
from app.backend.learning.models import Lesson
from tests.conftest import login


def test_speaking_lesson_model_and_structure(app):
    """Test Speaking lesson model and skill data persistence."""
    with app.app_context():
        lesson = Lesson(
            title="Job Interview Introduction",
            level="B2",
            skill="Speaking",
            short_description="Learn how to present yourself confidently in an English interview.",
            content="Practice self-introduction clearly.",
            examples="Tell me about yourself.|Hãy giới thiệu về bản thân.",
            skill_data={
                "speaking_genre": "Phỏng vấn xin việc (Job Interview)",
                "context": "Bạn đang phỏng vấn cho vị trí Software Engineer tại một công ty đa quốc gia.",
                "sentences": [
                    {
                        "idx": 1,
                        "text": "Good morning, thank you for inviting me to this interview.",
                        "ipa": "/ɡʊd ˈmɔːr.nɪŋ ˈθæŋk juː fɔːr ɪnˈvaɪ.tɪŋ miː tuː ðɪs ˈɪn.tɚ.vjuː/",
                        "vi": "Chào buổi sáng, cảm ơn quý công ty đã mời tôi tham gia phỏng vấn."
                    },
                    {
                        "idx": 2,
                        "text": "I have over five years of experience in backend development.",
                        "ipa": "/aɪ hæv ˈoʊ.vɚ faɪv jɪərz ʌv ɪkˈspɪr.i.əns ɪn ˈbæk.end dɪˈvel.əp.mənt/",
                        "vi": "Tôi có hơn năm năm kinh nghiệm trong phát triển hệ thống backend."
                    }
                ],
                "tips": [
                    "Phát âm rõ âm cuối 'thank you', 'experience'.",
                    "Giữ ngữ điệu tự tin và tốc độ vừa phải."
                ]
            }
        )
        db.session.add(lesson)
        db.session.commit()

        saved = Lesson.query.filter_by(title="Job Interview Introduction").first()
        assert saved is not None
        assert saved.skill == "Speaking"
        assert saved.skill_slug == "speaking"
        assert saved.url == f"/speaking/{saved.id}"
        assert len(saved.skill_data.get("sentences", [])) == 2


def test_speaking_recording_page_elements(client):
    """Test that /speaking/<id> renders all Speaking Recording & Visualizer UI components."""
    login(client)

    with client.application.app_context():
        lesson = Lesson(
            title="Daily Coffee Shop Ordering",
            level="A2",
            skill="Speaking",
            short_description="Practice ordering coffee naturally in English.",
            content="Speaking practice at a coffee shop.",
            examples="Can I have a latte?|Cho tôi một ly latte nhé.",
            skill_data={
                "speaking_genre": "Giao tiếp đời sống",
                "sentences": [
                    {
                        "idx": 1,
                        "text": "Can I have a medium iced latte with oat milk, please?",
                        "ipa": "/kæn aɪ hæv ə ˈmiː.di.əm aɪst ˈlɑː.teɪ wɪð oʊt mɪlk pliːz/",
                        "vi": "Cho tôi một ly latte đá cỡ vừa với sữa yến mạch nhé?"
                    }
                ]
            }
        )
        db.session.add(lesson)
        db.session.commit()
        lesson_id = lesson.id

    res = client.get(f"/speaking/{lesson_id}")
    assert res.status_code == 200
    html = res.get_data(as_text=True)

    # Verify key speaking studio & recording components (Feature 4.6)
    assert "speakingVisualizerCanvas" in html
    assert "btnPlayUserSpeech" in html
    assert "Nghe lại bản thu" in html
    assert "recordingTimerText" in html
    assert "btnRecordSpeech" in html
    assert "btnPlayRefSpeech" in html
    assert "Can I have a medium iced latte" in html
