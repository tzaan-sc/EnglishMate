"""
Admin Error Recovery, Self-Healing & Circuit Breaker Routes
===========================================================
Mục 15.2: Error Recovery Admin Dashboard & Control APIs
- GET  /admin/system/recovery: Giao diện quản trị Tự phục hồi hệ thống & Trạng thái Circuit Breakers
- POST /admin/system/recovery/diagnose: Kích hoạt chẩn đoán & tự khôi phục dịch vụ
- POST /admin/system/recovery/circuit-breakers/<name>/reset: Đóng lại mạch (Reset CLOSED)
- POST /admin/system/recovery/circuit-breakers/<name>/trip: Ngắt mạch khẩn cấp (Force OPEN)
"""

from flask import render_template, request, jsonify, flash, redirect, url_for
from flask_login import current_user

from . import bp
from .utils import admin_required, log_audit_action
from .error_recovery_service import (
    circuit_breaker_registry,
    run_system_recovery_diagnostics,
    recover_database_connection,
    recover_zombie_tasks,
    recover_cache_service,
)


@bp.get("/system/recovery")
@bp.get("/recovery")
@admin_required
def system_recovery_dashboard():
    """Giao diện Quản trị Tự Khôi phục Hệ thống & Circuit Breakers (Error Recovery)."""
    diagnostics = run_system_recovery_diagnostics(force_recovery=False)
    breakers = circuit_breaker_registry.get_all_statuses()

    return render_template(
        "admin/recovery.html",
        diagnostics=diagnostics,
        breakers=breakers
    )


@bp.post("/system/recovery/diagnose")
@bp.post("/recovery/diagnose")
@admin_required
def run_recovery_diagnostics_api():
    """API Chạy quy trình Tự động Chẩn đoán & Phục hồi Hệ thống (Self-Healing)."""
    force = request.form.get("force") in ("1", "true", "True") or (request.get_json(silent=True) or {}).get("force", False)
    res = run_system_recovery_diagnostics(force_recovery=force)

    log_audit_action(
        user_id=current_user.id,
        action="RUN_SYSTEM_SELF_HEALING",
        target_type="SYSTEM_RECOVERY",
        target_id="ALL",
        details=f"Chạy chẩn đoán tự phục hồi hệ thống (Trạng thái: {res.get('status')})"
    )

    if request.is_json:
        return jsonify(res)

    flash("Đã thực hiện xong quy trình tự phục hồi và kiểm tra hệ thống.", "success")
    return redirect(url_for("admin.system_recovery_dashboard"))


@bp.post("/system/recovery/circuit-breakers/<string:name>/reset")
@admin_required
def reset_circuit_breaker_route(name):
    """Admin đóng mạch Circuit Breaker về trạng thái CLOSED."""
    breaker = circuit_breaker_registry.get(name)
    if not breaker:
        return jsonify({"success": False, "error": "Không tìm thấy Circuit Breaker."}), 404

    breaker.reset()

    log_audit_action(
        user_id=current_user.id,
        action="RESET_CIRCUIT_BREAKER",
        target_type="CIRCUIT_BREAKER",
        target_id=name,
        details=f"Đóng mạch Circuit Breaker '{name}' về CLOSED"
    )

    if request.is_json:
        return jsonify({"success": True, "message": f"Đã đóng mạch '{name}' thành công.", "status": breaker.get_status()})

    flash(f"Đã đóng mạch '{name}' thành công.", "success")
    return redirect(url_for("admin.system_recovery_dashboard"))


@bp.post("/system/recovery/circuit-breakers/<string:name>/trip")
@admin_required
def trip_circuit_breaker_route(name):
    """Admin chủ động ngắt mạch (Force OPEN) để cách ly dịch vụ lỗi."""
    breaker = circuit_breaker_registry.get(name)
    if not breaker:
        return jsonify({"success": False, "error": "Không tìm thấy Circuit Breaker."}), 404

    breaker.trip(duration_seconds=60.0)

    log_audit_action(
        user_id=current_user.id,
        action="TRIP_CIRCUIT_BREAKER",
        target_type="CIRCUIT_BREAKER",
        target_id=name,
        details=f"Ngắt mạch khẩn cấp Circuit Breaker '{name}' (OPEN)"
    )

    if request.is_json:
        return jsonify({"success": True, "message": f"Đã ngắt mạch '{name}' khẩn cấp.", "status": breaker.get_status()})

    flash(f"Đã ngắt mạch '{name}' khẩn cấp trong 60s.", "warning")
    return redirect(url_for("admin.system_recovery_dashboard"))
