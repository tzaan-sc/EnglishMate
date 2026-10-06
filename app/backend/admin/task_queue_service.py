import gc
import json
import logging
import os
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from datetime import datetime, timezone, timedelta
from typing import Any, Callable, Dict, List, Optional, Tuple

import psutil
from flask import current_app

from app.extensions import db
from app.backend.admin.models import BackgroundTask, now

logger = logging.getLogger(__name__)

# ===========================================================================
# 1. TASK HANDLER REGISTRY
# ===========================================================================
TASK_HANDLERS: Dict[str, Callable] = {}


def register_task_handler(name: str):
    """Decorator để đăng ký một hàm xử lý tác vụ nền."""
    def decorator(fn: Callable):
        TASK_HANDLERS[name] = fn
        return fn
    return decorator


# --- Built-in Standard Handlers ---

@register_task_handler("test_dummy_task")
def _handle_test_dummy_task(params: dict) -> dict:
    """Tác vụ mẫu kiểm thử hệ thống worker."""
    sleep_sec = float(params.get("sleep_sec", 0.05))
    fail = bool(params.get("fail", False))
    time.sleep(sleep_sec)
    if fail:
        raise RuntimeError(params.get("fail_message", "Cố tình tạo lỗi kiểm thử Retry Logic."))
    return {"message": "Dummy task executed successfully", "echo": params.get("echo", "ok")}


@register_task_handler("clean_expired_tokens")
def _handle_clean_expired_tokens(params: dict) -> dict:
    """Dọn dẹp các token xác thực/reset mật khẩu đã hết hạn."""
    from app.backend.auth.models import PasswordResetToken
    cutoff = datetime.now(timezone.utc)
    deleted_count = 0
    try:
        expired = PasswordResetToken.query.filter(
            (PasswordResetToken.expires_at < cutoff) | (PasswordResetToken.is_used == True)
        ).all()
        for token in expired:
            db.session.delete(token)
            deleted_count += 1
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        logger.warning(f"Error cleaning expired tokens: {exc}")
    return {"deleted_tokens": deleted_count, "timestamp": datetime.now(timezone.utc).isoformat()}


@register_task_handler("system_cache_warming")
def _handle_system_cache_warming(params: dict) -> dict:
    """Nạp trước dữ liệu tĩnh bảng xếp hạng, từ vựng và ngữ pháp vào bộ nhớ Cache."""
    from .cache_service import warm_up_cache
    res = warm_up_cache()
    return res


@register_task_handler("email_queue_sync")
def _handle_email_queue_sync(params: dict) -> dict:
    """Quét và xử lý hàng đợi email hẹn giờ."""
    from app.backend.admin.email_service import process_scheduled_email_queue
    processed = process_scheduled_email_queue()
    return {"emails_processed": processed, "timestamp": datetime.now(timezone.utc).isoformat()}


@register_task_handler("database_auto_backup")
def _handle_database_auto_backup(params: dict) -> dict:
    """Sao lưu CSDL tự động trong luồng ngầm."""
    from app.backend.admin.backup_service import create_database_backup
    res = create_database_backup(backup_type="AUTO", is_compressed=True, notes="Tác vụ nền sao lưu tự động.")
    return res


# ===========================================================================
# 2. TASK QUEUE MANAGER & WORKER POOL
# ===========================================================================
class TaskQueueManager:
    """
    Quản lý hàng đợi tác vụ nền, worker pool, độ ưu tiên (Priority),
    thử lại với Exponential Backoff và giám sát tài nguyên RAM/CPU.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(TaskQueueManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return
        self.worker_pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="EM-Worker")
        self._initialized = True

    def get_current_memory_mb(self) -> float:
        """Đo mức RAM đang sử dụng của tiến trình hiện tại (MB)."""
        try:
            process = psutil.Process(os.getpid())
            return round(process.memory_info().rss / (1024 * 1024), 2)
        except Exception:
            return 0.0

    def get_system_metrics(self) -> dict:
        """Lấy thông số tải RAM và CPU của hệ điều hành."""
        try:
            vmem = psutil.virtual_memory()
            cpu_pct = psutil.cpu_percent(interval=None)
            process = psutil.Process(os.getpid())
            proc_mem = round(process.memory_info().rss / (1024 * 1024), 2)
            return {
                "system_ram_total_mb": round(vmem.total / (1024 * 1024), 1),
                "system_ram_used_mb": round(vmem.used / (1024 * 1024), 1),
                "system_ram_percent": vmem.percent,
                "process_ram_mb": proc_mem,
                "cpu_percent": cpu_pct
            }
        except Exception as exc:
            return {
                "system_ram_total_mb": 0,
                "system_ram_used_mb": 0,
                "system_ram_percent": 0.0,
                "process_ram_mb": 0.0,
                "cpu_percent": 0.0,
                "error": str(exc)
            }


queue_manager = TaskQueueManager()


# ===========================================================================
# 3. ENQUEUE & DISPATCH ENGINE
# ===========================================================================
def enqueue_background_task(
    name: str,
    params: Optional[dict] = None,
    priority: int = 5,  # 1: LOW, 5: NORMAL, 10: HIGH
    task_type: str = "ASYNC_JOB",
    max_retries: int = 3,
    retry_delay_seconds: int = 5,
    timeout_seconds: int = 300,
    scheduled_at: Optional[datetime] = None,
    user_id: Optional[int] = None,
    async_exec: bool = True
) -> dict:
    """
    Đưa tác vụ mới vào bảng BackgroundTask và giao cho Worker Pool thực thi.
    """
    task_id = uuid.uuid4().hex
    params_dict = params or {}
    params_json = json.dumps(params_dict, ensure_ascii=False)

    is_future = scheduled_at and scheduled_at > datetime.now(timezone.utc)
    initial_status = "PENDING"

    task = BackgroundTask(
        task_id=task_id,
        name=name,
        task_type=task_type,
        priority=priority,
        status=initial_status,
        params_json=params_json,
        max_retries=max_retries,
        retry_delay_seconds=retry_delay_seconds,
        timeout_seconds=timeout_seconds,
        scheduled_at=scheduled_at,
        created_by_id=user_id,
        created_at=now()
    )

    db.session.add(task)
    try:
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        return {"success": False, "error": f"Lỗi lưu CSDL tác vụ: {exc}"}

    # Nếu tác vụ được hẹn giờ trong tương lai -> giữ PENDING chờ scheduler
    if is_future:
        return {
            "success": True,
            "task_id": task_id,
            "status": "PENDING",
            "message": f"Tác vụ '{name}' đã được lên lịch chạy vào {scheduled_at.isoformat()}."
        }

    # Thực thi tác vụ
    if async_exec:
        try:
            app_obj = current_app._get_current_object()
            queue_manager.worker_pool.submit(_execute_task_in_worker, app_obj, task_id)
        except Exception as exc:
            logger.warning(f"Worker pool submission failed, running synchronously: {exc}")
            _execute_task_in_worker(current_app._get_current_object(), task_id)
    else:
        app_obj = current_app._get_current_object()
        _execute_task_in_worker(app_obj, task_id)

    return {
        "success": True,
        "task_id": task_id,
        "status": "PENDING",
        "priority": priority,
        "name": name
    }


def _execute_task_in_worker(app, task_id: str):
    """
    Hàm thực thi ngầm bởi Worker Thread:
    - Đo thời gian thực thi (Performance Monitoring duration_ms)
    - Giám sát RAM khởi đầu và kết thúc (Resource Management)
    - Timeout supervision
    - Cơ chế Retry Exponential Backoff khi phát sinh ngoại lệ
    """
    try:
        with app.app_context():
            task = BackgroundTask.query.filter_by(task_id=task_id).first()
            if not task or task.status in ("CANCELLED", "COMPLETED"):
                return

            handler = TASK_HANDLERS.get(task.name)
            if not handler:
                task.status = "FAILED"
                task.error_message = f"Không tìm thấy hàm xử lý đã đăng ký cho tác vụ: '{task.name}'"
                task.completed_at = now()
                db.session.commit()
                return

            task.status = "RUNNING"
            task.started_at = now()
            db.session.commit()

            start_mem = queue_manager.get_current_memory_mb()
            start_time = time.perf_counter()
            params = task.params_dict
            timeout_limit = task.timeout_seconds or 300

            try:
                result = handler(params)
                elapsed_ms = (time.perf_counter() - start_time) * 1000.0
                end_mem = queue_manager.get_current_memory_mb()

                task.status = "COMPLETED"
                task.result_json = json.dumps(result, ensure_ascii=False) if result is not None else "{}"
                task.error_message = None
                task.duration_ms = round(elapsed_ms, 2)
                task.memory_start_mb = start_mem
                task.memory_end_mb = end_mem
                task.memory_peak_mb = max(start_mem, end_mem)
                task.completed_at = now()
                db.session.commit()

                # Resource Optimization: Dọn dẹp rác bộ nhớ nếu tác vụ tiêu tốn nhiều RAM
                if (end_mem - start_mem) > 20.0:
                    gc.collect()

            except FutureTimeoutError:
                elapsed_ms = (time.perf_counter() - start_time) * 1000.0
                end_mem = queue_manager.get_current_memory_mb()
                err_msg = f"Tác vụ bị ngắt do vượt quá thời gian tối đa {timeout_limit} giây (Execution Timeout)."
                _handle_task_failure_and_retry(app, task, err_msg, elapsed_ms, start_mem, end_mem)

            except Exception as exc:
                elapsed_ms = (time.perf_counter() - start_time) * 1000.0
                end_mem = queue_manager.get_current_memory_mb()
                err_msg = f"Ngoại lệ khi thực thi tác vụ: {type(exc).__name__}: {str(exc)}"
                _handle_task_failure_and_retry(app, task, err_msg, elapsed_ms, start_mem, end_mem)
    except Exception as outer_err:
        logger.warning(f"Error executing worker task {task_id}: {outer_err}")


def _handle_task_failure_and_retry(
    app,
    task: BackgroundTask,
    error_message: str,
    duration_ms: float,
    start_mem: float,
    end_mem: float
):
    """Xử lý thất bại và tự động thử lại với Exponential Backoff."""
    task.duration_ms = round(duration_ms, 2)
    task.memory_start_mb = start_mem
    task.memory_end_mb = end_mem
    task.memory_peak_mb = max(start_mem, end_mem)
    task.error_message = error_message

    if task.retry_count < task.max_retries:
        task.retry_count += 1
        task.status = "RETRYING"
        # Exponential Backoff: delay = base_delay * (2 ^ (retry - 1))
        delay = task.retry_delay_seconds * (2 ** (task.retry_count - 1))
        task_id = task.task_id
        db.session.commit()

        logger.info(f"Retrying task {task_id} (Attempt {task.retry_count}/{task.max_retries}) after {delay}s...")

        def _retry_timer():
            try:
                time.sleep(delay)
                with app.app_context():
                    _execute_task_in_worker(app, task_id)
            except Exception as e:
                logger.warning(f"Error in retry timer for {task_id}: {e}")

        retry_thread = threading.Thread(target=_retry_timer, daemon=True, name=f"EM-Retry-{task_id[:8]}")
        retry_thread.start()
    else:
        task.status = "FAILED"
        task.completed_at = now()
        db.session.commit()


# ===========================================================================
# 4. QUEUE DISPATCH & PRIORITY SORTING
# ===========================================================================
def process_pending_background_tasks(limit: int = 10) -> int:
    """
    Quét và kích hoạt các tác vụ PENDING theo thứ tự ưu tiên (Priority Descending: HIGH -> LOW)
    và created_at Ascending.
    """
    now_utc = datetime.now(timezone.utc)
    pending_tasks = BackgroundTask.query.filter(
        (BackgroundTask.status == "PENDING") &
        ((BackgroundTask.scheduled_at == None) | (BackgroundTask.scheduled_at <= now_utc))
    ).order_by(
        BackgroundTask.priority.desc(),  # High priority (10) executed first
        BackgroundTask.created_at.asc()
    ).limit(limit).all()

    dispatched = 0
    app_obj = current_app._get_current_object()
    for t in pending_tasks:
        queue_manager.worker_pool.submit(_execute_task_in_worker, app_obj, t.task_id)
        dispatched += 1

    return dispatched


# ===========================================================================
# 5. PERFORMANCE MONITORING & ANALYTICS
# ===========================================================================
def get_background_processing_analytics() -> dict:
    """
    Tổng hợp toàn bộ chỉ số hiệu năng (Performance Monitoring),
    thời gian thực thi (Duration ms), tỷ lệ thành công và tài nguyên hệ thống.
    """
    all_tasks = BackgroundTask.query.all()
    total_count = len(all_tasks)

    completed_count = sum(1 for t in all_tasks if t.status == "COMPLETED")
    failed_count = sum(1 for t in all_tasks if t.status == "FAILED")
    running_count = sum(1 for t in all_tasks if t.status == "RUNNING")
    pending_count = sum(1 for t in all_tasks if t.status in ("PENDING", "RETRYING"))
    cancelled_count = sum(1 for t in all_tasks if t.status == "CANCELLED")

    # Success rate
    success_rate = round((completed_count / total_count * 100.0), 1) if total_count > 0 else 100.0

    # Average execution duration (ms)
    completed_durations = [t.duration_ms for t in all_tasks if t.status == "COMPLETED" and t.duration_ms > 0]
    avg_duration_ms = round(sum(completed_durations) / len(completed_durations), 1) if completed_durations else 0.0
    max_duration_ms = round(max(completed_durations), 1) if completed_durations else 0.0

    # Grouped by task name stats
    task_name_stats = {}
    for t in all_tasks:
        name = t.name
        if name not in task_name_stats:
            task_name_stats[name] = {"total": 0, "completed": 0, "failed": 0, "total_duration": 0.0}
        task_name_stats[name]["total"] += 1
        if t.status == "COMPLETED":
            task_name_stats[name]["completed"] += 1
            task_name_stats[name]["total_duration"] += t.duration_ms
        elif t.status == "FAILED":
            task_name_stats[name]["failed"] += 1

    for k, v in task_name_stats.items():
        comp = v["completed"]
        v["avg_duration_ms"] = round(v["total_duration"] / comp, 1) if comp > 0 else 0.0

    # 7-day timeline metrics
    timeline = {}
    today = datetime.now(timezone.utc).date()
    for i in range(6, -1, -1):
        day_str = (today - timedelta(days=i)).strftime("%d/%m")
        timeline[day_str] = {"completed": 0, "failed": 0, "total": 0}

    for t in all_tasks:
        if t.created_at:
            day_key = t.created_at.strftime("%d/%m")
            if day_key in timeline:
                timeline[day_key]["total"] += 1
                if t.status == "COMPLETED":
                    timeline[day_key]["completed"] += 1
                elif t.status == "FAILED":
                    timeline[day_key]["failed"] += 1

    # System Resources
    system_metrics = queue_manager.get_system_metrics()

    return {
        "total_count": total_count,
        "completed_count": completed_count,
        "failed_count": failed_count,
        "running_count": running_count,
        "pending_count": pending_count,
        "cancelled_count": cancelled_count,
        "success_rate": success_rate,
        "avg_duration_ms": avg_duration_ms,
        "max_duration_ms": max_duration_ms,
        "task_name_stats": task_name_stats,
        "chart_labels": list(timeline.keys()),
        "chart_completed": [v["completed"] for v in timeline.values()],
        "chart_failed": [v["failed"] for v in timeline.values()],
        "system_metrics": system_metrics,
        "registered_handlers": list(TASK_HANDLERS.keys())
    }


# ===========================================================================
# 6. TASK ACTIONS: CANCEL, RETRY, PURGE
# ===========================================================================
def cancel_background_task(task_id: str) -> dict:
    """Hủy bỏ một tác vụ đang chờ hoặc đang chạy."""
    task = BackgroundTask.query.filter_by(task_id=task_id).first()
    if not task:
        return {"success": False, "error": "Không tìm thấy tác vụ."}
    if task.status in ("COMPLETED", "FAILED"):
        return {"success": False, "error": f"Không thể hủy tác vụ đã kết thúc ({task.status})."}

    task.status = "CANCELLED"
    task.completed_at = now()
    try:
        db.session.commit()
        return {"success": True, "message": f"Đã hủy tác vụ '{task.name}' thành công."}
    except Exception as exc:
        db.session.rollback()
        return {"success": False, "error": str(exc)}


def retry_background_task_now(task_id: str) -> dict:
    """Kích hoạt chạy lại ngay một tác vụ đã thất bại hoặc bị hủy."""
    task = BackgroundTask.query.filter_by(task_id=task_id).first()
    if not task:
        return {"success": False, "error": "Không tìm thấy tác vụ."}

    task.status = "PENDING"
    task.error_message = None
    task.retry_count = 0
    task.started_at = None
    task.completed_at = None
    try:
        db.session.commit()
        app_obj = current_app._get_current_object()
        queue_manager.worker_pool.submit(_execute_task_in_worker, app_obj, task.task_id)
        return {"success": True, "message": f"Đã đưa tác vụ '{task.name}' vào hàng đợi chạy lại."}
    except Exception as exc:
        db.session.rollback()
        return {"success": False, "error": str(exc)}


def purge_old_background_tasks(days_to_keep: int = 7) -> int:
    """Dọn dẹp các tác vụ đã hoàn thành hoặc thất bại cũ hơn N ngày."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days_to_keep)
    old_tasks = BackgroundTask.query.filter(
        (BackgroundTask.status.in_(["COMPLETED", "FAILED", "CANCELLED"])) &
        (BackgroundTask.created_at < cutoff)
    ).all()
    deleted_count = 0
    for t in old_tasks:
        db.session.delete(t)
        deleted_count += 1
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
    return deleted_count
