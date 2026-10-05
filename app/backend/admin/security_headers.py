from typing import Any, Dict, Optional
from flask import request
from .models import SystemConfig
from .utils import log_audit_action

DEFAULT_CSP_POLICY = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://unpkg.com; "
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net; "
    "font-src 'self' data: https://fonts.gstatic.com https://cdn.jsdelivr.net; "
    "img-src 'self' data: blob: https:; "
    "media-src 'self' blob: data: https:; "
    "connect-src 'self' https:; "
    "frame-ancestors 'self';"
)


def get_security_headers_config() -> Dict[str, Any]:
    """Lấy cấu hình các Security Headers hiện tại từ SystemConfig."""
    is_enabled = SystemConfig.is_feature_enabled("SECURITY_HEADERS_ENABLED", default=True)
    csp_enabled = SystemConfig.is_feature_enabled("SECURITY_CSP_ENABLED", default=True)
    hsts_enabled = SystemConfig.is_feature_enabled("SECURITY_HSTS_ENABLED", default=False)
    frame_options = SystemConfig.get_config("SECURITY_FRAME_OPTIONS", default="SAMEORIGIN")
    referrer_policy = SystemConfig.get_config("SECURITY_REFERRER_POLICY", default="strict-origin-when-cross-origin")
    custom_csp = SystemConfig.get_config("SECURITY_CUSTOM_CSP", default="")

    return {
        "SECURITY_HEADERS_ENABLED": is_enabled,
        "SECURITY_CSP_ENABLED": csp_enabled,
        "SECURITY_HSTS_ENABLED": hsts_enabled,
        "SECURITY_FRAME_OPTIONS": frame_options,
        "SECURITY_REFERRER_POLICY": referrer_policy,
        "SECURITY_CUSTOM_CSP": custom_csp,
    }


def save_security_headers_config(settings: Dict[str, Any], admin_id: Optional[int] = None) -> Dict[str, Any]:
    """Cập nhật các thông số bảo vệ HTTP Security Headers."""
    if "SECURITY_HEADERS_ENABLED" in settings:
        val = settings["SECURITY_HEADERS_ENABLED"]
        is_active = val if isinstance(val, bool) else str(val).lower() in ("true", "1", "on", "yes")
        SystemConfig.set_feature_status("SECURITY_HEADERS_ENABLED", is_active, description="Bật/Tắt bộ Security Headers toàn hệ thống", category="SECURITY")

    if "SECURITY_CSP_ENABLED" in settings:
        val = settings["SECURITY_CSP_ENABLED"]
        is_active = val if isinstance(val, bool) else str(val).lower() in ("true", "1", "on", "yes")
        SystemConfig.set_feature_status("SECURITY_CSP_ENABLED", is_active, description="Bật Content-Security-Policy (CSP)", category="SECURITY")

    if "SECURITY_HSTS_ENABLED" in settings:
        val = settings["SECURITY_HSTS_ENABLED"]
        is_active = val if isinstance(val, bool) else str(val).lower() in ("true", "1", "on", "yes")
        SystemConfig.set_feature_status("SECURITY_HSTS_ENABLED", is_active, description="Bật Strict-Transport-Security (HSTS)", category="SECURITY")

    if "SECURITY_FRAME_OPTIONS" in settings:
        val = str(settings["SECURITY_FRAME_OPTIONS"]).strip().upper()
        if val not in ("SAMEORIGIN", "DENY"):
            val = "SAMEORIGIN"
        SystemConfig.set_config("SECURITY_FRAME_OPTIONS", val, description="Chính sách X-Frame-Options", category="SECURITY")

    if "SECURITY_REFERRER_POLICY" in settings:
        val = str(settings["SECURITY_REFERRER_POLICY"]).strip()
        SystemConfig.set_config("SECURITY_REFERRER_POLICY", val, description="Chính sách Referrer-Policy", category="SECURITY")

    if "SECURITY_CUSTOM_CSP" in settings:
        val = str(settings["SECURITY_CUSTOM_CSP"]).strip()
        SystemConfig.set_config("SECURITY_CUSTOM_CSP", val, description="Cấu hình CSP tùy chỉnh", category="SECURITY")

    log_audit_action(
        user_id=admin_id,
        action="UPDATE_SECURITY_HEADERS",
        target_type="SYSTEM_CONFIG",
        details=f"Cập nhật cấu hình HTTP Security Headers: {settings}"
    )

    return {
        "success": True,
        "config": get_security_headers_config(),
        "message": "Đã lưu cài đặt HTTP Security Headers thành công!"
    }


def apply_security_headers(response, req=None):
    """
    Middleware gắn các HTTP Security Headers tiêu chuẩn quốc tế vào mỗi Response.
    Bảo vệ chống lại các lỗ hổng:
    - MIME Sniffing: X-Content-Type-Options: nosniff
    - Clickjacking: X-Frame-Options: SAMEORIGIN
    - Reflected XSS: X-XSS-Protection: 1; mode=block
    - Data Leakage: Referrer-Policy: strict-origin-when-cross-origin
    - Feature Misuse: Permissions-Policy
    - XSS & Injection: Content-Security-Policy (CSP)
    - Protocol Downgrade: Strict-Transport-Security (HSTS)
    """
    req_obj = req or request
    try:
        cfg = get_security_headers_config()
    except Exception:
        # Fallback to default secure headers in case db is not initialized yet
        cfg = {
            "SECURITY_HEADERS_ENABLED": True,
            "SECURITY_CSP_ENABLED": True,
            "SECURITY_HSTS_ENABLED": False,
            "SECURITY_FRAME_OPTIONS": "SAMEORIGIN",
            "SECURITY_REFERRER_POLICY": "strict-origin-when-cross-origin",
            "SECURITY_CUSTOM_CSP": "",
        }

    if not cfg["SECURITY_HEADERS_ENABLED"]:
        return response

    # 1. Anti MIME-Sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"

    # 2. Anti Clickjacking (X-Frame-Options)
    response.headers["X-Frame-Options"] = cfg["SECURITY_FRAME_OPTIONS"] or "SAMEORIGIN"

    # 3. Reflected XSS Filter
    response.headers["X-XSS-Protection"] = "1; mode=block"

    # 4. Referrer Policy
    response.headers["Referrer-Policy"] = cfg["SECURITY_REFERRER_POLICY"] or "strict-origin-when-cross-origin"

    # 5. Permissions Policy (Allow microphone for Speaking features and IELTS simulations)
    response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=(self)"

    # 6. Content-Security-Policy (CSP)
    if cfg["SECURITY_CSP_ENABLED"]:
        csp_header = cfg["SECURITY_CUSTOM_CSP"] if cfg["SECURITY_CUSTOM_CSP"] else DEFAULT_CSP_POLICY
        response.headers["Content-Security-Policy"] = csp_header

    # 7. Strict-Transport-Security (HSTS)
    is_https = False
    if req_obj:
        is_https = req_obj.is_secure or req_obj.headers.get("X-Forwarded-Proto") == "https"

    if cfg["SECURITY_HSTS_ENABLED"] or is_https:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

    return response
