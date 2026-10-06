"""
User Error Handling, Support Hub, FAQ, Error Tutorials & Helpdesk Tickets
========================================================================
Mục 15.3:
- Support Contacts: Trang thông tin liên hệ hỗ trợ kỹ thuật rõ ràng (/support).
- Error Tutorials: Hướng dẫn tự khắc phục lỗi phổ biến (/tutorials/errors).
- FAQ Integration: Trang Câu hỏi thường gặp (/faq).
- Video Tutorials: Video clips ngắn hướng dẫn học tập (/tutorials/videos).
- Chat Support: Tiện ích hỗ trợ trực tuyến thời gian thực & AI Support Assistant (/api/support/chat).
- Ticket System: Hệ thống gửi và tra cứu phiếu hỗ trợ (/support/tickets, /api/support/tickets).
"""

import uuid
import re
from datetime import datetime, timezone, timedelta
from flask import render_template, request, jsonify, flash, redirect, url_for, g
from flask_login import current_user, login_required
from sqlalchemy import desc

from ...extensions import db
from ..admin.models import SupportTicket, SystemErrorLog, now
from . import bp


# ---------------------------------------------------------------------------
# FAQ DATA REPOSITORY
# ---------------------------------------------------------------------------
FAQ_ITEMS = [
    {
        "category": "ACCOUNT",
        "category_name": "Tài khoản & Đăng nhập",
        "icon": "person-circle",
        "question": "Tôi không nhận được mã xác thực OTP qua Email thì phải làm sao?",
        "answer": "Vui lòng kiểm tra kỹ mục Thư rác (Spam / Junk) hoặc tab Quảng cáo (Promotions) trong hộp thư. Nếu sau 60 giây chưa nhận được, bạn có thể nhấn nút 'Gửi lại mã OTP'. Đảm bảo địa chỉ email bạn nhập hoàn toàn chính xác."
    },
    {
        "category": "ACCOUNT",
        "category_name": "Tài khoản & Đăng nhập",
        "icon": "key",
        "question": "Làm thế nào để đổi mật khẩu hoặc lấy lại mật khẩu đã quên?",
        "answer": "Tại màn hình đăng nhập, chọn 'Quên mật khẩu', sau đó nhập email đã đăng ký. Hệ thống sẽ gửi mã bảo mật kèm liên kết để bạn đặt lại mật khẩu mới an toàn."
    },
    {
        "category": "LEARNING",
        "category_name": "Học tập & Luyện thi",
        "icon": "journal-text",
        "question": "Phương pháp ôn tập lặp lại ngắt quãng (Spaced Repetition) hoạt động như thế nào?",
        "answer": "EnglishMate tự động tính toán thời điểm bạn chuẩn bị quên từ vựng dựa trên thuật toán SRS (SuperMemo-2). Thẻ từ vựng sẽ được lên lịch ôn tập vào các ngày tiếp theo giúp bạn ghi nhớ sâu vào trí nhớ dài hạn."
    },
    {
        "category": "LEARNING",
        "category_name": "Học tập & Luyện thi",
        "icon": "trophy",
        "question": "Làm thế nào để duy trì chuỗi Streak học tập liên tục?",
        "answer": "Bạn chỉ cần hoàn thành mục tiêu học tập hàng ngày (học 5-10 từ vựng hoặc làm 1 bài kiểm tra). Nếu bận việc đột xuất, bạn có thể kích hoạt 'Bảo vệ chuỗi' (Streak Freeze) trong trang Hồ sơ cá nhân."
    },
    {
        "category": "TECHNICAL",
        "category_name": "Kỹ thuật & Thiết bị",
        "icon": "mic",
        "question": "Trình duyệt báo lỗi không thể truy cập Microphone khi luyện phát âm?",
        "answer": "Nhấp vào biểu tượng Ổ khóa hoặc Cài đặt trang web ở góc trái thanh địa chỉ trình duyệt, chọn Cho phép (Allow) quyền Microphone. Sau đó tải lại trang (F5)."
    },
    {
        "category": "TECHNICAL",
        "category_name": "Kỹ thuật & Thiết bị",
        "icon": "volume-up",
        "question": "Âm thanh phát âm không kêu trên điện thoại iPhone / iPad?",
        "answer": "Trên thiết bị iOS, hãy kiểm tra cần gạt rung/chuông ở cạnh sườn máy (không được để chế độ Im lặng) và nhấn vào màn hình ít nhất một lần để cấp quyền tự động phát âm thanh cho trình duyệt Safari."
    },
]

# ---------------------------------------------------------------------------
# ERROR TUTORIALS DATA REPOSITORY
# ---------------------------------------------------------------------------
ERROR_TUTORIALS = [
    {
        "slug": "microphone-permission",
        "title": "Khắc phục lỗi không cấp quyền Microphone khi luyện phát âm",
        "category": "Thiết bị & Âm thanh",
        "icon": "mic-fill",
        "badge": "Phổ biến nhất",
        "badge_color": "danger",
        "summary": "Hướng dẫn chi tiết cấp quyền Micro cho Google Chrome, Apple Safari, Microsoft Edge và điện thoại di động.",
        "steps": [
            "1. Nhìn lên thanh địa chỉ (URL) của trình duyệt, nhấp vào biểu tượng Ổ khóa 🔒 hoặc Cài đặt trang.",
            "2. Tìm mục 'Microphone' (hoặc 'Quyền truy cập Micro') và chuyển từ 'Chặn' sang 'Cho phép' (Allow).",
            "3. Nếu sử dụng Safari trên iPhone/iPad: Vào Cài đặt máy > Safari > Micro > Chọn 'Hỏi' hoặc 'Cho phép'.",
            "4. Tải lại trang học (nhấn Ctrl+F5 trên máy tính hoặc vuốt làm mới trên điện thoại).",
            "5. Nhấn lại nút Micro và thử phát âm một từ mẫu để kiểm tra thanh sóng âm."
        ]
    },
    {
        "slug": "otp-email-delay",
        "title": "Khắc phục lỗi không nhận được email mã xác thực OTP",
        "category": "Tài khoản & Email",
        "icon": "envelope-exclamation-fill",
        "badge": "Quan trọng",
        "badge_color": "warning",
        "summary": "Các bước kiểm tra hộp thư Spam, bộ lọc tường lửa và cơ chế gửi lại mã an toàn.",
        "steps": [
            "1. Mở hòm thư và kiểm tra kỹ trong các thư mục: Spam (Thư rác), Junk, Promotions (Quảng cáo) hoặc Updates.",
            "2. Tìm kiếm với từ khóa 'EnglishMate' trong thanh tìm kiếm hòm thư.",
            "3. Kiểm tra xem địa chỉ email nhập trên màn hình đăng ký đã chính xác từng ký tự hay chưa.",
            "4. Chờ hết 60 giây đếm ngược rồi nhấn 'Gửi lại mã OTP'.",
            "5. Nếu vẫn không nhận được sau 3 lần thử, hãy gửi phiếu hỗ trợ kèm Request Trace ID ở chân trang để kỹ thuật viên kiểm tra trực tiếp."
        ]
    },
    {
        "slug": "flashcard-offline-sync",
        "title": "Khắc phục lỗi Flashcard tải chậm hoặc mất kết nối mạng",
        "category": "Mạng & Dữ liệu",
        "icon": "wifi-off",
        "badge": "Hữu ích",
        "badge_color": "info",
        "summary": "Cách làm mới bộ nhớ đệm (Cache) và nạp lại dữ liệu thẻ từ vựng khi đường truyền chập chờn.",
        "steps": [
            "1. Kiểm tra kết nối Wifi / 4G trên thiết bị của bạn.",
            "2. Thực hiện xóa bộ nhớ cache trang web bằng tổ hợp phím Ctrl + Shift + R (Windows) hoặc Cmd + Shift + R (Mac).",
            "3. Hệ thống EnglishMate tự động lưu tiến độ vào LocalStorage, bài học của bạn sẽ không bị mất điểm.",
            "4. Đóng bớt các tab trình duyệt nặng hoặc ứng dụng chạy ngầm nếu bộ nhớ RAM máy bị đầy."
        ]
    },
    {
        "slug": "mobile-audio-autoplay",
        "title": "Khắc phục lỗi âm thanh phát âm không kêu trên trình duyệt Mobile",
        "category": "Trình duyệt Di động",
        "icon": "phone-fill",
        "badge": "Mẹo hay",
        "badge_color": "success",
        "summary": "Chính sách chặn Autoplay của iOS / Android và cách kích hoạt phát âm thanh một chạm.",
        "steps": [
            "1. Tắt chế độ 'Không làm phiền' (Do Not Disturb) và bật âm lượng media trên thiết bị.",
            "2. Đối với iPhone: Gạt cần gạt âm thanh sang vị trí Chuông (Ringer on).",
            "3. Chạm vào màn hình ít nhất 1 lần để trình duyệt cấp phép phát âm thanh SpeechSynthesis.",
            "4. Sử dụng trình duyệt Chrome hoặc Safari phiên bản mới nhất để đạt độ tương thích chuẩn nhất."
        ]
    }
]

# ---------------------------------------------------------------------------
# VIDEO TUTORIALS DATA REPOSITORY
# ---------------------------------------------------------------------------
VIDEO_TUTORIALS = [
    {
        "id": "vid-1",
        "title": "Lộ trình học tiếng Anh thông minh cho người mới bắt đầu",
        "duration": "03:45",
        "category": "Khởi động",
        "badge": "Người mới",
        "thumbnail": "https://images.unsplash.com/photo-1434030216411-0b793f4b4173?w=600&auto=format&fit=crop&q=80",
        "video_url": "https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ",
        "description": "Hướng dẫn tổng quan các tính năng cốt lõi: Học từ vựng theo chủ đề, Luyện phát âm AI, Ôn tập Flashcard và Thi thử TOEIC/THPT."
    },
    {
        "id": "vid-2",
        "title": "Bí quyết luyện phát âm chuẩn IPA cùng AI Assistant",
        "duration": "04:12",
        "category": "Phát âm AI",
        "badge": "Nâng cao",
        "thumbnail": "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?w=600&auto=format&fit=crop&q=80",
        "video_url": "https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ",
        "description": "Cách ghi âm giọng đọc, phân tích sóng âm và nhận phản hồi chi tiết từ AI để sửa từng âm tiết khó."
    },
    {
        "id": "vid-3",
        "title": "Cách tạo bộ Flashcard cá nhân & Tận dụng thuật toán SRS",
        "duration": "02:50",
        "category": "Từ vựng",
        "badge": "Mẹo học",
        "thumbnail": "https://images.unsplash.com/photo-1456513080510-7bf3a84b82f8?w=600&auto=format&fit=crop&q=80",
        "video_url": "https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ",
        "description": "Hướng dẫn tự tạo danh sách từ vựng yêu thích, chia sẻ bộ thẻ cùng bạn bè và ôn tập ngắt quãng thông minh."
    },
    {
        "id": "vid-4",
        "title": "Chiến thuật làm bài thi TOEIC 4 kỹ năng đạt điểm cao",
        "duration": "05:30",
        "category": "Luyện thi",
        "badge": "Chiến lược",
        "thumbnail": "https://images.unsplash.com/photo-1546410531-bb4caa6b424d?w=600&auto=format&fit=crop&q=80",
        "video_url": "https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ",
        "description": "Phân bổ thời gian làm bài, mẹo nghe Part 1-4 và chiến thuật đọc hiểu Part 7 giải thích chi tiết từng câu."
    }
]


# ===========================================================================
# 1. PUBLIC ROUTES: SUPPORT HUB, FAQ, TUTORIALS
# ===========================================================================

@bp.get("/support")
def support_center():
    """Trang Trung tâm Hỗ trợ & Trợ giúp Kỹ thuật (Support Center)."""
    trace_id = getattr(g, "request_id", "")
    return render_template(
        "main/support.html",
        faq_items=FAQ_ITEMS[:4],
        error_tutorials=ERROR_TUTORIALS,
        video_tutorials=VIDEO_TUTORIALS,
        trace_id=trace_id
    )


@bp.get("/faq")
def faq_page():
    """Trang Câu hỏi Thường gặp (FAQ)."""
    category_filter = request.args.get("category", "").strip().upper()
    search = request.args.get("q", "").strip().lower()

    filtered = FAQ_ITEMS
    if category_filter:
        filtered = [f for f in filtered if f["category"] == category_filter]
    if search:
        filtered = [
            f for f in filtered
            if search in f["question"].lower() or search in f["answer"].lower()
        ]

    return render_template(
        "main/faq.html",
        faq_items=filtered,
        all_count=len(FAQ_ITEMS),
        current_category=category_filter,
        search_query=search
    )


@bp.get("/tutorials/errors")
@bp.get("/support/troubleshooting")
def error_tutorials_page():
    """Trang Hướng dẫn Tự Khắc phục Lỗi Kỹ thuật Thường Gặp."""
    return render_template(
        "main/error_tutorials.html",
        tutorials=ERROR_TUTORIALS,
        trace_id=getattr(g, "request_id", "")
    )


@bp.get("/tutorials/videos")
def video_tutorials_page():
    """Trang Video Hướng dẫn Tương tác trên Nền tảng EnglishMate."""
    return render_template(
        "main/video_tutorials.html",
        videos=VIDEO_TUTORIALS
    )


# ===========================================================================
# 2. HELPDESK TICKET SYSTEM ROUTES
# ===========================================================================

@bp.get("/support/tickets")
def support_tickets_page():
    """Trang Gửi và Tra cứu Phiếu Yêu cầu Hỗ trợ (Tickets)."""
    user_tickets = []
    if current_user.is_authenticated:
        user_tickets = SupportTicket.query.filter_by(user_id=current_user.id).order_by(
            SupportTicket.created_at.desc()
        ).all()

    trace_id = request.args.get("trace_id") or getattr(g, "request_id", "")

    return render_template(
        "main/support_tickets.html",
        tickets=user_tickets,
        prefilled_trace_id=trace_id
    )


@bp.post("/api/support/tickets")
def create_support_ticket_api():
    """API Tạo Phiếu Hỗ trợ Mới."""
    data = request.get_json(silent=True) or request.form

    title = (data.get("title") or "").strip()
    description = (data.get("description") or "").strip()
    category = (data.get("category") or "TECHNICAL").strip().upper()
    priority = (data.get("priority") or "MEDIUM").strip().upper()
    trace_id = (data.get("trace_id") or getattr(g, "request_id", "") or "").strip()
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    phone = (data.get("phone") or "").strip()

    if current_user.is_authenticated:
        if not name:
            name = getattr(current_user, "name", "") or current_user.username
        if not email:
            email = current_user.email

    if not title:
        return jsonify({"success": False, "error": "Vui lòng nhập tiêu đề sự cố."}), 400
    if not description:
        return jsonify({"success": False, "error": "Vui lòng nhập mô tả chi tiết sự cố."}), 400
    if not email:
        return jsonify({"success": False, "error": "Vui lòng nhập địa chỉ email liên hệ."}), 400

    # Sinh mã phiếu định danh duy nhất (VD: TKT-202610-8F92)
    rand_code = uuid.uuid4().hex[:6].upper()
    ticket_code = f"TKT-{datetime.now().strftime('%y%m')}-{rand_code}"

    ticket = SupportTicket(
        ticket_code=ticket_code,
        user_id=current_user.id if current_user.is_authenticated else None,
        name=name[:100] if name else None,
        email=email[:120],
        phone=phone[:20] if phone else None,
        category=category,
        priority=priority,
        title=title[:255],
        description=description,
        trace_id=trace_id[:64] if trace_id else None,
        status="OPEN",
        created_at=now(),
        updated_at=now()
    )

    db.session.add(ticket)
    db.session.commit()

    # Bắn cảnh báo cho Admin qua Webhook / Alert nếu là lỗi khẩn cấp
    try:
        if priority in ("HIGH", "URGENT"):
            from ..admin.alert_service import alert_service
            alert_service.dispatch_alert_async({
                "type": "NEW_URGENT_TICKET",
                "ticket_code": ticket_code,
                "title": title,
                "email": email,
                "trace_id": trace_id,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
    except Exception:
        pass

    if request.is_json:
        return jsonify({
            "success": True,
            "ticket_code": ticket_code,
            "message": f"Phiếu hỗ trợ #{ticket_code} đã được gửi thành công. Kỹ thuật viên sẽ phản hồi trong vòng 24h."
        })

    flash(f"Đã gửi phiếu hỗ trợ thành công! Mã tra cứu của bạn là: {ticket_code}", "success")
    return redirect(url_for("main.support_tickets_page"))


@bp.get("/api/support/tickets/<string:ticket_code>")
def lookup_support_ticket_api(ticket_code):
    """API Tra cứu Chi tiết và Tiến độ Xử lý của Phiếu Hỗ trợ."""
    ticket = SupportTicket.query.filter_by(ticket_code=ticket_code.strip().upper()).first()
    if not ticket:
        return jsonify({"success": False, "error": "Không tìm thấy phiếu hỗ trợ với mã này."}), 404

    return jsonify({
        "success": True,
        "ticket": {
            "ticket_code": ticket.ticket_code,
            "title": ticket.title,
            "category": ticket.category,
            "category_label": ticket.category_label,
            "priority": ticket.priority,
            "priority_badge_class": ticket.priority_badge_class,
            "status": ticket.status,
            "status_badge_class": ticket.status_badge_class,
            "description": ticket.description,
            "trace_id": ticket.trace_id,
            "admin_reply": ticket.admin_reply,
            "created_at": ticket.created_at_vn.strftime("%d/%m/%Y %H:%M:%S") if ticket.created_at_vn else None,
            "resolved_at": ticket.resolved_at_vn.strftime("%d/%m/%Y %H:%M:%S") if ticket.resolved_at_vn else None,
        }
    })


# ===========================================================================
# 3. LIVE CHAT SUPPORT ASSISTANT API
# ===========================================================================

@bp.post("/api/support/chat")
def live_chat_assistant_api():
    """
    15.3. Chat Support: Bộ phản hồi tự động thông minh cho Live Chat Widget.
    Tự động nhận diện từ khóa lỗi và đưa ra giải pháp tức thì, hướng dẫn tra cứu hoặc hỗ trợ mở ticket.
    """
    data = request.get_json(silent=True) or request.form
    message = (data.get("message") or "").strip().lower()

    if not message:
        return jsonify({"success": False, "reply": "Xin chào! Mình có thể giúp gì cho bạn hôm nay?"})

    trace_id = getattr(g, "request_id", "")

    # Phân tích ý định người dùng bằng từ khóa
    if any(k in message for k in ["micro", "mic", "thu âm", "ghi âm", "phát âm"]):
        reply = (
            "🎤 **Về sự cố Microphone:**\n"
            "Bạn vui lòng kiểm tra biểu tượng Ổ khóa 🔒 trên thanh địa chỉ trình duyệt và chuyển quyền Micro sang 'Cho phép' (Allow).\n"
            "👉 Xem [Hướng dẫn cấp quyền Micro chi tiết](/tutorials/errors#microphone-permission)."
        )
        quick_actions = [
            {"label": "Xem hướng dẫn Micro", "url": "/tutorials/errors#microphone-permission"},
            {"label": "Tạo phiếu hỗ trợ", "action": "open_ticket_modal"}
        ]

    elif any(k in message for k in ["otp", "mã xác thực", "email", "không nhận được mail"]):
        reply = (
            "📧 **Về mã xác thực OTP:**\n"
            "Email có thể mất 30-60 giây để chuyển đến hoặc nằm trong mục **Spam / Quảng cáo**.\n"
            "Nếu sau 1 phút chưa có, bạn hãy bấm 'Gửi lại mã OTP'.\n"
            "👉 Xem [Hướng dẫn khắc phục sự cố Email OTP](/tutorials/errors#otp-email-delay)."
        )
        quick_actions = [
            {"label": "Xem hướng dẫn OTP", "url": "/tutorials/errors#otp-email-delay"},
            {"label": "Gửi phiếu hỗ trợ", "action": "open_ticket_modal"}
        ]

    elif any(k in message for k in ["streak", "chuỗi", "đóng băng", "freeze"]):
        reply = (
            "🔥 **Về Chuỗi Streak:**\n"
            "Bạn có thể dùng tính năng 'Bảo vệ chuỗi' (Streak Freeze) trong mục Cá nhân để giữ chuỗi ngày học nếu bận việc đột xuất!"
        )
        quick_actions = [
            {"label": "Đến trang Hồ sơ cá nhân", "url": "/profile"}
        ]

    elif any(k in message for k in ["mã lỗi", "trace id", "lỗi 500", "lỗi 404", "crash", "sự cố"]):
        reply = (
            f"🛠️ **Tra cứu sự cố kỹ thuật:**\n"
            f"Mã phiên làm việc hiện tại của bạn là: `{trace_id}`.\n"
            f"Bạn có thể sao chép mã này và gửi phiếu hỗ trợ để Admin kiểm tra log trong tích tắc!"
        )
        quick_actions = [
            {"label": "Gửi phiếu kèm Trace ID", "action": "open_ticket_modal", "trace_id": trace_id}
        ]

    elif any(k in message for k in ["video", "clip", "hướng dẫn học", "cách học"]):
        reply = (
            "🎬 **Video Hướng dẫn Học tập:**\n"
            "EnglishMate có sẵn các video clip ngắn hướng dẫn cách học phát âm IPA, tạo Flashcard và luyện thi TOEIC.\n"
            "👉 Xem [Thư viện Video Hướng dẫn](/tutorials/videos)."
        )
        quick_actions = [
            {"label": "Xem Video Hướng dẫn", "url": "/tutorials/videos"}
        ]

    elif any(k in message for k in ["ticket", "phiếu", "liên hệ", "hotline", "hỗ trợ"]):
        reply = (
            "🎫 **Hỗ trợ Kỹ thuật viên:**\n"
            "Bạn có thể gửi phiếu yêu cầu hỗ trợ (Helpdesk Ticket) hoặc gọi hotline: **1900 6868** (8:00 - 22:00 hàng ngày)."
        )
        quick_actions = [
            {"label": "Gửi phiếu hỗ trợ", "action": "open_ticket_modal"},
            {"label": "Tra cứu phiếu đã gửi", "url": "/support/tickets"}
        ]

    else:
        reply = (
            "🤖 **Trợ lý EnglishMate:**\n"
            "Cảm ơn bạn đã nhắn tin! Bạn có thể xem nhanh các chủ đề phổ biến dưới đây hoặc gửi phiếu hỗ trợ trực tiếp cho ban quản trị."
        )
        quick_actions = [
            {"label": "Câu hỏi thường gặp (FAQ)", "url": "/faq"},
            {"label": "Hướng dẫn tự sửa lỗi", "url": "/tutorials/errors"},
            {"label": "Gửi phiếu hỗ trợ", "action": "open_ticket_modal"}
        ]

    return jsonify({
        "success": True,
        "reply": reply,
        "trace_id": trace_id,
        "quick_actions": quick_actions
    })
