import re
from typing import Any, Dict, Optional, Set, Union


def mask_email(email: Optional[str]) -> str:
    """
    Che giấu địa chỉ email (ví dụ: user@example.com -> u***r@example.com, john.doe@domain.com -> j***e@domain.com).
    Bảo toàn định dạng tên miền để người dùng nhận biết được nhà cung cấp email.
    """
    if not email or not isinstance(email, str):
        return ""

    email = email.strip()
    if "@" not in email:
        return mask_text(email, visible_start=1, visible_end=1)

    parts = email.split("@", 1)
    username, domain = parts[0], parts[1]

    if len(username) == 0:
        return f"***@{domain}"
    elif len(username) == 1:
        masked_user = f"{username}***"
    elif len(username) == 2:
        masked_user = f"{username[0]}***{username[1]}"
    else:
        masked_user = f"{username[0]}***{username[-1]}"

    return f"{masked_user}@{domain}"


def mask_ip_address(ip_str: Optional[str], mask_level: str = "medium") -> str:
    """
    Che giấu địa chỉ IPv4 hoặc IPv6 nhằm bảo vệ quyền riêng tư người dùng.
    - IPv4: 192.168.1.100 -> 192.168.***.*** (medium) hoặc 192.168.1.*** (low)
    - IPv6: 2001:db8:85a3::8a2e:370:7334 -> 2001:db8:****:****
    """
    if not ip_str or not isinstance(ip_str, str):
        return ""

    ip_clean = ip_str.strip()

    # IPv4 detection
    ipv4_pattern = r"^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$"
    match_v4 = re.match(ipv4_pattern, ip_clean)
    if match_v4:
        o1, o2, o3, o4 = match_v4.groups()
        if mask_level == "low":
            return f"{o1}.{o2}.{o3}.***"
        elif mask_level == "high":
            return f"{o1}.***.***.***"
        else:  # medium
            return f"{o1}.{o2}.***.***"

    # IPv6 detection
    if ":" in ip_clean:
        parts = ip_clean.split(":")
        if len(parts) >= 2:
            return f"{parts[0]}:{parts[1]}:" + ":".join(["****"] * min(4, max(1, len(parts) - 2)))

    return mask_text(ip_clean, visible_start=2, visible_end=2)


def mask_phone(phone_str: Optional[str]) -> str:
    """
    Che giấu số điện thoại (ví dụ: 0912345678 -> 0912***678 hoặc 09****5678).
    """
    if not phone_str or not isinstance(phone_str, str):
        return ""

    cleaned = re.sub(r"\s+", "", phone_str.strip())
    if len(cleaned) <= 4:
        return "****"

    if len(cleaned) >= 10:
        return f"{cleaned[:4]}***{cleaned[-3:]}"
    return f"{cleaned[:2]}***{cleaned[-2:]}"


def mask_text(text: Optional[str], visible_start: int = 2, visible_end: int = 2, mask_char: str = "*") -> str:
    """Che giấu chuỗi văn bản thông thường theo độ dài hiển thị đầu và cuối."""
    if not text or not isinstance(text, str):
        return ""

    s = text.strip()
    length = len(s)
    if length <= (visible_start + visible_end):
        return mask_char * min(length, 4)

    start_part = s[:visible_start]
    end_part = s[-visible_end:] if visible_end > 0 else ""
    return f"{start_part}{mask_char * 3}{end_part}"


DEFAULT_SENSITIVE_KEYS = {
    "password",
    "password_hash",
    "token",
    "access_token",
    "refresh_token",
    "secret",
    "api_key",
    "auth_token",
    "credit_card",
    "otp",
}


def mask_sensitive_dict(
    data: Union[Dict[str, Any], list, Any],
    sensitive_keys: Optional[Set[str]] = None,
    mask_emails: bool = True,
    mask_ips: bool = True
) -> Any:
    """
    Duyệt đệ quy và che giấu các trường nhạy cảm trong Dictionary/JSON payload.
    """
    keys_to_mask = sensitive_keys if sensitive_keys is not None else DEFAULT_SENSITIVE_KEYS

    if isinstance(data, dict):
        masked_dict = {}
        for k, v in data.items():
            k_lower = str(k).lower()
            if any(s_key in k_lower for s_key in keys_to_mask):
                masked_dict[k] = "******"
            elif mask_emails and ("email" in k_lower or (isinstance(v, str) and "@" in v and "." in v)):
                masked_dict[k] = mask_email(v) if isinstance(v, str) else v
            elif mask_ips and ("ip" in k_lower or "ip_address" in k_lower):
                masked_dict[k] = mask_ip_address(v) if isinstance(v, str) else v
            elif isinstance(v, (dict, list)):
                masked_dict[k] = mask_sensitive_dict(v, keys_to_mask, mask_emails, mask_ips)
            else:
                masked_dict[k] = v
        return masked_dict
    elif isinstance(data, list):
        return [mask_sensitive_dict(item, keys_to_mask, mask_emails, mask_ips) for item in data]
    return data


def is_data_masking_enabled() -> bool:
    """Kiểm tra xem chế độ Data Masking có đang được bật trong hệ thống hay không."""
    try:
        from .models import SystemConfig
        return SystemConfig.is_feature_enabled("DATA_MASKING_ENABLED", default=True)
    except Exception:
        return True
