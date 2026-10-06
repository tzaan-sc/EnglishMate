"""
EnglishMate Error Handling, Analysis & Realtime Monitoring Service
==================================================================
Chịu trách nhiệm:
1. Error Analysis: Tự động gom nhóm lỗi (Fingerprinting theo Exception + Traceback location),
   thống kê tần suất xuất hiện, tỷ lệ theo mã HTTP (5xx, 4xx) và xu hướng lỗi theo thời gian.
2. Error Monitoring: Tích hợp Sentry SDK, tự động bắt unhandled exceptions, thu thập đầy đủ
   ngữ cảnh (Traceback, Route, Method, User ID, IP, User Agent, Params) và quản lý vòng đời lỗi.
"""

import os
import sys
import uuid
import time
import json
import hashlib
import logging
import traceback
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from flask import Flask, request, g, current_app
from sqlalchemy import func, desc

from ...extensions import db
from .models import SystemErrorLog, now

logger = logging.getLogger("englishmate.errors")

_SENTRY_INITIALIZED = False


# ===========================================================================
# 1. INITIALIZATION & SENTRY INTEGRATION
# ===========================================================================
def init_error_monitoring(app: Flask):
    """
    Khởi tạo hệ thống giám sát lỗi toàn diện (Sentry SDK + Custom Exception Tracker).
    """
    global _SENTRY_INITIALIZED

    sentry_dsn = (
        app.config.get("SENTRY_DSN")
        or os.getenv("SENTRY_DSN", "")
    ).strip()

    environment = app.config.get("ENV") or os.getenv("FLASK_ENV", "production")

    if sentry_dsn and not app.config.get("TESTING"):
        try:
            import sentry_sdk
            from sentry_sdk.integrations.flask import FlaskIntegration
            from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

            sentry_sdk.init(
                dsn=sentry_dsn,
                integrations=[FlaskIntegration(), SqlalchemyIntegration()],
                traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.2")),
                environment=environment,
                release=os.getenv("APP_VERSION", "v1.0.0"),
                send_default_pii=False,
            )
            _SENTRY_INITIALIZED = True
            logger.info("✅ [Sentry] Đã kích hoạt giám sát lỗi thời gian thực Sentry SDK.")
        except Exception as exc:
            logger.warning(f"⚠️ [Sentry] Không thể khởi tạo Sentry SDK ({exc}). Sẽ sử dụng Local Error Monitoring.")
            _SENTRY_INITIALIZED = False
    else:
        _SENTRY_INITIALIZED = False

    # Đăng ký handler bắt ngoại lệ toàn cục 500
    @app.errorhandler(500)
    def _handle_500_internal_error(error):
        record_system_error(
            exc=getattr(error, "original_exception", error),
            status_code=500,
            severity="CRITICAL",
            custom_message=str(error)
        )
        from flask import render_template
        if request.is_json or request.path.startswith("/api/"):
            from flask import jsonify
            return jsonify({
                "success": False,
                "error": "InternalServerError",
                "message": "Đã xảy ra sự cố nội bộ máy chủ. Đội ngũ kỹ thuật đã được thông báo tự động."
            }), 500
        return render_template("errors/500.html"), 500


def is_sentry_active() -> bool:
    """Kiểm tra Sentry SDK có đang hoạt động hay không."""
    return _SENTRY_INITIALIZED


# ===========================================================================
# 2. ERROR FINGERPRINTING & RECORDING
# ===========================================================================
def compute_error_fingerprint(
    exception_type: str,
    error_message: str,
    traceback_str: Optional[str] = None
) -> str:
    """
    Tạo mã băm Fingerprint chuẩn xác để gom nhóm tự động các lỗi giống nhau.
    Chuẩn hóa dòng code và trích xuất file/function từ traceback frame.
    """
    location_key = ""
    import re
    if traceback_str:
        lines = [line.strip() for line in traceback_str.split("\n") if line.strip()]
        # Tìm dòng 'File "...", line ...' gần nhất
        file_lines = [l for l in lines if l.startswith('File "')]
        if file_lines:
            last_frame = file_lines[-1]
            location_key = re.sub(r", line \d+", "", last_frame)

    # Nếu không có traceback location, chuẩn hóa thông điệp lỗi (loại bỏ UUID, số ID)
    if not location_key:
        norm_msg = re.sub(r"[0-9a-fA-F-]{8,}", "{ID}", error_message or "")
        norm_msg = re.sub(r"\d+", "{N}", norm_msg)
        location_key = norm_msg[:200]

    raw_data = f"{exception_type}::{location_key}"
    return hashlib.sha256(raw_data.encode("utf-8")).hexdigest()[:32]


def record_system_error(
    exc: Optional[Exception] = None,
    status_code: int = 500,
    severity: str = "ERROR",
    route: Optional[str] = None,
    method: Optional[str] = None,
    user_id: Optional[int] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    params: Optional[dict] = None,
    custom_message: Optional[str] = None,
) -> Optional[SystemErrorLog]:
    """
    Ghi nhận một lỗi hệ thống vào CSDL và chuyển tiếp cảnh báo Sentry:
    - Gom nhóm tự động theo Fingerprint nếu lỗi tương tự đã xuất hiện trong 24h.
    - Tăng occurrence_count và cập nhật last_seen_at.
    """
    try:
        # 1. Trích xuất thông tin ngoại lệ
        if exc is not None:
            if isinstance(exc, Exception):
                exc_type = type(exc).__name__
                exc_msg = str(exc) or exc_type
                tb_str = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
            else:
                exc_type = str(getattr(exc, "name", "HTTPException"))
                exc_msg = str(getattr(exc, "description", exc))
                tb_str = str(exc)
        else:
            exc_type = "GenericSystemError"
            exc_msg = custom_message or "Lỗi hệ thống không xác định"
            tb_str = ""

        if custom_message and exc_msg != custom_message:
            exc_msg = f"{custom_message} ({exc_msg})"

        # 2. Thu thập ngữ cảnh HTTP nếu đang trong Request Context
        req_route = route
        req_method = method
        req_user_id = user_id
        req_ip = ip_address
        req_ua = user_agent
        req_params = params

        try:
            from flask import has_request_context
            if has_request_context():
                if not req_route:
                    req_route = request.path
                if not req_method:
                    req_method = request.method
                if not req_ip:
                    from .network_security import get_client_ip
                    req_ip = get_client_ip(request)
                if not req_ua:
                    req_ua = request.headers.get("User-Agent", "")[:255]
                if req_user_id is None:
                    from flask_login import current_user
                    if current_user and current_user.is_authenticated:
                        req_user_id = current_user.id
                if req_params is None:
                    req_params = {
                        "args": request.args.to_dict(),
                        "form": {k: v for k, v in request.form.to_dict().items() if "password" not in k.lower()}
                    }
        except Exception:
            pass

        fingerprint = compute_error_fingerprint(exc_type, exc_msg, tb_str)

        # 3. Gửi sự kiện đến Sentry nếu được kích hoạt
        sentry_event_id = None
        if _SENTRY_INITIALIZED and exc is not None and isinstance(exc, Exception):
            try:
                import sentry_sdk
                with sentry_sdk.push_scope() as scope:
                    if req_user_id:
                        scope.user = {"id": req_user_id}
                    if req_route:
                        scope.set_tag("route", req_route)
                    scope.set_tag("status_code", str(status_code))
                    sentry_event_id = sentry_sdk.capture_exception(exc)
            except Exception as s_err:
                logger.warning(f"Error sending event to Sentry: {s_err}")

        # 4. Kiểm tra gom nhóm lỗi (Error Grouping):
        # Nếu đã có bản ghi chưa giải quyết cùng fingerprint trong vòng 24h -> Increment count
        cutoff_24h = datetime.now(timezone.utc) - timedelta(hours=24)
        existing_log = SystemErrorLog.query.filter(
            SystemErrorLog.fingerprint == fingerprint,
            SystemErrorLog.is_resolved == False,
            SystemErrorLog.last_seen_at >= cutoff_24h
        ).first()

        if existing_log:
            existing_log.occurrence_count += 1
            existing_log.last_seen_at = now()
            existing_log.error_message = exc_msg  # Cập nhật thông điệp mới nhất
            if tb_str:
                existing_log.traceback_text = tb_str
            if req_params:
                existing_log.request_params_json = json.dumps(req_params, ensure_ascii=False, default=str)
            db.session.commit()
            return existing_log

        # 5. Tạo mới Error Log Record
        error_uuid = str(uuid.uuid4())
        params_json_str = json.dumps(req_params, ensure_ascii=False, default=str) if req_params else None

        new_log = SystemErrorLog(
            error_id=error_uuid,
            fingerprint=fingerprint,
            exception_type=exc_type[:120],
            error_message=exc_msg,
            status_code=status_code,
            severity=severity.upper(),
            route=req_route[:255] if req_route else None,
            http_method=(req_method or "GET")[:10],
            user_id=req_user_id,
            ip_address=req_ip[:64] if req_ip else None,
            user_agent=req_ua[:255] if req_ua else None,
            traceback_text=tb_str,
            request_params_json=params_json_str,
            is_resolved=False,
            sentry_event_id=str(sentry_event_id) if sentry_event_id else None,
            occurrence_count=1,
            first_seen_at=now(),
            last_seen_at=now(),
            created_at=now(),
        )
        db.session.add(new_log)
        db.session.commit()
        logger.error(f"🚨 [Error Logged] {exc_type} on {req_route} (ID: {error_uuid})")

        # 6. Tự động bắn thông báo cảnh báo qua Telegram/Discord/Slack Webhooks
        try:
            from .alert_service import alert_service
            alert_service.dispatch_error_alert_async({
                "error_id": error_uuid,
                "fingerprint": fingerprint,
                "exception_type": exc_type,
                "message": exc_msg,
                "status_code": status_code,
                "severity": severity.upper(),
                "route": req_route or "/",
                "method": req_method or "GET",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "client_ip": req_ip or "127.0.0.1",
                "user_id": req_user_id,
                "traceback": tb_str[:600] if tb_str else "",
            })
        except Exception:
            pass

        return new_log

    except Exception as inner_err:
        try:
            db.session.rollback()
        except Exception:
            pass
        logger.critical(f"FATAL: Error recording system error log: {inner_err}")
        return None


# ===========================================================================
# 3. ERROR ANALYSIS & REPORTING ENGINE
# ===========================================================================
def get_error_analytics(days: int = 7) -> dict:
    """
    Phân tích và thống kê xu hướng lỗi hệ thống (Error Analysis):
    - Tổng số lần xảy ra lỗi, số nhóm lỗi duy nhất (Unique Fingerprints).
    - Phân bố theo mã HTTP status code (500, 502, 503, 404, 403, 400).
    - Phân bố theo loại ngoại lệ (Exception Types).
    - Phân bố theo đường dẫn (Top Error Routes).
    - Chuỗi thời gian 7 ngày (Daily Error Trend).
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    # 1. Tổng quan số liệu
    total_occurrences = db.session.query(func.coalesce(func.sum(SystemErrorLog.occurrence_count), 0)).filter(
        SystemErrorLog.created_at >= cutoff
    ).scalar() or 0

    unique_groups = db.session.query(func.count(SystemErrorLog.id)).filter(
        SystemErrorLog.created_at >= cutoff
    ).scalar() or 0

    unresolved_count = db.session.query(func.count(SystemErrorLog.id)).filter(
        SystemErrorLog.is_resolved == False
    ).scalar() or 0

    resolved_count = db.session.query(func.count(SystemErrorLog.id)).filter(
        SystemErrorLog.is_resolved == True
    ).scalar() or 0

    # Lỗi trong 24 giờ qua
    cutoff_24h = datetime.now(timezone.utc) - timedelta(hours=24)
    last_24h_count = db.session.query(func.coalesce(func.sum(SystemErrorLog.occurrence_count), 0)).filter(
        SystemErrorLog.last_seen_at >= cutoff_24h
    ).scalar() or 0

    # 2. Phân bố theo Status Code
    status_distribution_raw = db.session.query(
        SystemErrorLog.status_code,
        func.sum(SystemErrorLog.occurrence_count).label("count")
    ).filter(
        SystemErrorLog.created_at >= cutoff
    ).group_by(SystemErrorLog.status_code).all()

    status_distribution = {
        str(row.status_code): int(row.count) for row in status_distribution_raw
    }

    # 3. Phân bố theo Exception Type (Top 10)
    exc_type_raw = db.session.query(
        SystemErrorLog.exception_type,
        func.sum(SystemErrorLog.occurrence_count).label("count")
    ).filter(
        SystemErrorLog.created_at >= cutoff
    ).group_by(SystemErrorLog.exception_type).order_by(desc("count")).limit(10).all()

    exception_types = [
        {"type": row.exception_type, "count": int(row.count)}
        for row in exc_type_raw
    ]

    # 4. Phân bố theo Route (Top 10)
    routes_raw = db.session.query(
        SystemErrorLog.route,
        func.sum(SystemErrorLog.occurrence_count).label("count")
    ).filter(
        SystemErrorLog.created_at >= cutoff,
        SystemErrorLog.route.isnot(None)
    ).group_by(SystemErrorLog.route).order_by(desc("count")).limit(10).all()

    top_routes = [
        {"route": row.route or "Unknown", "count": int(row.count)}
        for row in routes_raw
    ]

    # 5. Phân bố theo Mức độ nghiêm trọng (Severity)
    severity_raw = db.session.query(
        SystemErrorLog.severity,
        func.sum(SystemErrorLog.occurrence_count).label("count")
    ).filter(
        SystemErrorLog.created_at >= cutoff
    ).group_by(SystemErrorLog.severity).all()

    severity_distribution = {
        row.severity: int(row.count) for row in severity_raw
    }

    # 6. Biểu đồ xu hướng hàng ngày (Daily Trend 7 ngày)
    daily_trend = []
    for i in range(days - 1, -1, -1):
        day_start = (datetime.now(timezone.utc) - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        day_count = db.session.query(func.coalesce(func.sum(SystemErrorLog.occurrence_count), 0)).filter(
            SystemErrorLog.created_at >= day_start,
            SystemErrorLog.created_at < day_end
        ).scalar() or 0
        
        daily_trend.append({
            "date": day_start.strftime("%d/%m"),
            "date_iso": day_start.strftime("%Y-%m-%d"),
            "count": int(day_count)
        })

    return {
        "days": days,
        "total_occurrences": total_occurrences,
        "unique_groups": unique_groups,
        "unresolved_count": unresolved_count,
        "resolved_count": resolved_count,
        "last_24h_count": last_24h_count,
        "status_distribution": status_distribution,
        "exception_types": exception_types,
        "top_routes": top_routes,
        "severity_distribution": severity_distribution,
        "daily_trend": daily_trend,
        "sentry_active": _SENTRY_INITIALIZED
    }


def get_error_incidents_list(
    page: int = 1,
    per_page: int = 20,
    status_code: Optional[int] = None,
    severity: Optional[str] = None,
    is_resolved: Optional[bool] = None,
    search: Optional[str] = None
) -> dict:
    """Lấy danh sách các nhóm lỗi (Incidents) có phân trang và bộ lọc."""
    query = SystemErrorLog.query

    if status_code:
        query = query.filter(SystemErrorLog.status_code == status_code)
    if severity:
        query = query.filter(SystemErrorLog.severity == severity.upper())
    if is_resolved is not None:
        query = query.filter(SystemErrorLog.is_resolved == is_resolved)
    if search:
        s = f"%{search.strip()}%"
        query = query.filter(
            (SystemErrorLog.error_message.ilike(s))
            | (SystemErrorLog.exception_type.ilike(s))
            | (SystemErrorLog.route.ilike(s))
            | (SystemErrorLog.error_id.ilike(s))
        )

    # Ưu tiên các lỗi chưa xử lý và mới xuất hiện nhất
    query = query.order_by(
        SystemErrorLog.is_resolved.asc(),
        SystemErrorLog.last_seen_at.desc()
    )

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return {
        "items": pagination.items,
        "total": pagination.total,
        "page": pagination.page,
        "pages": pagination.pages,
        "has_prev": pagination.has_prev,
        "has_next": pagination.has_next
    }


# ===========================================================================
# 4. ERROR RESOLUTION & MAINTENANCE ACTIONS
# ===========================================================================
def resolve_error_incident(
    error_id: str,
    admin_id: Optional[int] = None,
    notes: Optional[str] = None
) -> bool:
    """Đánh dấu một nhóm lỗi đã được xử lý xong."""
    item = SystemErrorLog.query.filter_by(error_id=error_id).first()
    if not item:
        return False

    item.is_resolved = True
    item.resolved_at = now()
    item.resolved_by_id = admin_id
    if notes:
        item.resolution_notes = notes

    db.session.commit()
    logger.info(f"✅ Đã xử lý xong sự cố lỗi {error_id} bởi Admin #{admin_id}")
    return True


def resolve_all_error_incidents(admin_id: Optional[int] = None, severity: Optional[str] = None) -> int:
    """Đánh dấu giải quyết hàng loạt toàn bộ các sự cố lỗi đang mở."""
    query = SystemErrorLog.query.filter_by(is_resolved=False)
    if severity:
        query = query.filter_by(severity=severity.upper())

    items = query.all()
    count = 0
    now_time = now()
    for it in items:
        it.is_resolved = True
        it.resolved_at = now_time
        it.resolved_by_id = admin_id
        count += 1

    db.session.commit()
    return count


def purge_old_error_logs(days_to_keep: int = 30) -> int:
    """Dọn dẹp các sự cố lỗi đã xử lý quá số ngày quy định."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days_to_keep)
    old_logs = SystemErrorLog.query.filter(
        SystemErrorLog.is_resolved == True,
        SystemErrorLog.last_seen_at < cutoff
    ).all()

    count = 0
    for l in old_logs:
        db.session.delete(l)
        count += 1

    db.session.commit()
    logger.info(f"🧹 Đã xóa {count} bản ghi nhật ký lỗi cũ đã giải quyết trước {days_to_keep} ngày.")
    return count


def trigger_simulated_error(error_type: str = "division_by_zero") -> dict:
    """
    Kích hoạt ngoại lệ mô phỏng để kiểm tra toàn trình (Test Simulation)
    cơ chế bắt lỗi, lưu CSDL và chuyển tiếp Sentry.
    """
    try:
        if error_type == "division_by_zero":
            _ = 1 / 0
        elif error_type == "value_error":
            raise ValueError("Mô phỏng lỗi ValueError do dữ liệu đầu vào không hợp lệ.")
        elif error_type == "key_error":
            sample_dict = {}
            _ = sample_dict["missing_required_token"]
        elif error_type == "null_reference":
            obj = None
            obj.get_user_id()
        else:
            raise RuntimeError(f"Mô phỏng lỗi ngoại lệ Runtime: {error_type}")
    except Exception as exc:
        log_entry = record_system_error(
            exc=exc,
            status_code=500,
            severity="ERROR",
            route="/admin/system/errors/test-trigger",
            method="POST",
            custom_message=f"Test simulated exception: {error_type}"
        )
        return {
            "success": True,
            "simulated_type": error_type,
            "error_id": log_entry.error_id if log_entry else None,
            "fingerprint": log_entry.fingerprint if log_entry else None,
            "sentry_event_id": log_entry.sentry_event_id if log_entry else None,
            "message": f"Đã mô phỏng thành công ngoại lệ '{type(exc).__name__}'."
        }
