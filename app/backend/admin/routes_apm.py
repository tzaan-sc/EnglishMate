"""
APM & Performance Optimization Admin Routes.
Provides routes for monitoring application performance, response latencies,
throughput, slowest endpoints, and system resource usage.
"""

from flask import render_template, jsonify, request, flash, redirect, url_for, Response, send_file
from flask_login import login_required, current_user
import json
from datetime import datetime

from . import bp
from .utils import admin_required
from .apm_service import apm_monitor


@bp.route("/system/apm", methods=["GET"])
@login_required
@admin_required
def system_apm():
    """Trang tổng quan giám sát hiệu năng hệ thống (APM Dashboard)."""
    summary = apm_monitor.get_summary()
    slow_endpoints = apm_monitor.get_slowest_endpoints(limit=15)
    recent_slow = apm_monitor.get_recent_slow_requests(limit=30)
    recent_requests = apm_monitor.get_recent_requests(limit=50)

    return render_template(
        "admin/apm_dashboard.html",
        summary=summary,
        slow_endpoints=slow_endpoints,
        recent_slow=recent_slow,
        recent_requests=recent_requests,
        active_tab="apm",
    )


@bp.route("/system/apm/api/metrics", methods=["GET"])
@login_required
@admin_required
def apm_metrics_api():
    """API trả về dữ liệu số liệu APM thời gian thực dạng JSON."""
    summary = apm_monitor.get_summary()
    slow_endpoints = apm_monitor.get_slowest_endpoints(limit=20)
    recent_slow = apm_monitor.get_recent_slow_requests(limit=50)
    recent_requests = apm_monitor.get_recent_requests(limit=50)

    return jsonify({
        "success": True,
        "summary": summary,
        "slow_endpoints": slow_endpoints,
        "recent_slow": recent_slow,
        "recent_requests": recent_requests,
        "timestamp": datetime.now().isoformat(),
    })


@bp.route("/system/apm/api/reset", methods=["POST"])
@login_required
@admin_required
def apm_reset_metrics():
    """Đặt lại toàn bộ số liệu thống kê APM về 0."""
    apm_monitor.reset_metrics()
    if request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"success": True, "message": "Đã thiết lập lại số liệu APM thành công."})
    flash("Đã thiết lập lại toàn bộ số liệu giám sát APM.", "success")
    return redirect(url_for("admin.system_apm"))


@bp.route("/system/apm/export", methods=["GET"])
@login_required
@admin_required
def apm_export_report():
    """Xuất báo cáo số liệu hiệu năng hệ thống dạng tệp JSON."""
    summary = apm_monitor.get_summary()
    slow_endpoints = apm_monitor.get_slowest_endpoints(limit=50)
    recent_slow = apm_monitor.get_recent_slow_requests(limit=100)

    report_data = {
        "report_type": "EnglishMate APM Performance Report",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "summary": summary,
        "slow_endpoints": slow_endpoints,
        "recent_slow_requests": recent_slow,
    }

    json_str = json.dumps(report_data, indent=2, ensure_ascii=False)
    filename = f"apm_performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    return Response(
        json_str,
        mimetype="application/json",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )
