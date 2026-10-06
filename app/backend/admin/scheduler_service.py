import logging
import threading
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional

from flask import Flask

from app.backend.admin.task_queue_service import enqueue_background_task

logger = logging.getLogger(__name__)

# Try importing APScheduler
try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.triggers.interval import IntervalTrigger
    APSCHEDULER_AVAILABLE = True
except ImportError:
    BackgroundScheduler = None
    APSCHEDULER_AVAILABLE = False


class EnglishMateScheduler:
    """
    Quản lý bộ lập lịch tác vụ định kỳ tự động (APScheduler / Cron Jobs - Mục 12.5).
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(EnglishMateScheduler, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return

        self.app: Optional[Flask] = None
        self.scheduler = None
        self.is_running = False
        self.registered_definitions: Dict[str, dict] = {}
        self._fallback_threads: List[threading.Thread] = []
        self._stop_event = threading.Event()

        if APSCHEDULER_AVAILABLE:
            try:
                self.scheduler = BackgroundScheduler(daemon=True)
            except Exception as exc:
                logger.warning(f"Failed to initialize BackgroundScheduler: {exc}")
                self.scheduler = None

        self._register_default_job_definitions()
        self._initialized = True

    def _register_default_job_definitions(self):
        """Định nghĩa các tác vụ định kỳ chuẩn của hệ thống EnglishMate."""
        self.registered_definitions = {
            "email_queue_sync_job": {
                "name": "Đồng bộ Hàng đợi Email Hẹn giờ",
                "task_name": "email_queue_sync",
                "type": "interval",
                "minutes": 1,
                "description": "Quét và phát email hẹn giờ trong hàng đợi mỗi 1 phút.",
                "enabled": True,
            },
            "clean_expired_tokens_job": {
                "name": "Dọn dẹp Token hết hạn",
                "task_name": "clean_expired_tokens",
                "type": "cron",
                "hour": 2,
                "minute": 0,
                "description": "Dọn dẹp mã OTP và Token reset mật khẩu hết hạn hàng ngày lúc 02:00.",
                "enabled": True,
            },
            "system_cache_warming_job": {
                "name": "Nạp trước Cache Dữ liệu Tĩnh",
                "task_name": "system_cache_warming",
                "type": "cron",
                "hour": 4,
                "minute": 0,
                "description": "Nạp trước bảng xếp hạng và danh mục từ vựng vào bộ nhớ lúc 04:00.",
                "enabled": True,
            },
            "auto_database_backup_job": {
                "name": "Sao lưu CSDL Định kỳ Tự động",
                "task_name": "database_auto_backup",
                "type": "cron",
                "hour": 3,
                "minute": 0,
                "description": "Tự động đóng gói và sao lưu CSDL hàng ngày lúc 03:00.",
                "enabled": True,
            }
        }

    def init_app(self, app: Flask):
        """Khởi động bộ lập lịch cùng vòng đời ứng dụng Flask."""
        self.app = app
        if not self.is_running:
            self.start()

    def start(self):
        """Bắt đầu chạy scheduler."""
        if self.is_running:
            return

        if self.scheduler:
            try:
                # Add default scheduled jobs
                for job_id, defn in self.registered_definitions.items():
                    if not defn.get("enabled", True):
                        continue

                    task_name = defn["task_name"]

                    def _job_wrapper(tn=task_name):
                        if self.app:
                            with self.app.app_context():
                                enqueue_background_task(
                                    name=tn,
                                    task_type="SCHEDULED_CRON",
                                    priority=5,
                                    async_exec=True
                                )

                    if defn["type"] == "interval":
                        trigger = IntervalTrigger(minutes=defn.get("minutes", 5))
                    else:
                        trigger = CronTrigger(hour=defn.get("hour", 0), minute=defn.get("minute", 0))

                    if not self.scheduler.get_job(job_id):
                        self.scheduler.add_job(
                            _job_wrapper,
                            trigger=trigger,
                            id=job_id,
                            name=defn["name"],
                            replace_existing=True
                        )

                self.scheduler.start()
                self.is_running = True
                logger.info("EnglishMate BackgroundScheduler started successfully.")
            except Exception as exc:
                logger.warning(f"APScheduler start exception, falling back to background daemon: {exc}")
                self._start_fallback_daemon()
        else:
            self._start_fallback_daemon()

    def _start_fallback_daemon(self):
        """Chạy daemon scheduler dự phòng nếu không có APScheduler."""
        self._stop_event.clear()

        def _fallback_loop():
            logger.info("Starting EnglishMate Fallback Scheduler daemon...")
            last_run = {}
            while not self._stop_event.is_set():
                now_utc = datetime.now(timezone.utc)
                for job_id, defn in self.registered_definitions.items():
                    if not defn.get("enabled", True):
                        continue
                    last = last_run.get(job_id, 0)
                    interval_sec = defn.get("minutes", 60) * 60
                    if (time.time() - last) >= interval_sec:
                        last_run[job_id] = time.time()
                        if self.app:
                            try:
                                with self.app.app_context():
                                    enqueue_background_task(
                                        name=defn["task_name"],
                                        task_type="SCHEDULED_CRON",
                                        priority=5,
                                        async_exec=True
                                    )
                            except Exception as exc:
                                logger.warning(f"Fallback job execution error: {exc}")
                time.sleep(30)

        t = threading.Thread(target=_fallback_loop, daemon=True, name="EM-Fallback-Scheduler")
        t.start()
        self._fallback_threads.append(t)
        self.is_running = True

    def get_jobs_status(self) -> List[dict]:
        """Lấy danh sách các tác vụ định kỳ và thời gian chạy kế tiếp."""
        jobs_list = []
        for job_id, defn in self.registered_definitions.items():
            job_info = {
                "id": job_id,
                "name": defn["name"],
                "task_name": defn["task_name"],
                "type": defn["type"],
                "description": defn["description"],
                "is_enabled": defn.get("enabled", True),
                "next_run_time": None,
                "trigger_desc": f"Mỗi {defn.get('minutes')} phút" if defn["type"] == "interval" else f"Hàng ngày lúc {defn.get('hour'):02d}:{defn.get('minute'):02d}"
            }

            if self.scheduler and self.is_running:
                aps_job = self.scheduler.get_job(job_id)
                if aps_job and aps_job.next_run_time:
                    job_info["next_run_time"] = aps_job.next_run_time.strftime("%d/%m/%Y %H:%M:%S")

            jobs_list.append(job_info)
        return jobs_list

    def trigger_job_now(self, job_id: str) -> dict:
        """Kích hoạt chạy ngay lập tức một tác vụ định kỳ."""
        defn = self.registered_definitions.get(job_id)
        if not defn:
            return {"success": False, "error": f"Không tìm thấy tác vụ định kỳ '{job_id}'."}

        res = enqueue_background_task(
            name=defn["task_name"],
            task_type="SCHEDULED_CRON",
            priority=10,  # Manual trigger gets HIGH priority
            async_exec=True
        )
        return {"success": True, "message": f"Đã kích hoạt chạy tác vụ '{defn['name']}' ngay lập tức.", "task": res}

    def toggle_job_enabled(self, job_id: str, enable: bool) -> dict:
        """Bật hoặc tắt một tác vụ định kỳ."""
        defn = self.registered_definitions.get(job_id)
        if not defn:
            return {"success": False, "error": f"Không tìm thấy tác vụ định kỳ '{job_id}'."}

        defn["enabled"] = bool(enable)
        if self.scheduler and self.is_running:
            try:
                if self.scheduler.get_job(job_id):
                    if enable:
                        self.scheduler.resume_job(job_id)
                    else:
                        self.scheduler.pause_job(job_id)
            except Exception as exc:
                logger.warning(f"Could not toggle job {job_id} in APScheduler: {exc}")

        status_text = "bật" if enable else "tạm dừng"
        return {"success": True, "message": f"Đã {status_text} tác vụ '{defn['name']}'."}

    def shutdown(self):
        """Tắt scheduler."""
        self._stop_event.set()
        if self.scheduler and self.is_running:
            try:
                self.scheduler.shutdown(wait=False)
            except Exception:
                pass
        self.is_running = False


# Singleton scheduler instance
scheduler = EnglishMateScheduler()


def init_background_scheduler(app: Flask):
    """Khởi tạo scheduler trong factory create_app."""
    scheduler.init_app(app)
    return scheduler
