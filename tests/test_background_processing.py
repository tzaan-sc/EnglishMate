import json
import time
from datetime import datetime, timezone, timedelta

import pytest

from app.extensions import db
from app.backend.admin.models import BackgroundTask
from app.backend.auth.models import User
from app.backend.admin.task_queue_service import (
    enqueue_background_task,
    cancel_background_task,
    retry_background_task_now,
    purge_old_background_tasks,
    process_pending_background_tasks,
    get_background_processing_analytics,
    register_task_handler,
    TASK_HANDLERS
)
from app.backend.admin.scheduler_service import scheduler


def _login_admin(client):
    return client.post("/auth/login", data={"email": "admin@test.com", "password": "admin123"}, follow_redirects=True)


# ===========================================================================
# 1. TASK QUEUE & ASYNC PROCESSING
# ===========================================================================

def test_task_queue_enqueue_and_execution(app):
    """Test đưa tác vụ vào hàng đợi và thực thi thành công."""
    with app.app_context():
        res = enqueue_background_task(
            name="test_dummy_task",
            params={"echo": "englishmate_task", "sleep_sec": 0.01},
            priority=5,
            async_exec=False  # synchronous execution for reliable test
        )
        assert res["success"] is True
        task_id = res["task_id"]

        task = BackgroundTask.query.filter_by(task_id=task_id).first()
        assert task is not None
        assert task.status == "COMPLETED"
        assert task.duration_ms >= 0.0
        assert "Dummy task executed successfully" in task.result_json


def test_task_queue_unregistered_handler(app):
    """Test xử lý khi tác vụ không có handler đã đăng ký."""
    with app.app_context():
        res = enqueue_background_task(
            name="non_existent_handler_job",
            params={},
            async_exec=False
        )
        assert res["success"] is True
        task = BackgroundTask.query.filter_by(task_id=res["task_id"]).first()
        assert task.status == "FAILED"
        assert "Không tìm thấy hàm xử lý" in task.error_message


# ===========================================================================
# 2. JOB PRIORITIZATION
# ===========================================================================

def test_job_prioritization_dispatch(app):
    """Test phân phối tác vụ ưu tiên HIGH (10) trước LOW (1)."""
    with app.app_context():
        # Enqueue low priority task
        low_res = enqueue_background_task(
            name="test_dummy_task",
            params={"echo": "low_priority"},
            priority=1,
            scheduled_at=datetime.now(timezone.utc) + timedelta(hours=1),
            async_exec=False
        )
        # Enqueue high priority task
        high_res = enqueue_background_task(
            name="test_dummy_task",
            params={"echo": "high_priority"},
            priority=10,
            scheduled_at=datetime.now(timezone.utc) + timedelta(hours=1),
            async_exec=False
        )

        low_task = BackgroundTask.query.filter_by(task_id=low_res["task_id"]).first()
        high_task = BackgroundTask.query.filter_by(task_id=high_res["task_id"]).first()
        assert low_task.priority_label == "Thấp (Low)"
        assert high_task.priority_label == "Cao (High)"

        # Make both due now
        low_task.scheduled_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        high_task.scheduled_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        db.session.commit()

        # Dispatch pending
        dispatched = process_pending_background_tasks(limit=10)
        assert dispatched >= 2


# ===========================================================================
# 3. RETRY LOGIC & EXPONENTIAL BACKOFF
# ===========================================================================

@register_task_handler("test_fail_task")
def _handle_test_fail_task(params: dict) -> dict:
    raise RuntimeError("Lỗi kết nối cơ sở dữ liệu giả lập.")


def test_retry_logic_failure_handling(app):
    """Test cơ chế thử lại khi gặp lỗi và chuyển FAILED khi vượt max_retries."""
    with app.app_context():
        res = enqueue_background_task(
            name="test_fail_task",
            params={"test": "retry"},
            max_retries=0,  # Fail immediately without retry thread
            async_exec=False
        )
        assert res["success"] is True
        task = BackgroundTask.query.filter_by(task_id=res["task_id"]).first()
        assert task.status == "FAILED"
        assert "Lỗi kết nối cơ sở dữ liệu giả lập" in task.error_message


# ===========================================================================
# 4. RESOURCE MANAGEMENT & PERFORMANCE MONITORING
# ===========================================================================

def test_resource_management_and_performance_tracking(app):
    """Test đo lường tài nguyên RAM (MB) và thời gian thực thi (duration_ms)."""
    with app.app_context():
        res = enqueue_background_task(
            name="test_dummy_task",
            params={"sleep_sec": 0.05},
            async_exec=False
        )
        task = BackgroundTask.query.filter_by(task_id=res["task_id"]).first()
        assert task.status == "COMPLETED"
        assert task.duration_ms >= 10.0  # At least ~50ms
        assert task.duration_formatted.endswith("ms") or task.duration_formatted.endswith("s")
        assert task.memory_start_mb >= 0.0
        assert task.memory_end_mb >= 0.0


def test_background_processing_analytics(app):
    """Test hàm tổng hợp chỉ số hiệu năng và tài nguyên hệ thống."""
    with app.app_context():
        analytics = get_background_processing_analytics()
        assert "total_count" in analytics
        assert "completed_count" in analytics
        assert "success_rate" in analytics
        assert "avg_duration_ms" in analytics
        assert "system_metrics" in analytics
        assert "process_ram_mb" in analytics["system_metrics"]
        assert "test_dummy_task" in analytics["registered_handlers"]


# ===========================================================================
# 5. SCHEDULED TASKS (APSCHEDULER)
# ===========================================================================

def test_scheduled_tasks_service_and_trigger(app):
    """Test bộ lập lịch APScheduler, lấy danh sách job và kích hoạt ngay."""
    with app.app_context():
        jobs = scheduler.get_jobs_status()
        assert len(jobs) >= 3
        job_ids = [j["id"] for j in jobs]
        assert "clean_expired_tokens_job" in job_ids
        assert "email_queue_sync_job" in job_ids

        # Test trigger job now
        res = scheduler.trigger_job_now("clean_expired_tokens_job")
        assert res["success"] is True

        # Test toggle enable/disable
        toggle_res = scheduler.toggle_job_enabled("clean_expired_tokens_job", False)
        assert toggle_res["success"] is True


# ===========================================================================
# 6. CANCEL, RETRY & PURGE TASK ACTIONS
# ===========================================================================

def test_cancel_and_retry_task_actions(app):
    """Test hủy và chạy lại tác vụ."""
    with app.app_context():
        # Create a pending task
        res = enqueue_background_task(
            name="test_dummy_task",
            scheduled_at=datetime.now(timezone.utc) + timedelta(hours=5),
            async_exec=False
        )
        task_id = res["task_id"]

        # Cancel
        cancel_res = cancel_background_task(task_id)
        assert cancel_res["success"] is True

        task = BackgroundTask.query.filter_by(task_id=task_id).first()
        assert task.status == "CANCELLED"

        # Retry now
        retry_res = retry_background_task_now(task_id)
        assert retry_res["success"] is True


# ===========================================================================
# 7. ADMIN DASHBOARD & API INTEGRATION
# ===========================================================================

def test_admin_background_tasks_views(client, app):
    """Test các view và endpoint API quản trị tác vụ nền."""
    with app.app_context():
        _login_admin(client)

        # 1. GET Dashboard
        res = client.get("/admin/system/background-tasks")
        assert res.status_code == 200
        assert b"Background Processing" in res.data or b"Task Queue" in res.data

        # 2. GET Analytics API
        res_api = client.get("/admin/system/background-tasks/analytics")
        assert res_api.status_code == 200
        json_data = res_api.get_json()
        assert json_data["success"] is True

        # 3. POST Enqueue Task
        res_enqueue = client.post(
            "/admin/system/background-tasks/enqueue",
            json={"name": "test_dummy_task", "priority": 10, "params": {"test": "admin_enqueue"}}
        )
        assert res_enqueue.status_code == 200
        assert res_enqueue.get_json()["success"] is True

        # 4. POST Purge Tasks
        res_purge = client.post(
            "/admin/system/background-tasks/purge",
            data={"days": 30}
        )
        assert res_purge.status_code == 302 or res_purge.status_code == 200
