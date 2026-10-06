"""
Real-time Alert Notification Service for EnglishMate.
Dispatches critical error (HTTP 500) and system alerts to Telegram, Discord, and Slack webhooks.
Includes rate limiting cooldown, asynchronous dispatching, and test trigger functionality.
"""

import os
import json
import time
import urllib.request
import urllib.error
import threading
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

logger = logging.getLogger("englishmate.alerts")

# In-memory cooldown tracking: {fingerprint: last_alert_timestamp}
_ALERT_COOLDOWN_MAP: Dict[str, float] = {}
_COOLDOWN_LOCK = threading.Lock()


class AlertService:
    @staticmethod
    def get_alert_config() -> Dict[str, Any]:
        """Fetch alert configuration from SystemSetting or environment variables."""
        from .models import SystemSetting

        enabled = SystemSetting.get_bool_setting("ALERT_NOTIFICATIONS_ENABLED", default=False)
        channels = SystemSetting.get_setting("ALERT_CHANNELS", default="all")  # telegram, discord, slack, all
        min_severity = SystemSetting.get_setting("ALERT_MIN_SEVERITY", default="CRITICAL")  # CRITICAL, ERROR, WARNING
        cooldown_sec = SystemSetting.get_int_setting("ALERT_COOLDOWN_SECONDS", default=60)

        telegram_token = SystemSetting.get_setting("TELEGRAM_BOT_TOKEN", default=os.getenv("TELEGRAM_BOT_TOKEN", ""))
        telegram_chat_id = SystemSetting.get_setting("TELEGRAM_CHAT_ID", default=os.getenv("TELEGRAM_CHAT_ID", ""))
        discord_webhook = SystemSetting.get_setting("DISCORD_WEBHOOK_URL", default=os.getenv("DISCORD_WEBHOOK_URL", ""))
        slack_webhook = SystemSetting.get_setting("SLACK_WEBHOOK_URL", default=os.getenv("SLACK_WEBHOOK_URL", ""))

        return {
            "enabled": enabled,
            "channels": channels,
            "min_severity": min_severity,
            "cooldown_seconds": cooldown_sec,
            "telegram": {
                "bot_token": telegram_token,
                "chat_id": telegram_chat_id,
                "configured": bool(telegram_token and telegram_chat_id),
            },
            "discord": {
                "webhook_url": discord_webhook,
                "configured": bool(discord_webhook),
            },
            "slack": {
                "webhook_url": slack_webhook,
                "configured": bool(slack_webhook),
            },
        }

    @staticmethod
    def save_alert_config(config_data: Dict[str, Any]) -> None:
        """Save alert settings into SystemSetting."""
        from .models import SystemSetting

        if "enabled" in config_data:
            SystemSetting.set_setting(
                "ALERT_NOTIFICATIONS_ENABLED",
                "true" if config_data["enabled"] else "false",
                "Bật/Tắt hệ thống cảnh báo sự cố tự động qua bot/webhook"
            )
        if "channels" in config_data:
            SystemSetting.set_setting(
                "ALERT_CHANNELS",
                str(config_data["channels"]),
                "Kênh nhận cảnh báo (telegram, discord, slack, all)"
            )
        if "min_severity" in config_data:
            SystemSetting.set_setting(
                "ALERT_MIN_SEVERITY",
                str(config_data["min_severity"]),
                "Mức độ lỗi tối thiểu để gửi cảnh báo (CRITICAL, ERROR, WARNING)"
            )
        if "cooldown_seconds" in config_data:
            SystemSetting.set_setting(
                "ALERT_COOLDOWN_SECONDS",
                str(config_data["cooldown_seconds"]),
                "Thời gian chờ chống spam cảnh báo giữa các lỗi cùng loại (giây)"
            )
        if "telegram_bot_token" in config_data:
            SystemSetting.set_setting("TELEGRAM_BOT_TOKEN", str(config_data["telegram_bot_token"]).strip(), "Telegram Bot Token")
        if "telegram_chat_id" in config_data:
            SystemSetting.set_setting("TELEGRAM_CHAT_ID", str(config_data["telegram_chat_id"]).strip(), "Telegram Chat ID")
        if "discord_webhook_url" in config_data:
            SystemSetting.set_setting("DISCORD_WEBHOOK_URL", str(config_data["discord_webhook_url"]).strip(), "Discord Webhook URL")
        if "slack_webhook_url" in config_data:
            SystemSetting.set_setting("SLACK_WEBHOOK_URL", str(config_data["slack_webhook_url"]).strip(), "Slack Webhook URL")

    @classmethod
    def dispatch_error_alert_async(cls, error_data: Dict[str, Any]) -> None:
        """Dispatch alert notification in background thread so request lifecycle is not delayed."""
        thread = threading.Thread(target=cls._dispatch_error_alert_sync, args=(error_data,), daemon=True)
        thread.start()

    @classmethod
    def _dispatch_error_alert_sync(cls, error_data: Dict[str, Any]) -> None:
        """Synchronously check cooldown and deliver alert to configured channels."""
        config = cls.get_alert_config()
        if not config["enabled"]:
            return

        fingerprint = error_data.get("fingerprint") or "generic_alert"
        now_ts = time.time()
        cooldown = config["cooldown_seconds"]

        with _COOLDOWN_LOCK:
            last_sent = _ALERT_COOLDOWN_MAP.get(fingerprint, 0.0)
            if now_ts - last_sent < cooldown:
                logger.info(f"[Alert] Skipped alert for fingerprint {fingerprint} (Cooldown active: {cooldown}s)")
                return
            _ALERT_COOLDOWN_MAP[fingerprint] = now_ts

        target_channels = config["channels"].lower()

        # Telegram
        if (target_channels in ("all", "telegram")) and config["telegram"]["configured"]:
            cls._send_telegram_alert(config["telegram"]["bot_token"], config["telegram"]["chat_id"], error_data)

        # Discord
        if (target_channels in ("all", "discord")) and config["discord"]["configured"]:
            cls._send_discord_alert(config["discord"]["webhook_url"], error_data)

        # Slack
        if (target_channels in ("all", "slack")) and config["slack"]["configured"]:
            cls._send_slack_alert(config["slack"]["webhook_url"], error_data)

    @classmethod
    def send_test_alert(cls, channel: str = "all", custom_message: Optional[str] = None) -> Dict[str, Any]:
        """Send a test alert message to verify channel integrations."""
        config = cls.get_alert_config()
        test_payload = {
            "title": "🧪 [TEST ALERT] EnglishMate System Notification",
            "exception_type": "TestAlertVerification",
            "message": custom_message or "Đây là thông báo kiểm tra kết nối bot cảnh báo tự động từ EnglishMate Admin.",
            "status_code": 200,
            "severity": "INFO",
            "route": "/admin/system/monitoring",
            "method": "POST",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "client_ip": "127.0.0.1",
            "user_id": 1,
            "is_test": True,
        }

        results = {}
        ch_lower = channel.lower()

        if ch_lower in ("all", "telegram"):
            if config["telegram"]["configured"]:
                ok, msg = cls._send_telegram_alert(config["telegram"]["bot_token"], config["telegram"]["chat_id"], test_payload)
                results["telegram"] = {"success": ok, "message": msg}
            else:
                results["telegram"] = {"success": False, "message": "Chưa cấu hình Telegram Bot Token hoặc Chat ID."}

        if ch_lower in ("all", "discord"):
            if config["discord"]["configured"]:
                ok, msg = cls._send_discord_alert(config["discord"]["webhook_url"], test_payload)
                results["discord"] = {"success": ok, "message": msg}
            else:
                results["discord"] = {"success": False, "message": "Chưa cấu hình Discord Webhook URL."}

        if ch_lower in ("all", "slack"):
            if config["slack"]["configured"]:
                ok, msg = cls._send_slack_alert(config["slack"]["webhook_url"], test_payload)
                results["slack"] = {"success": ok, "message": msg}
            else:
                results["slack"] = {"success": False, "message": "Chưa cấu hình Slack Webhook URL."}

        return {
            "success": any(r.get("success") for r in results.values()) if results else False,
            "results": results
        }

    # =========================================================================
    # CHANNEL ADAPTERS
    # =========================================================================
    @staticmethod
    def _send_telegram_alert(token: str, chat_id: str, data: Dict[str, Any]) -> tuple[bool, str]:
        """Send formatted HTML message to Telegram Bot API."""
        try:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            sev = data.get("severity", "CRITICAL")
            icon = "🚨" if sev == "CRITICAL" else ("⚠️" if sev == "ERROR" else "ℹ️")

            text = (
                f"{icon} <b>EnglishMate Alert: {sev}</b>\n\n"
                f"<b>Type:</b> <code>{data.get('exception_type', 'Error')}</code>\n"
                f"<b>Status:</b> <code>{data.get('status_code', 500)}</code>\n"
                f"<b>Route:</b> <code>{data.get('method', 'GET')} {data.get('route', '/')}</code>\n"
                f"<b>Time:</b> {data.get('timestamp', '')}\n"
                f"<b>IP:</b> <code>{data.get('client_ip', '127.0.0.1')}</code>\n"
                f"<b>Message:</b>\n<pre>{data.get('message', '')[:400]}</pre>"
            )

            payload = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            }

            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=8) as response:
                if response.status == 200:
                    return True, "Gửi Telegram thành công"
                return False, f"Telegram status: {response.status}"
        except Exception as e:
            logger.warning(f"Failed to send Telegram alert: {e}")
            return False, str(e)

    @staticmethod
    def _send_discord_alert(webhook_url: str, data: Dict[str, Any]) -> tuple[bool, str]:
        """Send embed payload to Discord Webhook."""
        try:
            sev = data.get("severity", "CRITICAL")
            color = 15548997 if sev == "CRITICAL" else (16776960 if sev == "ERROR" else 3447003)

            embed = {
                "title": f"🚨 [EnglishMate] {sev} Alert: {data.get('exception_type', 'Error')}",
                "description": data.get("message", "")[:500],
                "color": color,
                "fields": [
                    {"name": "Status", "value": f"`{data.get('status_code', 500)}`", "inline": True},
                    {"name": "Route", "value": f"`{data.get('method', 'GET')} {data.get('route', '/')}`", "inline": True},
                    {"name": "IP", "value": f"`{data.get('client_ip', '127.0.0.1')}`", "inline": True},
                    {"name": "Timestamp", "value": data.get("timestamp", ""), "inline": False},
                ],
                "footer": {"text": "EnglishMate Real-Time Monitoring"},
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

            payload = {
                "username": "EnglishMate Alert Bot",
                "embeds": [embed]
            }

            req = urllib.request.Request(
                webhook_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json", "User-Agent": "EnglishMateAlerts/1.0"}
            )
            with urllib.request.urlopen(req, timeout=8) as response:
                if response.status in (200, 204):
                    return True, "Gửi Discord thành công"
                return False, f"Discord status: {response.status}"
        except Exception as e:
            logger.warning(f"Failed to send Discord alert: {e}")
            return False, str(e)

    @staticmethod
    def _send_slack_alert(webhook_url: str, data: Dict[str, Any]) -> tuple[bool, str]:
        """Send rich payload to Slack Incoming Webhook."""
        try:
            sev = data.get("severity", "CRITICAL")
            icon = ":rotating_light:" if sev == "CRITICAL" else ":warning:"

            payload = {
                "text": f"{icon} *[EnglishMate Alert]* {sev}: {data.get('exception_type', 'Error')}",
                "attachments": [
                    {
                        "color": "danger" if sev == "CRITICAL" else "warning",
                        "fields": [
                            {"title": "Status Code", "value": str(data.get("status_code", 500)), "short": True},
                            {"title": "Route", "value": f"{data.get('method', 'GET')} {data.get('route', '/')}", "short": True},
                            {"title": "Time", "value": data.get("timestamp", ""), "short": True},
                            {"title": "IP", "value": data.get("client_ip", "127.0.0.1"), "short": True},
                            {"title": "Details", "value": data.get("message", "")[:400], "short": False},
                        ]
                    }
                ]
            }

            req = urllib.request.Request(
                webhook_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=8) as response:
                if response.status == 200:
                    return True, "Gửi Slack thành công"
                return False, f"Slack status: {response.status}"
        except Exception as e:
            logger.warning(f"Failed to send Slack alert: {e}")
            return False, str(e)


# Singleton alias
alert_service = AlertService()
