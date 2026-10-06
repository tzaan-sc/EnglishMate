"""
Admin Helpdesk Support Ticket Management Routes
===============================================
Mục 15.3: Ticket System Admin Interface
- GET  /admin/tickets: Bảng điều khiển quản lý và xử lý phiếu hỗ trợ học viên
- GET  /admin/tickets/<id>: Chi tiết phiếu hỗ trợ & thông tin lỗi Trace ID
- POST /admin/tickets/<id>/reply: Gửi phản hồi Admin và cập nhật trạng thái
- POST /admin/tickets/<id>/status: Chuyển nhanh trạng thái phiếu
"""

from datetime import datetime
from flask import render_template, request, jsonify, flash, redirect, url_for
from flask_login import current_user
from sqlalchemy import desc

from ...extensions import db
from . import bp
from .utils import admin_required, log_audit_action
from .models import SupportTicket, SystemErrorLog, now


@bp.get("/tickets")
@bp.get("/support/tickets")
@admin_required
def admin_tickets_dashboard():
    """Bảng điều khiển quản lý phiếu hỗ trợ người dùng."""
    page = request.args.get("page", 1, type=int)
    search = request.args.get("search", "").strip() or None
    status = request.args.get("status", "").strip().upper() or None
    category = request.args.get("category", "").strip().upper() or None
    priority = request.args.get("priority", "").strip().upper() or None

    query = SupportTicket.query

    if status:
        query = query.filter(SupportTicket.status == status)
    if category:
        query = query.filter(SupportTicket.category == category)
    if priority:
        query = query.filter(SupportTicket.priority == priority)
    if search:
        s = f"%{search}%"
        query = query.filter(
            (SupportTicket.ticket_code.ilike(s))
            | (SupportTicket.title.ilike(s))
            | (SupportTicket.email.ilike(s))
            | (SupportTicket.name.ilike(s))
            | (SupportTicket.trace_id.ilike(s))
        )

    # Thống kê nhanh
    open_count = SupportTicket.query.filter_by(status="OPEN").count()
    in_progress_count = SupportTicket.query.filter_by(status="IN_PROGRESS").count()
    resolved_count = SupportTicket.query.filter_by(status="RESOLVED").count()
    urgent_count = SupportTicket.query.filter(SupportTicket.priority.in_(["HIGH", "URGENT"]), SupportTicket.status != "RESOLVED").count()

    # Sắp xếp: Ưu tiên OPEN/IN_PROGRESS và mới nhất
    query = query.order_by(
        SupportTicket.status == "RESOLVED",
        SupportTicket.status == "CLOSED",
        SupportTicket.priority == "URGENT",
        SupportTicket.created_at.desc()
    )

    pagination = query.paginate(page=page, per_page=15, error_out=False)

    return render_template(
        "admin/tickets.html",
        tickets=pagination.items,
        pagination=pagination,
        open_count=open_count,
        in_progress_count=in_progress_count,
        resolved_count=resolved_count,
        urgent_count=urgent_count,
        search=search,
        status=status,
        category=category,
        priority=priority
    )


@bp.get("/tickets/<int:ticket_id>")
@admin_required
def get_ticket_detail_api(ticket_id):
    """API JSON lấy thông tin chi tiết của một phiếu hỗ trợ."""
    ticket = db.session.get(SupportTicket, ticket_id)
    if not ticket:
        return jsonify({"success": False, "error": "Không tìm thấy phiếu hỗ trợ."}), 404

    # Tra cứu lỗi liên quan nếu có trace_id
    related_error = None
    if ticket.trace_id:
        err_log = SystemErrorLog.query.filter_by(error_id=ticket.trace_id).first()
        if err_log:
            related_error = {
                "error_id": err_log.error_id,
                "exception_type": err_log.exception_type,
                "error_message": err_log.error_message,
                "status_code": err_log.status_code,
                "route": err_log.route,
                "created_at": err_log.created_at_vn.strftime("%d/%m/%Y %H:%M:%S") if err_log.created_at_vn else None,
            }

    return jsonify({
        "success": True,
        "ticket": {
            "id": ticket.id,
            "ticket_code": ticket.ticket_code,
            "user_id": ticket.user_id,
            "name": ticket.name or (ticket.user.username if ticket.user else "Khách"),
            "email": ticket.email,
            "phone": ticket.phone,
            "category": ticket.category,
            "category_label": ticket.category_label,
            "priority": ticket.priority,
            "priority_badge_class": ticket.priority_badge_class,
            "title": ticket.title,
            "description": ticket.description,
            "trace_id": ticket.trace_id,
            "status": ticket.status,
            "status_badge_class": ticket.status_badge_class,
            "admin_reply": ticket.admin_reply,
            "created_at": ticket.created_at_vn.strftime("%d/%m/%Y %H:%M:%S") if ticket.created_at_vn else None,
            "resolved_at": ticket.resolved_at_vn.strftime("%d/%m/%Y %H:%M:%S") if ticket.resolved_at_vn else None,
            "related_error": related_error
        }
    })


@bp.post("/tickets/<int:ticket_id>/reply")
@admin_required
def reply_ticket_route(ticket_id):
    """Admin gửi phản hồi và cập nhật trạng thái phiếu hỗ trợ."""
    ticket = db.session.get(SupportTicket, ticket_id)
    if not ticket:
        if request.is_json:
            return jsonify({"success": False, "error": "Không tìm thấy phiếu hỗ trợ."}), 404
        flash("Không tìm thấy phiếu hỗ trợ.", "danger")
        return redirect(url_for("admin.admin_tickets_dashboard"))

    data = request.get_json(silent=True) or request.form
    reply_text = (data.get("admin_reply") or data.get("reply") or "").strip()
    new_status = (data.get("status") or "IN_PROGRESS").strip().upper()

    if reply_text:
        ticket.admin_reply = reply_text
    ticket.status = new_status
    ticket.admin_id = current_user.id
    ticket.updated_at = now()

    if new_status in ("RESOLVED", "CLOSED"):
        ticket.resolved_at = now()

    db.session.commit()

    log_audit_action(
        user_id=current_user.id,
        action="REPLY_SUPPORT_TICKET",
        target_type="SUPPORT_TICKET",
        target_id=ticket.ticket_code,
        details=f"Phản hồi phiếu hỗ trợ {ticket.ticket_code} (Trạng thái: {new_status})"
    )

    # Gửi email thông báo cho người dùng nếu có cấu hình SMTP
    try:
        from .email_service import enqueue_email
        enqueue_email(
            to_email=ticket.email,
            subject=f"[EnglishMate] Phản hồi phiếu hỗ trợ #{ticket.ticket_code}: {ticket.title}",
            html_content=f"""<div style="font-family: sans-serif; padding: 20px; border: 1px solid #e2e8f0; border-radius: 8px;">
                <h3 style="color: #4f46e5;">EnglishMate Support Center</h3>
                <p>Xin chào <strong>{ticket.name or 'bạn'}</strong>,</p>
                <p>Phiếu hỗ trợ <strong>#{ticket.ticket_code}</strong> của bạn đã có phản hồi mới từ đội ngũ kỹ thuật:</p>
                <div style="background: #f8fafc; padding: 15px; border-left: 4px solid #4f46e5; margin: 15px 0;">
                    {reply_text}
                </div>
                <p>Trạng thái hiện tại: <strong>{new_status}</strong></p>
                <p>Bạn có thể tra cứu trực tiếp tại website EnglishMate mục Hỗ trợ.</p>
            </div>""",
            email_type="TICKET_REPLY",
            admin_id=current_user.id,
            async_send=True
        )
    except Exception:
        pass

    if request.is_json:
        return jsonify({
            "success": True,
            "message": f"Đã gửi phản hồi cho phiếu #{ticket.ticket_code} thành công.",
            "ticket_code": ticket.ticket_code,
            "status": ticket.status
        })

    flash(f"Đã phản hồi phiếu #{ticket.ticket_code} thành công!", "success")
    return redirect(url_for("admin.admin_tickets_dashboard"))
