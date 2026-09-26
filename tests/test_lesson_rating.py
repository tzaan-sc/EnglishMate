import pytest
from app.extensions import db
from app.backend.auth.models import User
from app.backend.learning.models import Lesson, LessonRating
from tests.conftest import login


def ensure_rating_lesson():
    l = Lesson.query.filter_by(title="Lesson Rating Demo").first()
    if not l:
        l = Lesson(
            title="Lesson Rating Demo",
            level="B1",
            skill="Listening",
            short_description="Bài học kiểm thử đánh giá chấm sao.",
            content="Nội dung bài học nghe chi tiết...",
            examples="Dialogue for listening...",
            is_active=True,
            view_count=5,
        )
        db.session.add(l)
        db.session.commit()
    return l


def test_rate_lesson_model_and_properties(client):
    with client.application.app_context():
        lesson = ensure_rating_lesson()
        user1 = User.query.filter_by(email="student@test.com").first()
        user2 = User.query.filter_by(email="admin@test.com").first()

        # Clean existing ratings for this test lesson
        LessonRating.query.filter_by(lesson_id=lesson.id).delete()
        db.session.commit()

        # Initially zero ratings
        assert lesson.average_rating == 0.0
        assert lesson.ratings_count == 0

        # Add first rating
        r1 = LessonRating(user_id=user1.id, lesson_id=lesson.id, rating=5, review_text="Bài học rất hay và dễ hiểu!")
        db.session.add(r1)
        db.session.commit()

        assert lesson.ratings_count == 1
        assert lesson.average_rating == 5.0

        # Add second rating
        r2 = LessonRating(user_id=user2.id, lesson_id=lesson.id, rating=4, review_text="Tốt nhưng cần thêm bài tập.")
        db.session.add(r2)
        db.session.commit()

        assert lesson.ratings_count == 2
        assert lesson.average_rating == 4.5

        dist = lesson.get_rating_distribution()
        assert dist["total"] == 2
        assert dist["counts"][5] == 1
        assert dist["counts"][4] == 1
        assert dist["percentages"][5] == 50
        assert dist["percentages"][4] == 50


def test_post_rate_lesson_ajax(client):
    login(client)

    with client.application.app_context():
        lesson = ensure_rating_lesson()
        lesson_id = lesson.id
        user = User.query.filter_by(email="student@test.com").first()
        LessonRating.query.filter_by(lesson_id=lesson_id, user_id=user.id).delete()
        db.session.commit()

    # Submit 5 stars rating via JSON AJAX
    res = client.post(
        f"/lessons/{lesson_id}/rate",
        json={"rating": 5, "review_text": "Phát âm rõ ràng, bài giảng tuyệt vời!"},
        headers={"X-Requested-With": "XMLHttpRequest"}
    )
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert data["rating"]["rating"] == 5
    assert "tuyệt vời" in data["rating"]["review_text"]
    assert data["average_rating"] >= 4.0
    assert data["ratings_count"] >= 1

    # Verify saved in database
    with client.application.app_context():
        user = User.query.filter_by(email="student@test.com").first()
        record = LessonRating.query.filter_by(user_id=user.id, lesson_id=lesson_id).first()
        assert record is not None
        assert record.rating == 5
        assert "Phát âm rõ ràng" in record.review_text


def test_update_existing_rating_ajax(client):
    login(client)

    with client.application.app_context():
        lesson = ensure_rating_lesson()
        lesson_id = lesson.id
        user = User.query.filter_by(email="student@test.com").first()
        # Seed an initial 5-star rating
        initial_rating = LessonRating.query.filter_by(user_id=user.id, lesson_id=lesson_id).first()
        if not initial_rating:
            initial_rating = LessonRating(user_id=user.id, lesson_id=lesson_id, rating=5, review_text="Bài hay ban đầu.")
            db.session.add(initial_rating)
            db.session.commit()

    # Update rating to 4 stars
    res = client.post(
        f"/lessons/{lesson_id}/rate",
        json={"rating": 4, "review_text": "Đã cập nhật: chấm 4 sao sau khi làm bài tập."},
        headers={"X-Requested-With": "XMLHttpRequest"}
    )
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert data["rating"]["rating"] == 4
    assert "Đã cập nhật đánh giá" in data["message"]

    with client.application.app_context():
        user = User.query.filter_by(email="student@test.com").first()
        records = LessonRating.query.filter_by(user_id=user.id, lesson_id=lesson_id).all()
        assert len(records) == 1
        assert records[0].rating == 4


def test_rate_lesson_invalid_rating(client):
    login(client)

    with client.application.app_context():
        lesson = ensure_rating_lesson()
        lesson_id = lesson.id

    # Test invalid values: 0, 6, string
    for invalid_val in [0, 6, "invalid"]:
        res = client.post(
            f"/lessons/{lesson_id}/rate",
            json={"rating": invalid_val, "review_text": "Test"},
            headers={"X-Requested-With": "XMLHttpRequest"}
        )
        assert res.status_code == 400
        data = res.get_json()
        assert data["success"] is False
        assert "từ 1 đến 5 sao" in data["message"]


def test_get_lesson_ratings_endpoint(client):
    login(client)

    with client.application.app_context():
        lesson = ensure_rating_lesson()
        lesson_id = lesson.id

    res = client.get(f"/lessons/{lesson_id}/ratings")
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert "ratings" in data
    assert "average_rating" in data
    assert "distribution" in data
