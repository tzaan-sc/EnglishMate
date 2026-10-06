"""
Unified Monitoring & Logging Admin Routes.
Handles System Resource Monitoring, Slow Query Analysis, Real-time Webhook Alerts,
Log Search/Analysis, and Automated Log Retention & Rotation.
"""

from flask import render_template, jsonify, request, flash, redirect, url_for, Response
from flask_login import login_required, current_user
import json
from datetime import datetime

from . import bp
from .utils import admin_required, log_audit_action
from .system_monitor_service import system_monitor
from .slow_query_logger import slow_query_monitor
from .alert_service import alert_service
from .log_analysis_service import log_analysis_service


@bp.route("/system/monitoring", methods=["GET"])
@login_required
@admin_required
def system_monitoring():
    """Trang tổng quan giám sát tài nguyên máy chủ, truy vấn chậm, cảnh báo bot và phân tích log."""
    resources = system_monitor.get_complete_system_metrics()
    slow_queries_summary = slow_query_monitor.get_summary()
    top_slow_templates = slow_query_monitor.get_top_slow_templates(limit=10)
    recent_slow_queries = slow_query_monitor.get_recent_slow_queries(limit=25)
    alert_config = alert_service.get_alert_config()
    log_overview = log_analysis_service.get_log_storage_overview()
    initial_logs = log_analysis_service.search_and_analyze_logs(level="ALL", limit=50)

    return render_template(
        "admin/monitoring_dashboard.html",
        resources=resources,
        slow_queries_summary=slow_queries_summary,
        top_slow_templates=top_slow_templates,
        recent_slow_queries=recent_slow_queries,
        alert_config=alert_config,
        log_overview=log_overview,
        initial_logs=initial_logs,
        active_tab="monitoring",
    )


@bp.route("/system/monitoring/api/resources", methods=["GET"])
@login_required
@admin_required
def api_system_resources():
    """API trả về số liệu tài nguyên phần cứng máy chủ thời gian thực dạng JSON."""
    metrics = system_monitor.get_complete_system_metrics()
    return jsonify({
        "success": True,
        "metrics": metrics,
        "timestamp": datetime.now().isoformat()
    })


@bp.route("/system/monitoring/api/slow-queries", methods=["GET"])
@login_required
@admin_required
def api_slow_queries():
    """API trả về thống kê các câu truy vấn CSDL chạy chậm."""
    summary = slow_query_monitor.get_summary()
    top_templates = slow_query_monitor.get_top_slow_templates(limit=20)
    recent_queries = slow_query_monitor.get_recent_slow_queries(limit=50)

    return jsonify({
        "success": True,
        "summary": summary,
        "top_templates": top_templates,
        "recent_queries": recent_queries,
        "timestamp": datetime.now().isoformat()
    })


@bp.route("/system/monitoring/api/slow-queries/reset", methods=["POST"])
@login_required
@admin_required
def reset_slow_queries():
    """Xóa toàn bộ số liệu thống kê truy vấn chậm."""
    slow_query_monitor.reset_metrics()
    log_audit_action(current_user.id, "RESET_SLOW_QUERIES", "System", None, "Đặt lại toàn bộ số liệu Slow Query Logger")
    if request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"success": True, "message": "Đã đặt lại dữ liệu giám sát truy vấn chậm."})
    flash("Đã đặt lại toàn bộ số liệu giám sát truy vấn chậm.", "success")
    return redirect(url_for("admin.system_monitoring"))


@bp.route("/system/monitoring/api/logs", methods=["GET"])
@login_required
@admin_required
def api_search_logs():
    """API tìm kiếm và phân tích tệp nhật ký theo bộ lọc."""
    filename = request.args.get("filename", "ALL")
    level = request.args.get("level", "ALL")
    keyword = request.args.get("keyword", "").strip()
    date_range = request.args.get("date_range", "all")
    limit = min(500, max(10, request.args.get("limit", 150, type=int)))

    result = log_analysis_service.search_and_analyze_logs(
        filename=filename,
        level=level,
        keyword=keyword,
        date_range=date_range,
        limit=limit
    )

    return jsonify({
        "success": True,
        "data": result,
        "timestamp": datetime.now().isoformat()
    })


@bp.route("/system/monitoring/api/alerts/config", methods=["POST"])
@login_required
@admin_required
def update_alert_config():
    """Cập nhật cấu hình kênh thông báo cảnh báo lỗi tự động (Telegram / Discord / Slack)."""
    data = request.get_json(silent=True) or request.form.to_dict()

    enabled = data.get("enabled")
    if isinstance(enabled, str):
        enabled = enabled.lower() in ("1", "true", "on", "yes")
    elif enabled is None:
        enabled = "ALERT_NOTIFICATIONS_ENABLED" in request.form

    config_payload = {
        "enabled": bool(enabled),
        "channels": data.get("channels", "all"),
        "min_severity": data.get("min_severity", "CRITICAL"),
        "cooldown_seconds": int(data.get("cooldown_seconds", 60)),
        "telegram_bot_token": data.get("telegram_bot_token", ""),
        "telegram_chat_id": data.get("telegram_chat_id", ""),
        "discord_webhook_url": data.get("discord_webhook_url", ""),
        "slack_webhook_url": data.get("slack_webhook_url", ""),
    }

    alert_service.save_alert_config(config_payload)
    log_audit_action(
        current_user.id,
        "UPDATE_ALERT_CONFIG",
        "SystemSetting",
        None,
        f"Cập nhật cấu hình kênh cảnh báo (Enabled: {enabled}, Channels: {config_payload['channels']})"
    )

    if request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"success": True, "message": "Đã lưu cấu hình cảnh báo thành công."})

    flash("Đã cập nhật cấu hình hệ thống cảnh báo sự cố.", "success")
    return redirect(url_for("admin.system_monitoring"))


@bp.route("/system/monitoring/api/alerts/test", methods=["POST"])
@login_required
@admin_required
def test_alert_notification():
    """Bắn thông báo thử nghiệm tới các kênh webhook đã cấu hình."""
    data = request.get_json(silent=True) or {}
    channel = data.get("channel") or request.form.get("channel", "all")
    custom_msg = data.get("message") or request.form.get("message")

    res = alert_service.send_test_alert(channel=channel, custom_message=custom_msg)
    log_audit_action(
        current_user.id,
        "TEST_ALERT_NOTIFICATION",
        "SystemAlert",
        None,
        f"Gửi cảnh báo thử nghiệm tới kênh {channel}: Kết quả {res.get('success')}"
    )

    return jsonify(res)


@bp.route("/system/monitoring/api/logs/rotate", methods=["POST"])
@login_required
@admin_required
def rotate_log_route():
    """Xoay vòng và nén file log thành tệp .gz."""
    data = request.get_json(silent=True) or {}
    filename = data.get("filename") or request.form.get("filename", "app.log")

    res = log_analysis_service.rotate_log_file(filename)
    if res.get("success"):
        log_audit_action(current_user.id, "ROTATE_LOG", "LogFile", None, f"Xoay vòng và nén file {filename}")
    return jsonify(res)


@bp.route("/system/monitoring/api/logs/cleanup", methods=["POST"])
@login_required
@admin_required
def cleanup_logs_route():
    """Dọn dẹp các tệp lưu trữ nhật ký cũ hơn số ngày cấu hình."""
    data = request.get_json(silent=True) or {}
    days = data.get("days") or request.form.get("days")
    days_int = int(days) if days else None

    res = log_analysis_service.cleanup_expired_log_archives(retention_days=days_int)
    log_audit_action(
        current_user.id,
        "CLEANUP_EXPIRED_LOGS",
        "LogArchive",
        None,
        f"Dọn dẹp {res.get('deleted_count')} tệp log lưu trữ cũ (Giải phóng {res.get('freed_mb')} MB)"
    )
    return jsonify(res)


@bp.route("/system/monitoring/export-logs", methods=["GET"])
@login_required
@admin_required
def export_filtered_logs():
    """Xuất nhật ký lọc ra tệp văn bản đính kèm để tải về."""
    filename = request.args.get("filename", "ALL")
    level = request.args.get("level", "ALL")
    keyword = request.args.get("keyword", "")
    date_range = request.args.get("date_range", "all")

    result = log_analysis_service.search_and_analyze_logs(
        filename=filename,
        level=level,
        keyword=keyword,
        date_range=date_range,
        limit=2000
    )

    lines = []
    lines.append(f"# EnglishMate System Log Export")
    lines.append(f"# Exported At: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"# Filter: File={filename}, Level={level}, Keyword={keyword}, Range={date_range}")
    lines.append(f"# Total Matches: {result.get('matching_count')}")
    lines.append("=" * 80)
    lines.append("")

    for entry in result.get("entries", []):
        lines.append(f"[{entry['timestamp']}] [{entry['level']}] [{entry['source_file']}] {entry['message']}")

    content = "\n".join(lines)
    export_filename = f"englishmate_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

    return Response(
        content,
        mimetype="text/plain",
        headers={"Content-Disposition": f"attachment;filename={export_filename}"}
    )
