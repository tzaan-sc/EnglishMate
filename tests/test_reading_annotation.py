import pytest
from app.extensions import db
from app.backend.learning.models import Lesson, ReadingAnnotation
from app.backend.auth.models import User
from tests.conftest import login


def test_reading_annotation_model(app):
    """Test ReadingAnnotation model fields and to_dict method."""
    with app.app_context():
        user = User.query.filter_by(email="student@test.com").first()
        lesson = Lesson(
            title="Climate Change and Renewable Energy",
            level="B2",
            skill="Reading",
            short_description="An informative reading passage about climate change.",
            content="Solar and wind energy are rapidly expanding across the world.\nThey offer cleaner alternatives.",
            examples="Solar power|Năng lượng mặt trời",
            skill_data={"reading_genre": "Scientific Article"}
        )
        db.session.add(lesson)
        db.session.commit()

        ann = ReadingAnnotation(
            lesson_id=lesson.id,
            user_id=user.id,
            selected_text="rapidly expanding",
            note_content="Tăng trưởng nhanh chóng - Collocation hữu ích",
            paragraph_index=0,
            start_offset=27,
            end_offset=44,
            color="yellow"
        )
        db.session.add(ann)
        db.session.commit()

        saved = ReadingAnnotation.query.filter_by(selected_text="rapidly expanding").first()
        assert saved is not None
        assert saved.color == "yellow"
        assert saved.note_content == "Tăng trưởng nhanh chóng - Collocation hữu ích"

        d = saved.to_dict()
        assert d["id"] == saved.id
        assert d["selected_text"] == "rapidly expanding"
        assert d["color"] == "yellow"
        assert "created_at" in d


def test_reading_annotation_api_flow(client):
    """Test creating, retrieving, and deleting reading annotations via API."""
    login(client)

    with client.application.app_context():
        lesson = Lesson(
            title="Technology and Modern Society",
            level="C1",
            skill="Reading",
            short_description="Discussion on AI transformation.",
            content="Artificial intelligence is transforming every sector.\nEthics must remain at the forefront.",
            examples="Artificial intelligence|Trí tuệ nhân tạo",
            skill_data={"reading_genre": "Tech Essay"}
        )
        db.session.add(lesson)
        db.session.commit()
        lesson_id = lesson.id

    # 1. Create annotation via POST
    res_post = client.post(
        f"/lessons/{lesson_id}/annotations",
        json={
            "selected_text": "transforming every sector",
            "note_content": "Cụm từ biểu đạt sự thay đổi toàn diện",
            "paragraph_index": 0,
            "start_offset": 27,
            "end_offset": 52,
            "color": "green"
        }
    )
    assert res_post.status_code == 201
    post_data = res_post.get_json()
    assert post_data["status"] == "success"
    ann_id = post_data["annotation"]["id"]
    assert post_data["annotation"]["color"] == "green"

    # 2. Get annotations list via GET
    res_get = client.get(f"/lessons/{lesson_id}/annotations")
    assert res_get.status_code == 200
    get_data = res_get.get_json()
    assert get_data["status"] == "success"
    assert len(get_data["annotations"]) >= 1
    assert any(a["id"] == ann_id for a in get_data["annotations"])

    # 3. View reading lesson page
    res_page = client.get(f"/reading/{lesson_id}")
    assert res_page.status_code == 200
    html = res_page.get_data(as_text=True)
    assert "transforming every sector" in html
    assert "annotationSelectionToolbar" in html
    assert "annotationEditorPopover" in html

    # 4. Delete annotation via DELETE
    res_del = client.delete(f"/lessons/{lesson_id}/annotations/{ann_id}")
    assert res_del.status_code == 200
    del_data = res_del.get_json()
    assert del_data["status"] == "success"

    # Verify deleted
    with client.application.app_context():
        deleted = ReadingAnnotation.query.filter_by(id=ann_id).first()
        assert deleted is None
