import pytest
from app.extensions import db
from app.backend.auth.models import User
from app.backend.learning.models import Lesson
from tests.conftest import login


def ensure_share_lesson():
    l = Lesson.query.filter_by(title="Lesson Sharing Demo").first()
    if not l:
        l = Lesson(
            title="Lesson Sharing Demo",
            level="B2",
            skill="Speaking",
            short_description="Bài học kiểm thử tính năng chia sẻ mạng xã hội và Web Share API.",
            content="Nội dung bài học luyện nói về Presentation Skills...",
            examples="Example dialogues...",
            is_active=True,
            view_count=12,
        )
        db.session.add(l)
        db.session.commit()
    return l


def test_lesson_detail_opengraph_meta_tags(client):
    """Test that lesson detail page outputs Open Graph and Twitter Card tags for social unfurling."""
    login(client)

    with client.application.app_context():
        lesson = ensure_share_lesson()
        lesson_id = lesson.id

    res = client.get(f"/lessons/{lesson_id}", follow_redirects=True)
    assert res.status_code == 200
    html = res.get_data(as_text=True)

    # Verify OpenGraph tags
    assert 'property="og:title"' in html
    assert "Lesson Sharing Demo" in html
    assert 'property="og:description"' in html
    assert 'property="og:type" content="article"' in html
    assert 'property="og:site_name" content="EnglishMate"' in html

    # Verify Twitter Cards
    assert 'name="twitter:card" content="summary_large_image"' in html
    assert 'name="twitter:title"' in html


def test_lesson_share_button_and_modal_markup(client):
    """Test that the lesson page contains the Share button and the rich social share modal."""
    login(client)

    with client.application.app_context():
        lesson = ensure_share_lesson()
        lesson_id = lesson.id

    res = client.get(f"/lessons/{lesson_id}", follow_redirects=True)
    assert res.status_code == 200
    html = res.get_data(as_text=True)

    # 1. Action bar Share button
    assert 'data-bs-target="#shareLessonModal"' in html
    assert "Chia sẻ" in html

    # 2. Share modal structure
    assert 'id="shareLessonModal"' in html
    assert "Chia sẻ Bài học" in html

    # 3. Social sharing channel buttons
    assert "shareSocialChannel('facebook')" in html
    assert "shareSocialChannel('zalo')" in html
    assert "shareSocialChannel('twitter')" in html
    assert "shareSocialChannel('linkedin')" in html
    assert "shareSocialChannel('telegram')" in html
    assert "shareSocialChannel('email')" in html

    # 4. Web Share API & Copy Link elements
    assert 'id="nativeWebShareBox"' in html
    assert 'onclick="shareNativeApp()"' in html
    assert 'id="shareUrlInput"' in html
    assert 'id="btnCopyShareLink"' in html
    assert 'onclick="copyShareUrl()"' in html
    assert 'id="copyAlert"' in html

    # 5. QR Code element
    assert 'id="qrCodeCollapseBox"' in html
    assert "api.qrserver.com" in html or "QR Code" in html
