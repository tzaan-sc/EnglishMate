"""
Admin Error Handling, Analysis & Realtime Monitoring Routes
============================================================
Routes:
- GET  /admin/system/errors: Bảng điều khiển phân tích lỗi & sự cố hệ thống
- GET  /admin/system/errors/api/analytics: JSON API thống kê xu hướng lỗi
- GET  /admin/system/errors/<error_id>: JSON API chi tiết sự cố & stacktrace
- POST /admin/system/errors/<error_id>/resolve: Đánh dấu sự cố đã xử lý
- POST /admin/system/errors/resolve-all: Đánh dấu tất cả sự cố đã xử lý
- POST /admin/system/errors/test-trigger: Mô phỏng ngoại lệ thử nghiệm
- POST /admin/system/errors/purge: Dọn dẹp nhật ký lỗi cũ đã giải quyết
"""

import json
from flask import render_template, request, jsonify, flash, redirect, url_for
from flask_login import current_user

from . import bp
from .utils import admin_required, log_audit_action
from .models import SystemErrorLog
from .error_monitoring_service import (
    get_error_analytics,
    get_error_incidents_list,
    resolve_error_incident,
    resolve_all_error_incidents,
    purge_old_error_logs,
    trigger_simulated_error,
    get_error_patterns_analysis,
    lookup_error_by_trace_or_id,
)


@bp.get("/system/errors")
@bp.get("/errors")
@admin_required
def error_analysis_dashboard():
    """Giao diện Quản trị Phân tích & Giám sát Lỗi Hệ thống."""
    page = request.args.get("page", 1, type=int)
    search = request.args.get("search", "").strip() or None
    status_code = request.args.get("status_code", type=int)
    severity = request.args.get("severity", "").strip() or None
    is_resolved_raw = request.args.get("is_resolved", "").strip()

    is_resolved = None
    if is_resolved_raw in ("0", "false", "False"):
        is_resolved = False
    elif is_resolved_raw in ("1", "true", "True"):
        is_resolved = True

    analytics = get_error_analytics(days=7)
    patterns = get_error_patterns_analysis(days=7)
    incidents = get_error_incidents_list(
        page=page,
        per_page=15,
        status_code=status_code,
        severity=severity,
        is_resolved=is_resolved,
        search=search
    )

    return render_template(
        "admin/error_analysis.html",
        analytics=analytics,
        patterns=patterns,
        incidents=incidents,
        search=search,
        status_code=status_code,
        severity=severity,
        is_resolved=1 if is_resolved is True else (0 if is_resolved is False else None)
    )


@bp.get("/system/errors/api/analytics")
@bp.get("/errors/api/analytics")
@admin_required
def get_error_analytics_api():
    """API JSON trả về số liệu phân tích lỗi cho biểu đồ."""
    days = request.args.get("days", 7, type=int)
    data = get_error_analytics(days=days)
    return jsonify(data)


@bp.get("/system/errors/api/patterns")
@bp.get("/errors/api/patterns")
@admin_required
def get_error_patterns_api():
    """API JSON phân tích các cụm mẫu lỗi (Error Patterns)."""
    days = request.args.get("days", 7, type=int)
    patterns = get_error_patterns_analysis(days=days)
    return jsonify({"success": True, "patterns": patterns})


@bp.get("/system/errors/lookup")
@bp.get("/errors/lookup")
@admin_required
def lookup_error_by_trace_route():
    """Tra cứu nhanh sự cố theo Request Trace ID."""
    trace_id = request.args.get("trace_id", "").strip()
    log_item = lookup_error_by_trace_or_id(trace_id)
    if not log_item:
        return jsonify({"success": False, "error": f"Không tìm thấy sự cố với Trace ID '{trace_id}'."}), 404
    return jsonify({
        "success": True,
        "error_id": log_item.error_id,
        "exception_type": log_item.exception_type,
        "error_message": log_item.error_message,
        "status_code": log_item.status_code,
        "severity": log_item.severity,
        "route": log_item.route,
        "created_at": log_item.created_at_vn.strftime("%d/%m/%Y %H:%M:%S") if log_item.created_at_vn else None,
    })


@bp.get("/system/errors/<string:error_id>")
@bp.get("/errors/<string:error_id>")
@admin_required
def get_error_detail_api(error_id):
    """API JSON lấy thông tin chi tiết và Stacktrace của một sự cố lỗi."""
    item = SystemErrorLog.query.filter_by(error_id=error_id).first()
    if not item:
        return jsonify({"success": False, "error": "Không tìm thấy sự cố lỗi."}), 404

    return jsonify({
        "success": True,
        "data": {
            "error_id": item.error_id,
            "fingerprint": item.fingerprint,
            "exception_type": item.exception_type,
            "error_message": item.error_message,
            "status_code": item.status_code,
            "severity": item.severity,
            "severity_badge_class": item.severity_badge_class,
            "route": item.route,
            "http_method": item.http_method,
            "user_id": item.user_id,
            "ip_address": item.ip_address,
            "user_agent": item.user_agent,
            "traceback_text": item.traceback_text,
            "request_params": json.loads(item.request_params_json) if item.request_params_json else None,
            "is_resolved": item.is_resolved,
            "resolved_at": item.resolved_at.isoformat() if item.resolved_at else None,
            "occurrence_count": item.occurrence_count,
            "first_seen_at": item.first_seen_at_vn.strftime("%d/%m/%Y %H:%M:%S") if item.first_seen_at_vn else None,
            "last_seen_at": item.last_seen_at_vn.strftime("%d/%m/%Y %H:%M:%S") if item.last_seen_at_vn else None,
            "sentry_event_id": item.sentry_event_id,
        }
    })


@bp.post("/system/errors/<string:error_id>/resolve")
@bp.post("/errors/<string:error_id>/resolve")
@admin_required
def resolve_error_route(error_id):
    """Đánh dấu sự cố lỗi đã được khắc phục."""
    notes = request.form.get("notes") or (request.get_json(silent=True) or {}).get("notes")
    success = resolve_error_incident(error_id=error_id, admin_id=current_user.id, notes=notes)

    if success:
        log_audit_action(
            user_id=current_user.id,
            action="RESOLVE_SYSTEM_ERROR",
            target_type="SYSTEM_ERROR_LOG",
            target_id=error_id,
            details=f"Đánh dấu giải quyết sự cố lỗi {error_id}"
        )

    if request.is_json:
        return jsonify({"success": success, "message": f"Đã giải quyết sự cố {error_id}"})
    if success:
        flash("Đã đánh dấu sự cố lỗi là ĐÃ XỬ LÝ.", "success")
    else:
        flash("Không tìm thấy sự cố lỗi cần xử lý.", "danger")
    return redirect(url_for("admin.error_analysis_dashboard"))


@bp.post("/system/errors/resolve-all")
@bp.post("/errors/resolve-all")
@admin_required
def resolve_all_errors_route():
    """Đánh dấu tất cả sự cố lỗi đang mở là đã xử lý."""
    severity = request.form.get("severity") or (request.get_json(silent=True) or {}).get("severity")
    count = resolve_all_error_incidents(admin_id=current_user.id, severity=severity)

    log_audit_action(
        user_id=current_user.id,
        action="RESOLVE_ALL_SYSTEM_ERRORS",
        target_type="SYSTEM_ERROR_LOG",
        target_id="ALL",
        details=f"Đánh dấu giải quyết {count} sự cố lỗi đang mở"
    )

    msg = f"Đã đánh dấu {count} sự cố lỗi là ĐÃ XỬ LÝ."
    if request.is_json:
        return jsonify({"success": True, "count": count, "message": msg})
    flash(msg, "success")
    return redirect(url_for("admin.error_analysis_dashboard"))


@bp.post("/system/errors/test-trigger")
@bp.post("/errors/test-trigger")
@admin_required
def test_trigger_error_route():
    """Kích hoạt ngoại lệ mô phỏng để kiểm tra toàn trình."""
    data = request.get_json(silent=True) or request.form
    error_type = data.get("error_type", "division_by_zero")
    res = trigger_simulated_error(error_type=error_type)
    return jsonify(res)


@bp.post("/system/errors/purge")
@bp.post("/errors/purge")
@admin_required
def purge_error_logs_route():
    """Dọn dẹp các sự cố lỗi cũ đã giải quyết."""
    days = request.form.get("days", 30, type=int)
    count = purge_old_error_logs(days_to_keep=days)

    log_audit_action(
        user_id=current_user.id,
        action="PURGE_OLD_ERROR_LOGS",
        target_type="SYSTEM_ERROR_LOG",
        target_id="OLD_RESOLVED",
        details=f"Dọn dẹp {count} bản ghi nhật ký lỗi đã xử lý trước {days} ngày"
    )

    msg = f"Đã dọn dẹp {count} bản ghi nhật ký lỗi cũ."
    if request.is_json:
        return jsonify({"success": True, "count": count, "message": msg})
    flash(msg, "info")
    return redirect(url_for("admin.error_analysis_dashboard"))
