import json
from tests.conftest import login
from app.backend.admin.models import SystemConfig
from app.backend.admin.network_security import (
    get_client_ip,
    is_ip_blacklisted,
    is_admin_ip_allowed,
    add_ip_blacklist,
    remove_ip_blacklist,
    add_admin_ip_whitelist,
    remove_admin_ip_whitelist,
    is_https_enforced,
    get_cors_allowed_origins,
    apply_cors_headers,
    record_network_traffic,
    record_blocked_request,
    get_network_monitoring_stats,
    generate_nginx_ssl_config,
    generate_ufw_firewall_script,
    get_cloudflare_ddos_recommendations,
)


def test_ip_blacklisting_blocks_requests(client, app):
    """Kiểm tra IP bị cấm (Blacklist) sẽ bị chặn ngay với HTTP 403."""
    with app.app_context():
        add_ip_blacklist("198.51.100.44", reason="Brute force attack test")

    # Gửi request với IP bị cấm qua header X-Forwarded-For
    res = client.get("/", headers={"X-Forwarded-For": "198.51.100.44"})
    assert res.status_code == 403
    assert b"403" in res.data

    # Thử gỡ IP khỏi danh sách cấm
    with app.app_context():
        remove_ip_blacklist("198.51.100.44")

    res2 = client.get("/", headers={"X-Forwarded-For": "198.51.100.44"})
    assert res2.status_code == 200


def test_admin_ip_whitelisting(client, app):
    """Kiểm tra Admin IP Whitelist: chỉ cho phép IP trong danh sách truy cập /admin."""
    with app.app_context():
        SystemConfig.set_config("ADMIN_IP_WHITELIST_ENABLED", "true", category="NETWORK")
        add_admin_ip_whitelist("203.0.113.10", note="Office VPN")

    # User từ IP lạ cố gắng truy cập admin portal
    res_stranger = client.get("/admin", headers={"X-Forwarded-For": "198.51.100.99"})
    assert res_stranger.status_code == 403

    # Gửi từ IP đã được whitelist
    login(client, "admin@test.com", "admin123")
    res_allowed = client.get("/admin/", headers={"X-Forwarded-For": "203.0.113.10"})
    assert res_allowed.status_code in (200, 302)

    # Dọn dẹp whitelist
    with app.app_context():
        remove_admin_ip_whitelist("203.0.113.10")
        SystemConfig.set_config("ADMIN_IP_WHITELIST_ENABLED", "false", category="NETWORK")


def test_cors_headers_applied(client, app):
    """Kiểm tra CORS headers được gắn đúng cho domain được phép."""
    # 1. Default wildcard CORS
    res_opt = client.open("/", method="OPTIONS", headers={
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "POST"
    })
    assert res_opt.status_code == 204
    assert res_opt.headers.get("Access-Control-Allow-Origin") == "*"
    assert "GET, POST" in res_opt.headers.get("Access-Control-Allow-Methods", "")

    # 2. Specific domain CORS configuration
    with app.app_context():
        SystemConfig.set_config("CORS_ALLOWED_ORIGINS", "http://localhost:3000, https://englishmate.vn", category="NETWORK")

    res_custom = client.get("/", headers={"Origin": "http://localhost:3000"})
    assert res_custom.headers.get("Access-Control-Allow-Origin") == "http://localhost:3000"

    # Reset
    with app.app_context():
        SystemConfig.set_config("CORS_ALLOWED_ORIGINS", "*", category="NETWORK")


def test_https_enforcement_redirect(client, app):
    """Kiểm tra HTTP sang HTTPS 301 Permanent Redirect khi bật HTTPS Enforcement."""
    with app.app_context():
        SystemConfig.set_config("HTTPS_ENFORCEMENT_ENABLED", "true", category="NETWORK")

    # Giả lập non-local client gửi request qua HTTP
    res = client.get(
        "/auth/login",
        headers={
            "X-Forwarded-Proto": "http",
            "X-Forwarded-For": "198.51.100.77",
            "Host": "englishmate.local",
        }
    )
    assert res.status_code == 301
    assert res.headers.get("Location", "").startswith("https://englishmate.local/auth/login")

    # Tắt HTTPS Enforcement
    with app.app_context():
        SystemConfig.set_config("HTTPS_ENFORCEMENT_ENABLED", "false", category="NETWORK")


def test_network_monitoring_telemetry(client, app):
    """Kiểm tra bộ ghi nhận lưu lượng mạng theo thời gian thực (sliding window)."""
    with app.app_context():
        record_network_traffic("/api/test-1", "1.2.3.4", "GET", 200, 15.5)
        record_network_traffic("/api/test-2", "1.2.3.5", "POST", 500, 42.0)
        record_blocked_request()

        stats = get_network_monitoring_stats()
        assert stats["total_requests_recorded"] >= 2
        assert stats["total_blocked_requests"] >= 1
        assert "active_ips_1m" in stats
        assert "status_2xx" in stats
        assert "status_5xx" in stats
        assert stats["status_5xx"] >= 1


def test_nginx_ssl_and_ufw_scripts_generation(app):
    """Kiểm tra việc tạo kịch bản cấu hình Nginx SSL TLS 1.3 và Firewall UFW."""
    with app.app_context():
        nginx_conf = generate_nginx_ssl_config(domain="englishmate.edu.vn", port=5000)
        assert "server_name englishmate.edu.vn" in nginx_conf
        assert "TLSv1.2 TLSv1.3;" in nginx_conf
        assert "proxy_pass http://127.0.0.1:5000;" in nginx_conf

        ufw_script = generate_ufw_firewall_script(ssh_port=22, allow_http_https=True)
        assert "ufw default deny incoming" in ufw_script
        assert "ufw limit 22/tcp" in ufw_script
        assert "ufw allow 80/tcp" in ufw_script
        assert "ufw allow 443/tcp" in ufw_script


        ddos_guide = get_cloudflare_ddos_recommendations()
        assert "Cloudflare" in ddos_guide["title"]
        assert any("Cloudflare Proxy" in s["name"] for s in ddos_guide["steps"])
        assert len(ddos_guide["steps"]) >= 4


def test_admin_network_security_management_endpoints(client, app):
    """Kiểm tra các endpoint REST quản lý Network Security trên giao diện Admin."""
    login(client, "admin@test.com", "admin123")

    # 1. GET Dashboard Page
    res_page = client.get("/admin/system/network-security")
    assert res_page.status_code == 200
    assert b"Network Security" in res_page.data or "T\xc6\xb0\xe1\xbb\x9dng l\xe1\xbb\xada".encode("utf-8") in res_page.data

    # 2. GET Real-time Stats JSON
    res_stats = client.get("/admin/system/network-security/stats")
    assert res_stats.status_code == 200
    data = res_stats.get_json()
    assert data["success"] is True
    assert "stats" in data

    # 3. POST Add to Blacklist
    res_bl = client.post("/admin/system/network-security/ip-rules", json={
        "list_type": "blacklist",
        "action": "add",
        "ip": "203.0.113.88",
        "reason": "Test attack rule"
    })
    assert res_bl.status_code == 200
    assert res_bl.get_json()["success"] is True

    # 4. POST Remove from Blacklist
    res_rm = client.post("/admin/system/network-security/ip-rules", json={
        "list_type": "blacklist",
        "action": "remove",
        "ip": "203.0.113.88"
    })
    assert res_rm.status_code == 200

    # 5. POST Update Settings (HTTPS & CORS)
    res_settings = client.post("/admin/system/network-security/settings", json={
        "https_enforcement": True,
        "cors_origins": "https://englishmate.vn, https://app.englishmate.vn"
    })
    assert res_settings.status_code == 200
    assert res_settings.get_json()["success"] is True

    # 6. GET Deployment Scripts
    res_scripts = client.get("/admin/system/network-security/deployment-scripts?domain=mytest.edu.vn&port=8000")
    assert res_scripts.status_code == 200
    scripts_data = res_scripts.get_json()
    assert scripts_data["success"] is True
    assert "mytest.edu.vn" in scripts_data["nginx_ssl_config"]
    assert "ufw" in scripts_data["ufw_firewall_script"]
    assert "enable" in scripts_data["ufw_firewall_script"]


