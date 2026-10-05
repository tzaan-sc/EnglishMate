import json
import time
from collections import deque
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple
from flask import Request, Response, redirect, request
from .models import SystemConfig, SystemSetting
from .utils import log_audit_action

# In-Memory Cache for High-Speed IP Filter Checks (Avoid DB query on every HTTP request)
_BLACKLISTED_IPS: Dict[str, Dict[str, Any]] = {}
_ADMIN_WHITELISTED_IPS: Set[str] = set()

# Real-Time Network Traffic Window (Last 500 requests for RPM and traffic monitoring)
_TRAFFIC_WINDOW: deque = deque(maxlen=1000)
_BLOCKED_REQUESTS_COUNT = 0


def get_client_ip(req: Optional[Request] = None) -> str:
    """Lấy địa chỉ IP thực của client từ các header Proxy / CDN (Cloudflare, Nginx) hoặc remote_addr."""
    if req is None:
        try:
            req = request
        except Exception:
            return "127.0.0.1"

    # 1. Cloudflare CF-Connecting-IP
    cf_ip = req.headers.get("CF-Connecting-IP")
    if cf_ip:
        return cf_ip.strip()

    # 2. X-Forwarded-For (Lấy IP đầu tiên trong chuỗi forwarded)
    x_forwarded = req.headers.get("X-Forwarded-For")
    if x_forwarded:
        ips = [ip.strip() for ip in x_forwarded.split(",")]
        if ips:
            return ips[0]

    # 3. X-Real-IP
    x_real = req.headers.get("X-Real-IP")
    if x_real:
        return x_real.strip()

    return req.remote_addr or "127.0.0.1"


# ---------------------------------------------------------------------------
# 1. IP BLACKLISTING & WHITELISTING (MỤC 11.12 & 11.13)
# ---------------------------------------------------------------------------

def is_ip_blacklisted(ip: str) -> bool:
    """Kiểm tra xem địa chỉ IP có nằm trong danh sách đen (Blacklist) hay không."""
    if not ip:
        return False

    now = time.time()
    if ip in _BLACKLISTED_IPS:
        entry = _BLACKLISTED_IPS[ip]
        expires_at = entry.get("expires_at")
        if expires_at and now > expires_at:
            # Expired temporary blacklist
            _BLACKLISTED_IPS.pop(ip, None)
            return False
        return True

    # Fallback to SystemConfig if in-memory missed
    try:
        blacklist_raw = SystemConfig.get_config("NETWORK_IP_BLACKLIST", default="")
        if blacklist_raw:
            blocked_set = {i.strip() for i in blacklist_raw.split(",") if i.strip()}
            if ip in blocked_set:
                _BLACKLISTED_IPS[ip] = {"reason": "Configured blacklist", "added_at": now, "expires_at": None}
                return True
    except Exception:
        pass

    return False


def is_admin_ip_allowed(ip: str) -> bool:
    """
    Kiểm tra xem địa chỉ IP có được phép truy cập trang Quản trị Admin không (IP Whitelist).
    - Nếu Whitelist bị tắt (mặc định): Cho phép tất cả IP.
    - Nếu Whitelist được bật: Chỉ cho phép IP có trong danh sách.
    """
    try:
        whitelist_enabled = SystemConfig.is_feature_enabled("ADMIN_IP_WHITELIST_ENABLED", default=False)
        if not whitelist_enabled:
            return True
    except Exception:
        return True

    # Localhost / Loopback always allowed
    if ip in ("127.0.0.1", "::1", "localhost"):
        return True

    if ip in _ADMIN_WHITELISTED_IPS:
        return True

    try:
        whitelist_raw = SystemConfig.get_config("ADMIN_IP_WHITELIST", default="")
        if whitelist_raw:
            allowed_set = {i.strip() for i in whitelist_raw.split(",") if i.strip()}
            _ADMIN_WHITELISTED_IPS.update(allowed_set)
            return ip in allowed_set
    except Exception:
        pass

    return False


def add_ip_blacklist(ip: str, reason: str = "Thao tác quản trị viên", duration_minutes: Optional[int] = None, admin_id: Optional[int] = None) -> Dict[str, Any]:
    """Thêm một địa chỉ IP vào danh sách chặn."""
    ip_clean = ip.strip()
    if not ip_clean:
        return {"success": False, "error": "IP không hợp lệ"}

    now = time.time()
    expires_at = (now + duration_minutes * 60) if duration_minutes else None
    _BLACKLISTED_IPS[ip_clean] = {
        "reason": reason,
        "added_at": now,
        "expires_at": expires_at,
        "expires_at_str": datetime.fromtimestamp(expires_at, tz=timezone.utc).strftime("%d/%m/%Y %H:%M:%S") if expires_at else "Vĩnh viễn"
    }

    # Persist in SystemConfig
    try:
        current_raw = SystemConfig.get_config("NETWORK_IP_BLACKLIST", default="")
        current_set = {i.strip() for i in current_raw.split(",") if i.strip()}
        current_set.add(ip_clean)
        SystemConfig.set_config("NETWORK_IP_BLACKLIST", ",".join(sorted(current_set)), description="Danh sách IP bị chặn (IP Blacklist)", category="NETWORK")
    except Exception:
        pass

    log_audit_action(
        user_id=admin_id,
        action="ADD_IP_BLACKLIST",
        target_type="IP_RULE",
        details=f"Đưa IP {ip_clean} vào danh sách chặn (Lý do: {reason})"
    )

    return {"success": True, "ip": ip_clean, "message": f"Đã đưa IP {ip_clean} vào danh sách chặn thành công."}


def remove_ip_blacklist(ip: str, admin_id: Optional[int] = None) -> Dict[str, Any]:
    """Gỡ một địa chỉ IP khỏi danh sách chặn."""
    ip_clean = ip.strip()
    _BLACKLISTED_IPS.pop(ip_clean, None)

    try:
        current_raw = SystemConfig.get_config("NETWORK_IP_BLACKLIST", default="")
        current_set = {i.strip() for i in current_raw.split(",") if i.strip()}
        current_set.discard(ip_clean)
        SystemConfig.set_config("NETWORK_IP_BLACKLIST", ",".join(sorted(current_set)), description="Danh sách IP bị chặn (IP Blacklist)", category="NETWORK")
    except Exception:
        pass

    log_audit_action(
        user_id=admin_id,
        action="REMOVE_IP_BLACKLIST",
        target_type="IP_RULE",
        details=f"Gỡ IP {ip_clean} khỏi danh sách chặn"
    )

    return {"success": True, "ip": ip_clean, "message": f"Đã gỡ IP {ip_clean} khỏi danh sách chặn."}


def add_admin_ip_whitelist(ip: str, note: str = "", admin_id: Optional[int] = None) -> Dict[str, Any]:
    """Thêm một địa chỉ IP vào danh sách cho phép truy cập Admin (IP Whitelist)."""
    ip_clean = ip.strip()
    if not ip_clean:
        return {"success": False, "error": "IP không hợp lệ"}

    _ADMIN_WHITELISTED_IPS.add(ip_clean)

    try:
        current_raw = SystemConfig.get_config("ADMIN_IP_WHITELIST", default="")
        current_set = {i.strip() for i in current_raw.split(",") if i.strip()}
        current_set.add(ip_clean)
        SystemConfig.set_config("ADMIN_IP_WHITELIST", ",".join(sorted(current_set)), description="Danh sách IP được phép vào Admin (Admin IP Whitelist)", category="NETWORK")
    except Exception:
        pass

    log_audit_action(
        user_id=admin_id,
        action="ADD_ADMIN_IP_WHITELIST",
        target_type="IP_RULE",
        details=f"Thêm IP {ip_clean} vào danh sách Admin Whitelist ({note})" if note else f"Thêm IP {ip_clean} vào danh sách Admin Whitelist"
    )

    return {"success": True, "ip": ip_clean, "message": f"Đã thêm IP {ip_clean} vào danh sách Admin Whitelist."}


def remove_admin_ip_whitelist(ip: str, admin_id: Optional[int] = None) -> Dict[str, Any]:
    """Gỡ một địa chỉ IP khỏi danh sách cho phép truy cập Admin."""
    ip_clean = ip.strip()
    _ADMIN_WHITELISTED_IPS.discard(ip_clean)

    try:
        current_raw = SystemConfig.get_config("ADMIN_IP_WHITELIST", default="")
        current_set = {i.strip() for i in current_raw.split(",") if i.strip()}
        current_set.discard(ip_clean)
        SystemConfig.set_config("ADMIN_IP_WHITELIST", ",".join(sorted(current_set)), description="Danh sách IP được phép vào Admin (Admin IP Whitelist)", category="NETWORK")
    except Exception:
        pass

    log_audit_action(
        user_id=admin_id,
        action="REMOVE_ADMIN_IP_WHITELIST",
        target_type="IP_RULE",
        details=f"Gỡ IP {ip_clean} khỏi danh sách Admin Whitelist"
    )

    return {"success": True, "ip": ip_clean, "message": f"Đã gỡ IP {ip_clean} khỏi danh sách Admin Whitelist."}


# ---------------------------------------------------------------------------
# 2. HTTPS ENFORCEMENT (MỤC 11.8)
# ---------------------------------------------------------------------------

def is_https_enforced() -> bool:
    """Kiểm tra cấu hình bắt buộc chuyển hướng HTTPS."""
    try:
        return SystemConfig.is_feature_enabled("HTTPS_ENFORCEMENT_ENABLED", default=False)
    except Exception:
        return False


def handle_https_enforcement(req: Request) -> Optional[Response]:
    """Tự động chuyển hướng 301 sang giao thức HTTPS an toàn nếu request gửi qua HTTP thông thường."""
    if not is_https_enforced():
        return None

    # Skip local development loops unless forced
    client_ip = get_client_ip(req)
    if client_ip in ("127.0.0.1", "::1", "localhost"):
        return None

    # Check if request is already HTTPS
    if req.is_secure or req.headers.get("X-Forwarded-Proto", "").lower() == "https":
        return None

    # Redirect to HTTPS
    url = req.url.replace("http://", "https://", 1)
    return redirect(url, code=301)


# ---------------------------------------------------------------------------
# 3. CORS CONFIGURATION (MỤC 11.10)
# ---------------------------------------------------------------------------

def get_cors_allowed_origins() -> List[str]:
    """Lấy danh sách các domain được phép gọi API (CORS Allowed Origins)."""
    try:
        raw = SystemConfig.get_config("CORS_ALLOWED_ORIGINS", default="*")
        if not raw:
            return ["*"]
        return [o.strip() for o in raw.split(",") if o.strip()]
    except Exception:
        return ["*"]


def apply_cors_headers(response: Response, req: Optional[Request] = None) -> Response:
    """Gắn các HTTP header CORS cho các API endpoints nhằm bảo vệ truy vấn chéo nguồn an toàn."""
    allowed_origins = get_cors_allowed_origins()
    req_origin = req.headers.get("Origin") if req else None

    if "*" in allowed_origins:
        response.headers["Access-Control-Allow-Origin"] = "*"
    elif req_origin and req_origin in allowed_origins:
        response.headers["Access-Control-Allow-Origin"] = req_origin
        response.headers["Vary"] = "Origin"

    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-CSRFToken, X-Requested-With"
    response.headers["Access-Control-Max-Age"] = "86400"

    return response


# ---------------------------------------------------------------------------
# 4. NETWORK TRAFFIC & CONNECTION MONITORING (MỤC 11.15)
# ---------------------------------------------------------------------------

def record_network_traffic(path: str, ip: str, method: str, status_code: int, duration_ms: float = 0.0) -> None:
    """Ghi nhận lưu lượng và request vào sliding-window để phân tích thời gian thực."""
    now = time.time()
    _TRAFFIC_WINDOW.append({
        "timestamp": now,
        "path": path,
        "ip": ip,
        "method": method,
        "status_code": status_code,
        "duration_ms": duration_ms,
    })


def record_blocked_request() -> None:
    """Tăng biến đếm số lượng request bị chặn bởi IP Blacklist / Whitelist."""
    global _BLOCKED_REQUESTS_COUNT
    _BLOCKED_REQUESTS_COUNT += 1


def get_network_monitoring_stats() -> Dict[str, Any]:
    """Tổng hợp số liệu thống kê lưu lượng mạng, RPM, IP đồng thời và phân bố mã lỗi."""
    now = time.time()
    one_min_ago = now - 60
    ten_min_ago = now - 600

    recent_1m = [r for r in list(_TRAFFIC_WINDOW) if r["timestamp"] >= one_min_ago]
    recent_10m = [r for r in list(_TRAFFIC_WINDOW) if r["timestamp"] >= ten_min_ago]

    rpm = len(recent_1m)
    active_ips_1m = len(set(r["ip"] for r in recent_1m))
    active_ips_10m = len(set(r["ip"] for r in recent_10m))

    # Calculate status code distribution
    status_2xx = sum(1 for r in recent_10m if 200 <= r["status_code"] < 300)
    status_3xx = sum(1 for r in recent_10m if 300 <= r["status_code"] < 400)
    status_4xx = sum(1 for r in recent_10m if 400 <= r["status_code"] < 500)
    status_5xx = sum(1 for r in recent_10m if r["status_code"] >= 500)

    # Calculate avg latency
    avg_latency = round(sum(r["duration_ms"] for r in recent_1m) / max(1, len(recent_1m)), 1)

    # Top client IPs
    ip_counts: Dict[str, int] = {}
    for r in recent_10m:
        ip_counts[r["ip"]] = ip_counts.get(r["ip"], 0) + 1
    top_ips = sorted(ip_counts.items(), key=lambda x: x[1], reverse=True)[:5]

    return {
        "requests_per_minute": rpm,
        "active_ips_1m": active_ips_1m,
        "active_ips_10m": active_ips_10m,
        "total_tracked_requests": len(_TRAFFIC_WINDOW),
        "total_requests_recorded": len(_TRAFFIC_WINDOW),
        "blocked_requests_total": _BLOCKED_REQUESTS_COUNT,
        "total_blocked_requests": _BLOCKED_REQUESTS_COUNT,
        "average_latency_ms": avg_latency,
        "status_2xx": status_2xx,
        "status_3xx": status_3xx,
        "status_4xx": status_4xx,
        "status_5xx": status_5xx,
        "status_distribution": {
            "2xx": status_2xx,
            "3xx": status_3xx,
            "4xx": status_4xx,
            "5xx": status_5xx,
        },
        "top_client_ips": [{"ip": item[0], "count": item[1]} for item in top_ips],
        "is_https_enforced": is_https_enforced(),
        "cors_origins": get_cors_allowed_origins(),
        "blacklisted_ips_count": len(_BLACKLISTED_IPS),
        "admin_whitelisted_ips_count": len(_ADMIN_WHITELISTED_IPS),
    }


# ---------------------------------------------------------------------------
# 5. PRODUCTION SERVER CONFIG TEMPLATES (NGINX SSL, FIREWALL UFW, CLOUDFLARE)
# ---------------------------------------------------------------------------

def generate_nginx_ssl_config(domain: str = "englishmate.vn", app_port: int = 5000, port: Optional[int] = None) -> str:
    """Tạo cấu hình Nginx Reverse Proxy chuẩn an ninh quốc tế (SSL TLS 1.3, HSTS, Gzip, Cloudflare Real IP)."""
    target_port = port if port is not None else app_port
    return f"""# ==============================================================================
# EnglishMate Nginx Production Configuration with SSL/TLS 1.3 & Security Hardening
# Domain: {domain}
# ==============================================================================

# 1. HTTP to HTTPS 301 Permanent Redirect
server {{
    listen 80;
    listen [::]:80;
    server_name {domain} www.{domain};
    return 301 https://$host$request_uri;
}}

# 2. HTTPS Server Block
server {{
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name {domain} www.{domain};

    # SSL Certificates (Let's Encrypt / Custom SSL)
    ssl_certificate /etc/letsencrypt/live/{domain}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/{domain}/privkey.pem;
    ssl_trusted_certificate /etc/letsencrypt/live/{domain}/chain.pem;

    # Modern TLS 1.2 / TLS 1.3 Protocols & Ciphers
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;
    ssl_session_tickets off;

    # Security Headers (HSTS, Anti-clickjacking, XSS)
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Gzip Compression for Fast Assets Delivery
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml application/json application/javascript application/rss+xml image/svg+xml;

    # Cloudflare Real IP Passthrough
    set_real_ip_from 173.245.48.0/20;
    set_real_ip_from 103.21.244.0/22;
    set_real_ip_from 103.22.200.0/22;
    set_real_ip_from 103.31.4.0/22;
    set_real_ip_from 141.101.64.0/18;
    set_real_ip_from 108.162.192.0/18;
    set_real_ip_from 190.93.240.0/20;
    set_real_ip_from 188.114.96.0/20;
    set_real_ip_from 197.234.240.0/22;
    set_real_ip_from 198.41.128.0/17;
    real_ip_header CF-Connecting-IP;

    # Reverse Proxy to Flask/Gunicorn App
    location / {{
        proxy_pass http://127.0.0.1:{target_port};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 90;
    }}

    # Static Files Fast Caching
    location /static/ {{
        alias /var/www/englishmate/app/frontend/static/;
        expires 30d;
        add_header Cache-Control "public, max-age=2592000, immutable";
    }}
}}
"""


def generate_ufw_firewall_script(ssh_port: int = 22, allow_http_https: bool = True) -> str:
    """Tạo kịch bản thiết lập tường lửa máy chủ Linux (UFW Firewall) bảo vệ cổng mạng."""
    http_lines = "sudo ufw allow 80/tcp comment 'Allow HTTP Port 80'\nsudo ufw allow 443/tcp comment 'Allow HTTPS Port 443'" if allow_http_https else ""
    return f"""#!/bin/bash
# ==============================================================================
# EnglishMate Linux Server Firewall Hardening Script (UFW)
# ==============================================================================

echo "[*] Cấu hình tường lửa UFW cho máy chủ EnglishMate..."

# Reset UFW
sudo ufw --force reset

# Default Policies: Deny incoming, Allow outgoing
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH with rate limiting (Anti-brute force)
sudo ufw limit {ssh_port}/tcp comment 'Rate-limited SSH Port {ssh_port}'

# Allow Web Ports (HTTP/HTTPS)
{http_lines}

# Deny Direct Access to Internal Flask/Database Ports
sudo ufw deny 5000/tcp comment 'Block direct Flask port access'
sudo ufw deny 5432/tcp comment 'Block direct PostgreSQL access'
sudo ufw deny 6379/tcp comment 'Block direct Redis access'

# Enable UFW
sudo ufw --force enable
sudo ufw status verbose

echo "[+] Tường lửa máy chủ UFW đã được thiết lập và kích hoạt an toàn!"
"""



def get_cloudflare_ddos_recommendations() -> Dict[str, Any]:
    """Cung cấp hướng dẫn và các khuyến nghị tối ưu Cloudflare DDoS & WAF Protection."""
    return {
        "title": "Khuyến nghị cấu hình Cloudflare DDoS & WAF Protection",
        "steps": [
            {
                "name": "1. Bật Cloudflare Proxy (Orange Cloud)",
                "description": "Chuyển các bản ghi DNS (A, CNAME) sang trạng thái Proxied để che giấu IP gốc của máy chủ."
            },
            {
                "name": "2. Kích hoạt 'Under Attack Mode' khi bị DDoS",
                "description": "Tự động hiển thị JavaScript challenge (Turnstile / Managed Challenge) trước khi cho phép truy cập."
            },
            {
                "name": "3. Cấu hình Rate Limiting Rules",
                "description": "Giới hạn tối đa 60 requests/phút trên các endpoint nhạy cảm như `/auth/login`, `/auth/register`."
            },
            {
                "name": "4. Bật Web Application Firewall (WAF) OWASP",
                "description": "Kích hoạt bộ lọc WAF chặn SQL Injection, XSS và Bad Bot Crawlers."
            },
            {
                "name": "5. Bật Bot Fight Mode & SSL Full (Strict)",
                "description": "Tự động phát hiện và chặn các mạng botnet tự động tấn công hệ thống."
            }
        ]
    }
