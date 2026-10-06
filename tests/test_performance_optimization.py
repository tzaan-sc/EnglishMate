"""
Test Suite for Section 12.8: Performance Optimization.
Tests:
- Lazy Loading on images & avatars
- Flask-Compress Gzip/Brotli compression
- Gunicorn & Nginx load balancing configurations
- APM (Application Performance Monitoring) tracking, latency percentiles, and admin dashboard
"""

import pytest
import os
import json
from tests.conftest import login
from app.backend.admin.apm_service import APMMonitor, apm_monitor


def test_compression_extension_and_config(app, client):
    """Kiểm tra Flask-Compress đã được khởi tạo và cấu hình đúng MIME types."""
    assert "COMPRESS_MIMETYPES" in app.config
    assert "text/html" in app.config["COMPRESS_MIMETYPES"]
    assert "application/json" in app.config["COMPRESS_MIMETYPES"]
    assert app.config.get("COMPRESS_MIN_SIZE", 0) >= 500

    # Test request with Accept-Encoding: gzip
    res = client.get("/", headers={"Accept-Encoding": "gzip"})
    assert res.status_code in (200, 302)
    # Vary header should contain Accept-Encoding when compression is active
    vary_header = res.headers.get("Vary", "")
    assert "Accept-Encoding" in vary_header or res.status_code == 302


def test_gunicorn_load_balancing_configuration():
    """Kiểm tra file cấu hình gunicorn.conf.py và công thức tính toán workers."""
    config_path = os.path.join(os.path.dirname(__file__), "..", "gunicorn.conf.py")
    assert os.path.exists(config_path)

    with open(config_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert 'worker_class = "gthread"' in content
    assert "max_requests = 1000" in content
    assert "max_requests_jitter = 50" in content
    assert "workers = " in content
    assert 'proc_name = "englishmate_gunicorn"' in content


def test_nginx_load_balancer_configuration():
    """Kiểm tra file cấu hình deployment/nginx_load_balancer.conf."""
    nginx_conf = os.path.join(os.path.dirname(__file__), "..", "deployment", "nginx_load_balancer.conf")
    assert os.path.exists(nginx_conf)

    with open(nginx_conf, "r", encoding="utf-8") as f:
        content = f.read()

    assert "upstream englishmate_cluster" in content
    assert "least_conn;" in content
    assert "max_fails=3 fail_timeout=10s" in content
    assert "gzip on;" in content
    assert "proxy_pass http://englishmate_cluster;" in content


def test_apm_monitor_unit_service():
    """Kiểm tra dịch vụ APMMonitor tính toán p50, p90, p95, p99, slowest endpoints và status codes."""
    monitor = APMMonitor(max_history=100, slow_threshold_ms=300.0)

    # Simulate 50 requests
    for i in range(1, 51):
        lat = float(i * 10)  # 10ms to 500ms
        ep = "learning.lesson_detail" if i % 2 == 0 else "main.index"
        status = 200 if i <= 45 else 500
        monitor.record_request(
            endpoint=ep,
            path=f"/{ep.replace('.', '/')}",
            method="GET",
            status_code=status,
            duration_ms=lat,
            client_ip="192.168.1.1"
        )

    summary = monitor.get_summary()
    assert summary["total_requests"] == 50
    assert summary["total_errors"] == 5
    assert summary["error_rate_pct"] == 10.0
    assert summary["min_latency_ms"] == 10.0
    assert summary["max_latency_ms"] == 500.0
    assert summary["p50_latency_ms"] > 0
    assert summary["p95_latency_ms"] >= summary["p50_latency_ms"]
    assert summary["p99_latency_ms"] >= summary["p95_latency_ms"]

    # Slowest endpoints ranking
    slow_list = monitor.get_slowest_endpoints(limit=5)
    assert len(slow_list) == 2
    assert slow_list[0]["avg_ms"] > 0

    # Slow requests count (>300ms)
    assert summary["slow_requests_count"] > 0
    assert len(monitor.get_recent_slow_requests()) > 0

    # Reset
    monitor.reset_metrics()
    summary_reset = monitor.get_summary()
    assert summary_reset["total_requests"] == 0
    assert summary_reset["avg_latency_ms"] == 0.0


def test_lazy_loading_in_templates():
    """Kiểm tra các thẻ <img> trong templates được trang bị loading='lazy'."""
    sidebar_file = os.path.join(os.path.dirname(__file__), "..", "app", "frontend", "templates", "_sidebar.html")
    with open(sidebar_file, "r", encoding="utf-8") as f:
        content = f.read()
    assert 'loading="lazy"' in content
    assert 'decoding="async"' in content

    profile_file = os.path.join(os.path.dirname(__file__), "..", "app", "frontend", "templates", "main", "profile.html")
    with open(profile_file, "r", encoding="utf-8") as f:
        content = f.read()
    assert 'loading="lazy"' in content
    assert 'decoding="async"' in content


def test_apm_admin_routes_unauthenticated(client):
    """Kiểm tra chưa đăng nhập bị chuyển hướng đến trang login."""
    res = client.get("/admin/system/apm")
    assert res.status_code == 302
    assert "/auth/login" in res.headers["Location"]


def test_apm_admin_routes_learner_forbidden(client):
    """Kiểm tra học viên bình thường bị từ chối truy cập 403."""
    login(client, "student@test.com", "user123")
    res = client.get("/admin/system/apm")
    assert res.status_code == 403


def test_apm_admin_routes_admin_success(client):
    """Kiểm tra Admin truy cập thành công 200 OK."""
    login(client, "admin@test.com", "admin123")
    res = client.get("/admin/system/apm")
    assert res.status_code == 200
    assert b"APM" in res.data


def test_apm_metrics_api_and_export(client):
    """Kiểm tra API /admin/system/apm/api/metrics và xuất báo cáo JSON /export."""
    login(client, "admin@test.com", "admin123")

    # 1. Test Metrics API
    res = client.get("/admin/system/apm/api/metrics")
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert "summary" in data
    assert "slow_endpoints" in data

    # 2. Test Reset API
    res_reset = client.post("/admin/system/apm/api/reset", headers={"X-Requested-With": "XMLHttpRequest"})
    assert res_reset.status_code in (200, 302)

    # 3. Test Export Report
    res_exp = client.get("/admin/system/apm/export")
    assert res_exp.status_code == 200
    assert res_exp.content_type == "application/json"
    assert "attachment;filename=" in res_exp.headers.get("Content-Disposition", "")
    exp_data = json.loads(res_exp.data.decode("utf-8"))
    assert exp_data["report_type"] == "EnglishMate APM Performance Report"
