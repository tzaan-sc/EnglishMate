import json
import pytest
from tests.conftest import login
from app.extensions import db, limiter
from app.backend.learning.models import Lesson, Vocabulary, Question


def test_api_meta_and_health(client):
    """Kiểm tra các endpoint meta, health, ping của API v1."""
    # 1. Meta
    res_meta = client.get("/api/v1/meta")
    assert res_meta.status_code == 200
    data_meta = res_meta.get_json()
    assert data_meta["success"] is True
    assert data_meta["version"] == "v1.0.0"
    assert "endpoints" in data_meta

    # 2. Health
    res_health = client.get("/api/v1/health")
    assert res_health.status_code == 200
    data_health = res_health.get_json()
    assert data_health["success"] is True
    assert data_health["status"] == "healthy"

    # 3. Ping
    res_ping = client.get("/api/v1/ping")
    assert res_ping.status_code == 200
    data_ping = res_ping.get_json()
    assert data_ping["pong"] is True


def test_api_lessons_endpoints(client, app):
    """Kiểm tra API danh sách bài học và chi tiết bài học (/api/v1/lessons)."""
    with app.app_context():
        # Get list of lessons
        res_list = client.get("/api/v1/lessons")
        assert res_list.status_code == 200
        data_list = res_list.get_json()
        assert data_list["success"] is True
        assert len(data_list["data"]) >= 1
        assert "pagination" in data_list
        assert data_list["pagination"]["page"] == 1

        first_lesson = data_list["data"][0]
        lesson_id = first_lesson["id"]

        # Filter by level
        res_filtered = client.get(f"/api/v1/lessons?level={first_lesson['level']}")
        assert res_filtered.status_code == 200
        assert res_filtered.get_json()["success"] is True

        # Get detail of lesson
        res_detail = client.get(f"/api/v1/lessons/{lesson_id}")
        assert res_detail.status_code == 200
        data_detail = res_detail.get_json()
        assert data_detail["success"] is True
        assert data_detail["data"]["id"] == lesson_id
        assert data_detail["data"]["title"] == first_lesson["title"]

        # Non-existent lesson
        res_404 = client.get("/api/v1/lessons/999999")
        assert res_404.status_code == 404
        assert res_404.get_json()["success"] is False

        # Skills & Levels endpoints
        res_skills = client.get("/api/v1/lessons/skills")
        assert res_skills.status_code == 200
        assert isinstance(res_skills.get_json()["data"], list)

        res_levels = client.get("/api/v1/lessons/levels")
        assert res_levels.status_code == 200
        assert isinstance(res_levels.get_json()["data"], list)


def test_api_vocabulary_endpoints(client, app):
    """Kiểm tra API từ vựng (/api/v1/vocabulary)."""
    with app.app_context():
        # List vocab
        res_list = client.get("/api/v1/vocabulary")
        assert res_list.status_code == 200
        data_list = res_list.get_json()
        assert data_list["success"] is True
        assert len(data_list["data"]) >= 1
        assert "pagination" in data_list

        vocab_id = data_list["data"][0]["id"]

        # Detail vocab
        res_detail = client.get(f"/api/v1/vocabulary/{vocab_id}")
        assert res_detail.status_code == 200
        data_detail = res_detail.get_json()
        assert data_detail["success"] is True
        assert data_detail["data"]["id"] == vocab_id

        # Search vocab
        res_search = client.get("/api/v1/vocabulary?search=hello")
        assert res_search.status_code == 200
        assert res_search.get_json()["success"] is True

        # Topics
        res_topics = client.get("/api/v1/vocabulary/topics")
        assert res_topics.status_code == 200
        assert isinstance(res_topics.get_json()["data"], list)

        # Random vocab
        res_random = client.get("/api/v1/vocabulary/random?count=3")
        assert res_random.status_code == 200
        data_random = res_random.get_json()
        assert data_random["success"] is True
        assert len(data_random["data"]) >= 1


def test_api_quizzes_and_stats(client, app):
    """Kiểm tra API trắc nghiệm (/api/v1/quizzes) và thống kê (/api/v1/stats)."""
    with app.app_context():
        # Quizzes list
        res_quizzes = client.get("/api/v1/quizzes")
        assert res_quizzes.status_code == 200
        data_quizzes = res_quizzes.get_json()
        assert data_quizzes["success"] is True
        assert isinstance(data_quizzes["data"], list)

        # Questions list
        res_questions = client.get("/api/v1/quizzes/questions?limit=5&include_answers=true")
        assert res_questions.status_code == 200
        data_questions = res_questions.get_json()
        assert data_questions["success"] is True
        assert len(data_questions["data"]) >= 1
        assert "correct_option" in data_questions["data"][0]

        # Public stats
        res_stats = client.get("/api/v1/stats")
        assert res_stats.status_code == 200
        data_stats = res_stats.get_json()
        assert data_stats["success"] is True
        assert "total_lessons" in data_stats["data"]
        assert "total_vocabulary" in data_stats["data"]

        # User stats (unauthenticated)
        res_user_unauth = client.get("/api/v1/user/stats")
        assert res_user_unauth.status_code == 401

        # User stats (authenticated)
        login(client, "student@test.com", "user123")
        res_user_auth = client.get("/api/v1/user/stats")
        assert res_user_auth.status_code == 200
        data_user = res_user_auth.get_json()
        assert data_user["success"] is True
        assert data_user["data"]["username"] == "student"


def test_cors_support_on_api(client):
    """Kiểm tra hỗ trợ CORS (Cross-Origin Resource Sharing) trên các endpoint /api/v1/*."""
    # Preflight OPTIONS request
    res_options = client.options(
        "/api/v1/lessons",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Content-Type, Authorization",
        }
    )
    assert res_options.status_code in (200, 204)
    assert "Access-Control-Allow-Origin" in res_options.headers

    # GET request with Origin
    res_get = client.get(
        "/api/v1/meta",
        headers={"Origin": "http://localhost:3000"}
    )
    assert res_get.status_code == 200
    assert "Access-Control-Allow-Origin" in res_get.headers


def test_swagger_openapi_documentation(client):
    """Kiểm tra tài liệu API OpenAPI / Swagger UI (/api/v1/docs và /api/v1/apispec.json)."""
    # Swagger UI page
    res_docs = client.get("/api/v1/docs")
    assert res_docs.status_code in (200, 308, 301, 302)

    # Alias redirects
    res_alias = client.get("/apidocs", follow_redirects=False)
    assert res_alias.status_code in (301, 302, 308)

    res_alias2 = client.get("/api/docs", follow_redirects=False)
    assert res_alias2.status_code in (301, 302, 308)

    # OpenAPI Spec JSON
    res_spec = client.get("/api/v1/apispec.json")
    assert res_spec.status_code == 200
    spec_data = res_spec.get_json()
    assert "paths" in spec_data
    assert "info" in spec_data
    assert spec_data["info"]["title"] == "EnglishMate REST API"


def test_rate_limiting_enforcement():
    """Kiểm tra cơ chế Rate Limiting (Flask-Limiter) giới hạn số lượt gọi và trả về mã 429."""
    from app.config import Config
    from app import create_app
    from app.extensions import limiter

    class RateLimitTestConfig(Config):
        TESTING = True
        WTF_CSRF_ENABLED = False
        SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
        RATELIMIT_ENABLED = True
        RATELIMIT_DEFAULT = "2 per minute"

    test_app = create_app(RateLimitTestConfig)
    
    @test_app.route("/api/v1/test-limited-action")
    @limiter.limit("2 per minute")
    def test_limited_action():
        from flask import jsonify
        return jsonify({"success": True, "message": "OK"})

    with test_app.app_context():
        test_client = test_app.test_client()

        # First 2 requests should pass
        res1 = test_client.get("/api/v1/test-limited-action")
        assert res1.status_code == 200
        res2 = test_client.get("/api/v1/test-limited-action")
        assert res2.status_code == 200

        # 3rd request exceeds rate limit (429 Too Many Requests)
        res_429 = test_client.get("/api/v1/test-limited-action")
        assert res_429.status_code == 429
        data_429 = res_429.get_json()
        assert data_429["success"] is False
        assert data_429["error"] == "Too Many Requests"


