"""
Test Suite for Section 12.9: Monitoring & Logging.
Tests:
- Slow Query Performance Logging (>500ms)
- Server Resource Monitoring (CPU, RAM, Disk, Network, Process)
- Real-time Alert System (Telegram, Discord, Slack Webhooks, Cooldown)
- Log Analysis, Search, Filter, Rotation (.gz) & Retention Cleanup
- Admin Monitoring Dashboard & REST APIs
"""

import pytest
import os
import json
from datetime import datetime, timedelta
from tests.conftest import login
from app.backend.admin.slow_query_logger import SlowQueryMonitor, slow_query_monitor
from app.backend.admin.system_monitor_service import SystemMonitorService, system_monitor
from app.backend.admin.alert_service import AlertService, alert_service
from app.backend.admin.log_analysis_service import LogAnalysisService, log_analysis_service


def test_slow_query_monitor_service(app):
    """Kiểm tra dịch vụ SlowQueryMonitor ghi nhận, phân tích mẫu SQL và đặt lại dữ liệu."""
    monitor = SlowQueryMonitor(max_history=50, default_threshold_ms=300.0)

    # 1. Ghi 10 câu truy vấn chậm
    for i in range(1, 11):
        sql = f"SELECT * FROM vocabulary WHERE topic = 'Topic_{i % 3}' AND id > {i * 10}"
        monitor.record_slow_query(
            statement=sql,
            duration_ms=400.0 + (i * 20),
            parameters=[i],
            context="TestRunner"
        )

    summary = monitor.get_summary()
    assert summary["total_slow_queries"] == 10
    assert summary["max_query_ms"] >= 600.0
    assert summary["avg_query_ms"] >= 400.0
    assert summary["distinct_slow_templates"] >= 1

    # Top templates
    top_templates = monitor.get_top_slow_templates(limit=5)
    assert len(top_templates) >= 1
    assert "vocabulary" in top_templates[0]["template"].lower()
    assert top_templates[0]["count"] == 10

    # Recent queries
    recent = monitor.get_recent_slow_queries(limit=5)
    assert len(recent) == 5

    # Reset
    monitor.reset_metrics()
    summary_reset = monitor.get_summary()
    assert summary_reset["total_slow_queries"] == 0
    assert summary_reset["avg_query_ms"] == 0.0


def test_system_resource_monitoring_service():
    """Kiểm tra dịch vụ giám sát tài nguyên máy chủ psutil (CPU, RAM, Disk, Network, Process)."""
    metrics = system_monitor.get_complete_system_metrics()
    assert "cpu" in metrics
    assert "ram" in metrics
    assert "disk" in metrics
    assert "network" in metrics
    assert "process" in metrics
    assert "history" in metrics

    # Verify numerical ranges
    assert 0.0 <= metrics["cpu"]["percent"] <= 100.0
    assert 0.0 <= metrics["ram"]["percent"] <= 100.0
    assert metrics["ram"]["total_mb"] > 0
    assert metrics["process"]["pid"] > 0
    assert len(metrics["history"]["cpu"]) >= 1


def test_alert_service_config_and_cooldown(app):
    """Kiểm tra cấu hình kênh cảnh báo bot và cơ chế chống spam (Cooldown)."""
    with app.app_context():
        # 1. Lưu cấu hình cảnh báo
        AlertService.save_alert_config({
            "enabled": True,
            "channels": "telegram",
            "min_severity": "CRITICAL",
            "cooldown_seconds": 30,
            "telegram_bot_token": "123456:TEST_TOKEN",
            "telegram_chat_id": "-100123456789",
        })

        config = AlertService.get_alert_config()
        assert config["enabled"] is True
        assert config["channels"] == "telegram"
        assert config["telegram"]["configured"] is True
        assert config["cooldown_seconds"] == 30

        # 2. Test Alert Trigger (mock test)
        res = AlertService.send_test_alert(channel="telegram", custom_message="Test alert verification")
        assert "telegram" in res["results"]


def test_log_analysis_search_rotation_and_cleanup(app):
    """Kiểm tra đọc, tìm kiếm log theo bộ lọc, xoay vòng nén tệp .gz và dọn dẹp log quá hạn."""
    log_dir = log_analysis_service.get_log_directory()
    test_log_file = os.path.join(log_dir, "test_app.log")

    # 1. Tạo tệp log giả lập
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(test_log_file, "w", encoding="utf-8") as f:
        f.write(f"[{now_str}] [INFO] [AppInit] EnglishMate server starting up\n")
        f.write(f"[{now_str}] [WARNING] [AuthService] High failed login attempts for user mai\n")
        f.write(f"[{now_str}] [ERROR] [PaymentService] Gateway timeout connecting to Stripe API\n")
        f.write(f"[{now_str}] [CRITICAL] [Database] Connection pool exhausted error\n")

    # 2. Tìm kiếm log với bộ lọc Level
    res_err = log_analysis_service.search_and_analyze_logs(
        filename="test_app.log",
        level="ERROR",
        limit=50
    )
    assert res_err["matching_count"] >= 1
    assert any("Stripe API" in e["message"] for e in res_err["entries"])

    # 3. Tìm kiếm theo từ khóa
    res_kw = log_analysis_service.search_and_analyze_logs(
        filename="test_app.log",
        level="ALL",
        keyword="Gateway timeout",
        limit=50
    )
    assert res_kw["matching_count"] == 1

    # 4. Thử nghiệm Xoay vòng & Nén tệp log (.gz)
    rot_res = log_analysis_service.rotate_log_file("test_app.log")
    assert rot_res["success"] is True
    assert os.path.exists(rot_res["archive_path"])

    # 5. Dọn dẹp log cũ
    clean_res = log_analysis_service.cleanup_expired_log_archives(retention_days=0)
    assert clean_res["success"] is True
    assert clean_res["deleted_count"] >= 1

    # Dọn dẹp tệp test
    if os.path.exists(test_log_file):
        os.remove(test_log_file)


def test_monitoring_admin_routes_unauthenticated(client):
    """Kiểm tra chưa đăng nhập bị chuyển hướng đến trang login."""
    res = client.get("/admin/system/monitoring")
    assert res.status_code == 302
    assert "/auth/login" in res.headers["Location"]


def test_monitoring_admin_routes_learner_forbidden(client):
    """Kiểm tra học viên bình thường bị từ chối 403."""
    login(client, "student@test.com", "user123")
    res = client.get("/admin/system/monitoring")
    assert res.status_code == 403


def test_monitoring_admin_routes_admin_success(client):
    """Kiểm tra Admin truy cập thành công 200 OK."""
    login(client, "admin@test.com", "admin123")
    res = client.get("/admin/system/monitoring")
    assert res.status_code == 200
    assert b"Monitoring" in res.data


def test_monitoring_admin_api_endpoints(client):
    """Kiểm tra các API REST của module Giám sát & Nhật ký."""
    login(client, "admin@test.com", "admin123")

    # 1. API Resources
    res_res = client.get("/admin/system/monitoring/api/resources")
    assert res_res.status_code == 200
    data_res = res_res.get_json()
    assert data_res["success"] is True
    assert "metrics" in data_res

    # 2. API Slow Queries
    res_sq = client.get("/admin/system/monitoring/api/slow-queries")
    assert res_sq.status_code == 200
    data_sq = res_sq.get_json()
    assert data_sq["success"] is True
    assert "summary" in data_sq

    # 3. API Reset Slow Queries
    res_reset = client.post("/admin/system/monitoring/api/slow-queries/reset", headers={"X-Requested-With": "XMLHttpRequest"})
    assert res_reset.status_code in (200, 302)

    # 4. API Search Logs
    res_logs = client.get("/admin/system/monitoring/api/logs?level=ALL")
    assert res_logs.status_code == 200
    data_logs = res_logs.get_json()
    assert data_logs["success"] is True

    # 5. API Update Alert Config
    res_alert = client.post(
        "/admin/system/monitoring/api/alerts/config",
        json={"enabled": True, "channels": "all", "cooldown_seconds": 60},
        headers={"X-Requested-With": "XMLHttpRequest"}
    )
    assert res_alert.status_code == 200

    # 6. Export Filtered Logs
    res_exp = client.get("/admin/system/monitoring/export-logs?level=ALL")
    assert res_exp.status_code == 200
    assert "text/plain" in res_exp.content_type
    assert "attachment;filename=" in res_exp.headers.get("Content-Disposition", "")
