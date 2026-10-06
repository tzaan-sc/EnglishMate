"""
Unit and Integration Tests for EnglishMate Distributed Caching System (Section 12.6)
Covers all 10 features:
1. Response Caching
2. Data Caching
3. Query Caching
4. Cache Invalidation
5. Cache Management (Admin UI & APIs)
6. Cache Statistics (Hits, Misses, Hit Rate %, Memory)
7. Cache Warming
8. Distributed Caching & Auto-Fallback
9. Cache Security & Namespacing
10. Cache Optimization (Zlib Compression)
"""

import time
import pytest
from flask import Flask, jsonify, request
from app import create_app
from app.config import TestConfig
from app.extensions import db, cache
from app.backend.auth.models import User
from app.backend.learning.models import Lesson, Vocabulary
from app.backend.admin.cache_service import (
    cache_service,
    cached_data,
    cached_response,
    cache_query,
    cache_get,
    cache_set,
    cache_delete,
    cache_has,
    invalidate_cache,
    invalidate_namespace,
    invalidate_leaderboard_cache,
    invalidate_vocab_cache,
    warm_up_cache,
    get_cache_statistics,
    get_cache_keys_list,
    stats_tracker,
)


@pytest.fixture
def test_app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        cache_service.flush_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(test_app):
    return test_app.test_client()


@pytest.fixture
def admin_user(test_app):
    with test_app.app_context():
        admin = User(
            username="cache_admin",
            email="cache_admin@example.com",
            role="ADMIN",
            xp=1500,
            current_streak=10
        )
        admin.set_password("AdminPass123!")
        db.session.add(admin)
        db.session.commit()
        return admin.id


# ===========================================================================
# 1. TEST CORE OPERATIONS & KEY NAMESPACING (Cache Security)
# ===========================================================================
def test_cache_set_get_and_security_namespacing(test_app):
    with test_app.app_context():
        # Set primitive & dict data
        cache_set("test_key", {"greeting": "Hello World"}, timeout=60, namespace="demo")
        
        # Verify Key exists and matches namespace
        assert cache_has("test_key", namespace="demo") is True
        assert cache_has("non_existent_key", namespace="demo") is False

        val = cache_get("test_key", namespace="demo")
        assert val == {"greeting": "Hello World"}

        # Verify key sanitization
        built_key = cache_service.build_key("demo_ns", "user@123:test/key")
        assert built_key.startswith("englishmate:v1:demo_ns:")
        assert "user@123:test/key" in built_key


# ===========================================================================
# 2. TEST COMPRESSION & OPTIMIZATION (>1KB)
# ===========================================================================
def test_cache_zlib_compression_optimization(test_app):
    with test_app.app_context():
        # Create a large payload > 1KB
        large_dict = {"items": [f"item_{i}_with_extra_long_padding_text_content" for i in range(100)]}
        
        cache_set("large_data", large_dict, timeout=120, namespace="data", compress=True)
        
        # Retrieve and verify decompression is seamless
        retrieved = cache_get("large_data", namespace="data")
        assert retrieved == large_dict
        assert len(retrieved["items"]) == 100

        # Check metadata tracker indicates compression
        keys = get_cache_keys_list(namespace="data")
        matching = [k for k in keys if "large_data" in k["key"]]
        assert len(matching) > 0
        assert matching[0]["is_compressed"] is True


# ===========================================================================
# 3. TEST DATA CACHING DECORATOR (@cached_data)
# ===========================================================================
def test_cached_data_decorator(test_app):
    with test_app.app_context():
        compute_counter = {"calls": 0}

        @cached_data(timeout=60, namespace="compute_test")
        def expensive_calculation(x, y):
            compute_counter["calls"] += 1
            return x * y + 42

        # First execution -> Computes
        res1 = expensive_calculation(10, 5)
        assert res1 == 92
        assert compute_counter["calls"] == 1

        # Second execution with same args -> Served from Cache (calls unchanged)
        res2 = expensive_calculation(10, 5)
        assert res2 == 92
        assert compute_counter["calls"] == 1

        # Different args -> Computes new result
        res3 = expensive_calculation(2, 3)
        assert res3 == 48
        assert compute_counter["calls"] == 2


# ===========================================================================
# 4. TEST QUERY CACHING (cache_query)
# ===========================================================================
def test_query_caching_helper(test_app):
    with test_app.app_context():
        query_executed = {"count": 0}

        def mock_db_query(topic_id=1, active_only=True):
            query_executed["count"] += 1
            return [{"id": 1, "title": "Vocabulary Unit 1", "active": active_only}]

        # First call -> Miss, executes fetch_fn
        data1 = cache_query("lessons", "get_units", mock_db_query, topic_id=1, active_only=True)
        assert len(data1) == 1
        assert query_executed["count"] == 1

        # Second call -> Hit, does not execute fetch_fn
        data2 = cache_query("lessons", "get_units", mock_db_query, topic_id=1, active_only=True)
        assert data2 == data1
        assert query_executed["count"] == 1


# ===========================================================================
# 5. TEST CACHE INVALIDATION (Single & Namespace)
# ===========================================================================
def test_cache_invalidation_single_and_namespace(test_app):
    with test_app.app_context():
        # Setup multiple keys across namespaces
        cache_set("vocab_1", {"word": "hello"}, namespace="vocab")
        cache_set("vocab_2", {"word": "world"}, namespace="vocab")
        cache_set("top_users", [{"id": 1, "xp": 100}], namespace="leaderboard")

        assert cache_has("vocab_1", namespace="vocab") is True
        assert cache_has("top_users", namespace="leaderboard") is True

        # Invalidate single key
        invalidate_cache("vocab_1", namespace="vocab")
        assert cache_has("vocab_1", namespace="vocab") is False
        assert cache_has("vocab_2", namespace="vocab") is True

        # Invalidate entire namespace
        deleted = invalidate_namespace("vocab")
        assert deleted >= 1
        assert cache_has("vocab_2", namespace="vocab") is False
        assert cache_has("top_users", namespace="leaderboard") is True  # Other namespace intact

        # Invalidate domain leaderboard
        invalidate_leaderboard_cache()
        assert cache_has("top_users", namespace="leaderboard") is False


# ===========================================================================
# 6. TEST CACHE STATISTICS TRACKER
# ===========================================================================
def test_cache_statistics_and_metrics(test_app):
    with test_app.app_context():
        cache_service.flush_all()

        # Generate some hits & misses
        cache_set("k1", "val1", namespace="test_stats")
        
        # 1 Hit
        v1 = cache_get("k1", namespace="test_stats")
        assert v1 == "val1"

        # 2 Misses
        v_missing1 = cache_get("non_existent_1", namespace="test_stats")
        v_missing2 = cache_get("non_existent_2", namespace="test_stats")
        assert v_missing1 is None and v_missing2 is None

        stats = get_cache_statistics()
        assert stats["hits"] >= 1
        assert stats["misses"] >= 2
        assert stats["total_requests"] >= 3
        assert 0.0 < stats["hit_rate_pct"] < 100.0
        assert stats["backend"] in ("SimpleCache", "Redis", "NullCache")
        assert stats["status"] in ("ONLINE", "DEGRADED_FALLBACK")


# ===========================================================================
# 7. TEST CACHE WARMING
# ===========================================================================
def test_cache_warming_engine(test_app):
    with test_app.app_context():
        # Populate a sample user and lesson
        u = User(username="learner1", email="learner1@example.com", xp=500, role="STUDENT")
        u.set_password("Pass123!")
        l = Lesson(title="Greetings", level="A1", skill="Speaking", short_description="Sample", content="Sample content", examples="Example")
        db.session.add_all([u, l])
        db.session.commit()

        # Run warm_up_cache
        res = warm_up_cache()
        assert res["success"] is True
        assert res["warmed_items_count"] >= 2
        assert "leaderboard:top_50_xp" in res["warmed_items"]
        assert "vocab:categories_catalog" in res["warmed_items"]

        # Check warmed data is in cache
        cached_top = cache_get("top_50_xp", namespace="leaderboard")
        assert cached_top is not None
        assert len(cached_top) >= 1
        assert cached_top[0]["username"] == "learner1"


# ===========================================================================
# 8. TEST RESPONSE CACHING (HTTP Headers X-Cache: MISS / HIT)
# ===========================================================================
def test_response_caching_endpoint(test_app, client):
    # Test on /api/v1/meta
    res1 = client.get("/api/v1/meta")
    assert res1.status_code == 200
    assert res1.headers.get("X-Cache") == "MISS"

    # Second GET request -> Cache HIT
    res2 = client.get("/api/v1/meta")
    assert res2.status_code == 200
    assert res2.headers.get("X-Cache") == "HIT"
    assert res2.json["version"] == "v1.0.0"


# ===========================================================================
# 9. TEST ADMIN CACHE MANAGEMENT UI & APIS
# ===========================================================================
def test_admin_cache_dashboard_and_actions(test_app, client, admin_user):
    with client.session_transaction() as sess:
        sess["_user_id"] = str(admin_user)
        sess["_fresh"] = True

    # 1. View Dashboard
    res = client.get("/admin/system/cache")
    assert res.status_code == 200
    assert "Quản trị Bộ nhớ Cache" in res.get_data(as_text=True)

    # 2. Get Stats API
    res_stats = client.get("/admin/system/cache/api/stats")
    assert res_stats.status_code == 200
    assert "hit_rate_pct" in res_stats.json

    # 3. Get Keys API
    res_keys = client.get("/admin/system/cache/api/keys")
    assert res_keys.status_code == 200
    assert "keys" in res_keys.json

    # 4. Invalidate Namespace API
    res_inv = client.post(
        "/admin/system/cache/invalidate-namespace",
        json={"namespace": "vocab"}
    )
    assert res_inv.status_code == 200
    assert res_inv.json["success"] is True

    # 5. Flush All API
    res_flush = client.post("/admin/system/cache/flush", json={})
    assert res_flush.status_code == 200
    assert res_flush.json["success"] is True

    # 6. Warm Cache API
    res_warm = client.post("/admin/system/cache/warm", json={})
    assert res_warm.status_code == 200
    assert res_warm.json["success"] is True
