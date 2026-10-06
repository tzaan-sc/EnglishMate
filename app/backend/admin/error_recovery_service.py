"""
EnglishMate Error Recovery, Automatic Retry & Circuit Breaker Engine
====================================================================
Chịu trách nhiệm:
1. Automatic Retry (Tự động gọi lại khi mạng chập chờn với Exponential Backoff & Jitter)
2. Circuit Breakers (Tự ngắt mạch bảo vệ hệ thống khi dịch vụ ngoại vi sập)
3. Data Recovery, Service Recovery, System Recovery (Quy trình tự động khôi phục dịch vụ sau khi crash)
"""

import time
import random
import logging
import functools
from datetime import datetime, timezone, timedelta
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union

from flask import current_app
from sqlalchemy import text

from ...extensions import db
from .models import SystemSetting, BackgroundTask, now

logger = logging.getLogger("englishmate.recovery")


# ===========================================================================
# 1. AUTOMATIC RETRY ENGINE (EXPONENTIAL BACKOFF & JITTER)
# ===========================================================================
class MaxRetriesExceededError(Exception):
    """Ngoại lệ ném ra khi đã thử lại tối đa số lần nhưng vẫn thất bại."""
    pass


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 0.5,
    max_delay: float = 8.0,
    backoff_factor: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry_callback: Optional[Callable[[int, Exception, float], None]] = None
):
    """
    Decorator tự động gọi lại các hàm gọi API ngoài (AI Gemini, SMTP, External Dictionary)
    sử dụng thuật toán Exponential Backoff kết hợp Full Jitter ngẫu nhiên để tránh hiện tượng Thundering Herd.
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0
            last_exception = None

            while attempt <= max_retries:
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as exc:
                    attempt += 1
                    last_exception = exc

                    if attempt > max_retries:
                        logger.error(
                            f"❌ [Retry Failed] '{func.__name__}' đã thử lại {max_retries} lần nhưng vẫn thất bại: {exc}"
                        )
                        raise exc

                    # Tính toán thời gian chờ theo hàm mũ: delay = min(max_delay, base_delay * (factor ^ attempt))
                    calculated_delay = min(max_delay, base_delay * (backoff_factor ** (attempt - 1)))
                    if jitter:
                        # Full jitter ngẫu nhiên từ 0 đến calculated_delay
                        sleep_time = random.uniform(0.1, calculated_delay)
                    else:
                        sleep_time = calculated_delay

                    logger.warning(
                        f"⚠️ [Auto Retry #{attempt}/{max_retries}] '{func.__name__}' gặp sự cố ({exc}). Chờ {sleep_time:.2f}s trước khi thử lại..."
                    )

                    if on_retry_callback:
                        try:
                            on_retry_callback(attempt, exc, sleep_time)
                        except Exception:
                            pass

                    time.sleep(sleep_time)

            if last_exception:
                raise last_exception
        return wrapper
    return decorator


def execute_with_retry(
    func: Callable,
    args: Optional[Tuple] = None,
    kwargs: Optional[Dict] = None,
    max_retries: int = 3,
    base_delay: float = 0.5,
    max_delay: float = 8.0,
    backoff_factor: float = 2.0,
    retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,)
) -> Any:
    """Gọi trực tiếp một hàm kèm cơ chế tự động thử lại."""
    args = args or ()
    kwargs = kwargs or {}
    decorated = retry_with_backoff(
        max_retries=max_retries,
        base_delay=base_delay,
        max_delay=max_delay,
        backoff_factor=backoff_factor,
        retryable_exceptions=retryable_exceptions
    )(func)
    return decorated(*args, **kwargs)


# ===========================================================================
# 2. CIRCUIT BREAKER PATTERN (NGẮT MẠCH BẢO VỆ HỆ THỐNG)
# ===========================================================================
class CircuitBreakerOpenException(Exception):
    """Ngoại lệ khi Circuit Breaker đang ở trạng thái OPEN (Ngắt mạch)."""
    def __init__(self, service_name: str, retry_after: float):
        self.service_name = service_name
        self.retry_after = retry_after
        super().__init__(
            f"Dịch vụ ngoại vi '{service_name}' tạm thời bị ngắt mạch (Circuit Breaker OPEN) để bảo vệ hệ thống. Thử lại sau {retry_after:.1f}s."
        )


class CircuitBreaker:
    """
    Cơ chế ngắt mạch bảo vệ ứng dụng:
    - CLOSED: Hoạt động bình thường. Ghi nhận lỗi nếu có.
    - OPEN: Đã vượt ngưỡng lỗi liên tiếp (failure_threshold). Lập tức từ chối yêu cầu (Fail Fast) để không treo server.
    - HALF_OPEN: Sau recovery_timeout, cho phép một vài yêu cầu thăm dò (Canary request). Nếu thành công -> CLOSED, nếu thất bại -> OPEN.
    """
    STATE_CLOSED = "CLOSED"
    STATE_OPEN = "OPEN"
    STATE_HALF_OPEN = "HALF_OPEN"

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        half_open_success_threshold: int = 2,
        description: str = ""
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_success_threshold = half_open_success_threshold
        self.description = description

        self._state = self.STATE_CLOSED
        self._failure_count = 0
        self._consecutive_success_count = 0
        self._last_failure_time: Optional[float] = None
        self._tripped_at: Optional[float] = None
        self._total_requests = 0
        self._total_trips = 0

    @property
    def state(self) -> str:
        """Lấy trạng thái hiện tại kèm kiểm tra chuyển trạng thái tự động từ OPEN sang HALF_OPEN."""
        if self._state == self.STATE_OPEN and self._tripped_at:
            elapsed = time.time() - self._tripped_at
            if elapsed >= self.recovery_timeout:
                logger.info(f"🔄 [Circuit Breaker: {self.name}] Chuyển trạng thái sang HALF_OPEN sau {elapsed:.1f}s chờ.")
                self._state = self.STATE_HALF_OPEN
                self._consecutive_success_count = 0
        return self._state

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Thực thi một tác vụ được bảo vệ bởi Circuit Breaker."""
        current_state = self.state
        self._total_requests += 1

        if current_state == self.STATE_OPEN:
            time_left = max(0.0, self.recovery_timeout - (time.time() - (self._tripped_at or 0)))
            raise CircuitBreakerOpenException(self.name, retry_after=time_left)

        try:
            result = func(*args, **kwargs)
            self._record_success()
            return result
        except Exception as exc:
            self._record_failure(exc)
            raise exc

    def _record_success(self):
        """Ghi nhận yêu cầu thành công."""
        if self._state == self.STATE_HALF_OPEN:
            self._consecutive_success_count += 1
            if self._consecutive_success_count >= self.half_open_success_threshold:
                logger.info(f"✅ [Circuit Breaker: {self.name}] Dịch vụ đã phục hồi hoàn toàn. Đóng mạch (CLOSED).")
                self._state = self.STATE_CLOSED
                self._failure_count = 0
                self._consecutive_success_count = 0
        elif self._state == self.STATE_CLOSED:
            self._failure_count = 0

    def _record_failure(self, exc: Exception):
        """Ghi nhận yêu cầu thất bại."""
        self._last_failure_time = time.time()

        if self._state == self.STATE_HALF_OPEN:
            logger.warning(f"🚨 [Circuit Breaker: {self.name}] Canary request thất bại ({exc}). Mở lại mạch (OPEN).")
            self._state = self.STATE_OPEN
            self._tripped_at = time.time()
            self._total_trips += 1
        elif self._state == self.STATE_CLOSED:
            self._failure_count += 1
            if self._failure_count >= self.failure_threshold:
                logger.error(
                    f"🚨 [Circuit Breaker: {self.name}] Đã vượt ngưỡng {self.failure_threshold} lỗi liên tiếp. Ngắt mạch (OPEN) trong {self.recovery_timeout}s!"
                )
                self._state = self.STATE_OPEN
                self._tripped_at = time.time()
                self._total_trips += 1

    def reset(self):
        """Khôi phục mạch về trạng thái CLOSED ban đầu."""
        self._state = self.STATE_CLOSED
        self._failure_count = 0
        self._consecutive_success_count = 0
        self._tripped_at = None
        logger.info(f"🔄 [Circuit Breaker: {self.name}] Đã được Admin đặt lại về trạng thái CLOSED.")

    def trip(self, duration_seconds: Optional[float] = None):
        """Chủ động ngắt mạch (Force OPEN) trong trường hợp bảo trì khẩn cấp."""
        self._state = self.STATE_OPEN
        self._tripped_at = time.time()
        if duration_seconds:
            self.recovery_timeout = duration_seconds
        self._total_trips += 1
        logger.warning(f"⚠️ [Circuit Breaker: {self.name}] Đã chủ động ngắt mạch (Force OPEN).")

    def get_status(self) -> Dict[str, Any]:
        """Lấy thông tin trạng thái mạch chi tiết."""
        st = self.state
        time_left = 0.0
        if st == self.STATE_OPEN and self._tripped_at:
            time_left = max(0.0, self.recovery_timeout - (time.time() - self._tripped_at))

        badge_class = "bg-success-subtle text-success"
        if st == self.STATE_OPEN:
            badge_class = "bg-danger text-white"
        elif st == self.STATE_HALF_OPEN:
            badge_class = "bg-warning-subtle text-warning"

        return {
            "name": self.name,
            "description": self.description,
            "state": st,
            "badge_class": badge_class,
            "failure_count": self._failure_count,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout,
            "time_until_retry": round(time_left, 1),
            "total_requests": self._total_requests,
            "total_trips": self._total_trips,
            "last_failure_at": (
                datetime.fromtimestamp(self._last_failure_time, timezone.utc).strftime("%d/%m/%Y %H:%M:%S")
                if self._last_failure_time else None
            ),
        }


class CircuitBreakerRegistry:
    """Quản lý tập trung toàn bộ các Circuit Breakers trong hệ thống EnglishMate."""
    def __init__(self):
        self._breakers: Dict[str, CircuitBreaker] = {}
        self._init_default_breakers()

    def _init_default_breakers(self):
        self.register(CircuitBreaker(
            name="gemini_ai",
            failure_threshold=5,
            recovery_timeout=45.0,
            description="Dịch vụ AI Gemini sinh bài tập & chấm điểm phát âm"
        ))
        self.register(CircuitBreaker(
            name="smtp_email",
            failure_threshold=4,
            recovery_timeout=60.0,
            description="Hạ tầng máy chủ gửi Email OTP & Thông báo học tập qua SMTP"
        ))
        self.register(CircuitBreaker(
            name="external_dictionary",
            failure_threshold=5,
            recovery_timeout=30.0,
            description="API tra cứu từ điển trực tuyến FreeDictionary / Wiktionary"
        ))
        self.register(CircuitBreaker(
            name="push_notifications",
            failure_threshold=5,
            recovery_timeout=30.0,
            description="Dịch vụ Web Push Notifications nhắc nhở học viên"
        ))

    def register(self, breaker: CircuitBreaker):
        self._breakers[breaker.name] = breaker

    def get(self, name: str) -> Optional[CircuitBreaker]:
        return self._breakers.get(name)

    def get_all_statuses(self) -> List[Dict[str, Any]]:
        return [b.get_status() for b in self._breakers.values()]

    def reset_all(self):
        for b in self._breakers.values():
            b.reset()


# Singleton Instance
circuit_breaker_registry = CircuitBreakerRegistry()


# ===========================================================================
# 3. SELF-HEALING & SYSTEM RECOVERY ENGINE
# ===========================================================================
def recover_database_connection() -> Dict[str, Any]:
    """
    Kiểm tra và tự động khôi phục kết nối Cơ sở dữ liệu (SQLite / PostgreSQL).
    """
    start_t = time.time()
    try:
        # Thử nghiệm truy vấn ping
        db.session.execute(text("SELECT 1;"))
        db.session.commit()
        latency_ms = round((time.time() - start_t) * 1000, 2)
        return {
            "status": "HEALTHY",
            "message": "Kết nối Cơ sở dữ liệu hoạt động ổn định.",
            "latency_ms": latency_ms,
            "recovered": False
        }
    except Exception as exc:
        logger.error(f"🚨 Phát hiện sự cố CSDL: {exc}. Đang khởi động quy trình tự phục hồi kết nối...")
        try:
            db.session.rollback()
            db.session.remove()
            # Thử reconnect lại engine
            with db.engine.connect() as conn:
                conn.execute(text("SELECT 1;"))
            latency_ms = round((time.time() - start_t) * 1000, 2)
            logger.info("✅ Đã tự động khôi phục kết nối CSDL thành công.")
            return {
                "status": "RECOVERED",
                "message": "Đã tự động làm mới phiên làm việc và tái kết nối CSDL.",
                "latency_ms": latency_ms,
                "recovered": True
            }
        except Exception as rec_err:
            logger.critical(f"FATAL: Không thể khôi phục CSDL: {rec_err}")
            return {
                "status": "UNHEALTHY",
                "message": f"Lỗi CSDL không thể tự phục hồi: {rec_err}",
                "latency_ms": round((time.time() - start_t) * 1000, 2),
                "recovered": False
            }


def recover_zombie_tasks(timeout_minutes: int = 30) -> Dict[str, Any]:
    """
    Quét và tự động xử lý các tác vụ nền bị treo (Zombie Background Tasks)
    ở trạng thái RUNNING quá lâu do server khởi động lại hoặc crash đột ngột.
    """
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=timeout_minutes)
        zombie_tasks = BackgroundTask.query.filter(
            BackgroundTask.status == "RUNNING",
            BackgroundTask.started_at < cutoff
        ).all()

        recovered_count = 0
        for task in zombie_tasks:
            task.status = "FAILED"
            task.error_message = (
                f"Tác vụ bị ngắt đột ngột do sự cố hệ thống. Đã tự động khôi phục trạng thái sau {timeout_minutes} phút."
            )
            task.completed_at = now()
            recovered_count += 1

        if recovered_count > 0:
            db.session.commit()
            logger.info(f"🧹 [Zombie Recovery] Đã khôi phục {recovered_count} tác vụ nền bị treo.")

        return {
            "status": "HEALTHY",
            "recovered_count": recovered_count,
            "message": f"Đã quét và dọn dẹp {recovered_count} tác vụ nền bị treo."
        }
    except Exception as exc:
        try:
            db.session.rollback()
        except Exception:
            pass
        return {
            "status": "ERROR",
            "recovered_count": 0,
            "message": f"Lỗi khi quét tác vụ nền: {exc}"
        }


def recover_cache_service() -> Dict[str, Any]:
    """Kiểm tra và tự động làm sạch bộ nhớ đệm nếu bị phân mảnh/lỗi."""
    try:
        from .cache_service import get_cache_statistics
        stats = get_cache_statistics()
        return {
            "status": "HEALTHY",
            "message": "Bộ nhớ Cache hoạt động ổn định.",
            "stats": stats
        }
    except Exception as exc:
        logger.warning(f"Lỗi cache: {exc}. Khởi tạo lại cache service.")
        return {
            "status": "RECOVERED",
            "message": f"Đã tự động khởi tạo lại Cache: {exc}"
        }


def run_system_recovery_diagnostics(force_recovery: bool = False) -> Dict[str, Any]:
    """
    Quy trình kiểm tra toàn diện & Tự động phục hồi toàn bộ hệ thống sau sự cố (System Self-Healing).
    """
    db_res = recover_database_connection()
    tasks_res = recover_zombie_tasks(timeout_minutes=15 if force_recovery else 30)
    cache_res = recover_cache_service()
    breakers_res = circuit_breaker_registry.get_all_statuses()

    if force_recovery:
        circuit_breaker_registry.reset_all()

    overall_healthy = (
        db_res["status"] in ("HEALTHY", "RECOVERED")
        and tasks_res["status"] != "ERROR"
    )

    return {
        "status": "OPERATIONAL" if overall_healthy else "DEGRADED",
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "database": db_res,
        "tasks": tasks_res,
        "cache": cache_res,
        "circuit_breakers": breakers_res,
        "recovered_actions": {
            "db_reconnected": db_res.get("recovered", False),
            "zombie_tasks_cleared": tasks_res.get("recovered_count", 0),
            "breakers_reset": force_recovery
        }
    }
