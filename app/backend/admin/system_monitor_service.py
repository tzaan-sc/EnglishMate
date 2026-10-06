"""
System Resource Monitoring Service for EnglishMate.
Collects and streams host CPU, RAM, Disk, Network, and Process health metrics.
Maintains historical timeseries samples for real-time visualization dashboards.
"""

import time
import os
import threading
from collections import deque
from datetime import datetime
from typing import Dict, List, Any, Optional

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


class SystemMonitorService:
    def __init__(self, history_len: int = 40):
        self.lock = threading.Lock()
        self.history_len = history_len
        self.cpu_history: deque = deque(maxlen=history_len)
        self.ram_history: deque = deque(maxlen=history_len)
        self.timestamps: deque = deque(maxlen=history_len)
        self.start_time = datetime.now()
        self._last_net_io = None
        self._last_net_time = time.time()

    def get_complete_system_metrics(self) -> Dict[str, Any]:
        """Fetch complete system and process resource metrics."""
        now_str = datetime.now().strftime("%H:%M:%S")
        uptime_seconds = int((datetime.now() - self.start_time).total_seconds())

        if not HAS_PSUTIL:
            return self._get_mock_fallback_metrics(now_str, uptime_seconds)

        try:
            # 1. CPU Metrics
            cpu_percent = psutil.cpu_percent(interval=None)
            cpu_per_core = psutil.cpu_percent(interval=None, percpu=True)
            cpu_count_logical = psutil.cpu_count(logical=True) or 1
            cpu_count_physical = psutil.cpu_count(logical=False) or cpu_count_logical
            try:
                cpu_freq = psutil.cpu_freq()
                cpu_freq_current = round(cpu_freq.current, 0) if cpu_freq else 0.0
            except Exception:
                cpu_freq_current = 0.0

            # 2. Memory (RAM) Metrics
            mem = psutil.virtual_memory()
            total_ram_mb = round(mem.total / (1024 * 1024), 1)
            used_ram_mb = round(mem.used / (1024 * 1024), 1)
            free_ram_mb = round(mem.available / (1024 * 1024), 1)
            ram_percent = round(mem.percent, 1)

            # Swap Memory
            try:
                swap = psutil.swap_memory()
                swap_total_mb = round(swap.total / (1024 * 1024), 1)
                swap_used_mb = round(swap.used / (1024 * 1024), 1)
                swap_percent = round(swap.percent, 1)
            except Exception:
                swap_total_mb = 0.0
                swap_used_mb = 0.0
                swap_percent = 0.0

            # 3. Disk Storage Metrics
            disk_path = os.path.abspath(os.sep)
            try:
                disk = psutil.disk_usage(disk_path)
                disk_total_gb = round(disk.total / (1024 * 1024 * 1024), 2)
                disk_used_gb = round(disk.used / (1024 * 1024 * 1024), 2)
                disk_free_gb = round(disk.free / (1024 * 1024 * 1024), 2)
                disk_percent = round(disk.percent, 1)
            except Exception:
                disk_total_gb = 0.0
                disk_used_gb = 0.0
                disk_free_gb = 0.0
                disk_percent = 0.0

            # Disk IO
            try:
                disk_io = psutil.disk_io_counters()
                disk_read_mb = round(disk_io.read_bytes / (1024 * 1024), 1) if disk_io else 0.0
                disk_write_mb = round(disk_io.write_bytes / (1024 * 1024), 1) if disk_io else 0.0
            except Exception:
                disk_read_mb = 0.0
                disk_write_mb = 0.0

            # 4. Network Traffic Metrics
            try:
                net_io = psutil.net_io_counters()
                bytes_sent_mb = round(net_io.bytes_sent / (1024 * 1024), 2)
                bytes_recv_mb = round(net_io.bytes_recv / (1024 * 1024), 2)
                packets_sent = net_io.packets_sent
                packets_recv = net_io.packets_recv
            except Exception:
                bytes_sent_mb = 0.0
                bytes_recv_mb = 0.0
                packets_sent = 0
                packets_recv = 0

            # 5. Current App Process Metrics
            proc = psutil.Process()
            proc_mem_info = proc.memory_info()
            proc_rss_mb = round(proc_mem_info.rss / (1024 * 1024), 1)
            proc_vms_mb = round(proc_mem_info.vms / (1024 * 1024), 1)
            proc_cpu = round(proc.cpu_percent(interval=None), 1)
            proc_threads = proc.num_threads()
            try:
                proc_fds = proc.num_fds() if hasattr(proc, "num_fds") else proc.num_handles()
            except Exception:
                proc_fds = 0

            # Record into timeseries history
            with self.lock:
                self.cpu_history.append(cpu_percent)
                self.ram_history.append(ram_percent)
                self.timestamps.append(now_str)

            return {
                "available": True,
                "timestamp": now_str,
                "uptime_seconds": uptime_seconds,
                "uptime_formatted": self._format_uptime(uptime_seconds),
                "cpu": {
                    "percent": cpu_percent,
                    "per_core": cpu_per_core,
                    "cores_logical": cpu_count_logical,
                    "cores_physical": cpu_count_physical,
                    "freq_mhz": cpu_freq_current,
                },
                "ram": {
                    "total_mb": total_ram_mb,
                    "used_mb": used_ram_mb,
                    "free_mb": free_ram_mb,
                    "percent": ram_percent,
                    "swap_total_mb": swap_total_mb,
                    "swap_used_mb": swap_used_mb,
                    "swap_percent": swap_percent,
                },
                "disk": {
                    "total_gb": disk_total_gb,
                    "used_gb": disk_used_gb,
                    "free_gb": disk_free_gb,
                    "percent": disk_percent,
                    "read_mb": disk_read_mb,
                    "write_mb": disk_write_mb,
                },
                "network": {
                    "sent_mb": bytes_sent_mb,
                    "recv_mb": bytes_recv_mb,
                    "packets_sent": packets_sent,
                    "packets_recv": packets_recv,
                },
                "process": {
                    "pid": os.getpid(),
                    "rss_mb": proc_rss_mb,
                    "vms_mb": proc_vms_mb,
                    "cpu_percent": proc_cpu,
                    "threads": proc_threads,
                    "file_descriptors": proc_fds,
                },
                "history": {
                    "labels": list(self.timestamps),
                    "cpu": list(self.cpu_history),
                    "ram": list(self.ram_history),
                }
            }

        except Exception as e:
            return self._get_mock_fallback_metrics(now_str, uptime_seconds, error=str(e))

    def _get_mock_fallback_metrics(self, now_str: str, uptime_seconds: int, error: Optional[str] = None) -> Dict[str, Any]:
        """Fallback metrics when psutil is unavailable or errors out."""
        with self.lock:
            self.cpu_history.append(5.0)
            self.ram_history.append(25.0)
            self.timestamps.append(now_str)

        return {
            "available": False,
            "error": error or "psutil module not available",
            "timestamp": now_str,
            "uptime_seconds": uptime_seconds,
            "uptime_formatted": self._format_uptime(uptime_seconds),
            "cpu": {
                "percent": 0.0,
                "per_core": [0.0],
                "cores_logical": 1,
                "cores_physical": 1,
                "freq_mhz": 0.0,
            },
            "ram": {
                "total_mb": 4096.0,
                "used_mb": 1024.0,
                "free_mb": 3072.0,
                "percent": 25.0,
                "swap_total_mb": 0.0,
                "swap_used_mb": 0.0,
                "swap_percent": 0.0,
            },
            "disk": {
                "total_gb": 100.0,
                "used_gb": 20.0,
                "free_gb": 80.0,
                "percent": 20.0,
                "read_mb": 0.0,
                "write_mb": 0.0,
            },
            "network": {
                "sent_mb": 0.0,
                "recv_mb": 0.0,
                "packets_sent": 0,
                "packets_recv": 0,
            },
            "process": {
                "pid": os.getpid(),
                "rss_mb": 120.0,
                "vms_mb": 250.0,
                "cpu_percent": 0.0,
                "threads": threading.active_count(),
                "file_descriptors": 0,
            },
            "history": {
                "labels": list(self.timestamps),
                "cpu": list(self.cpu_history),
                "ram": list(self.ram_history),
            }
        }

    @staticmethod
    def _format_uptime(seconds: int) -> str:
        d = seconds // 86400
        h = (seconds % 86400) // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        parts = []
        if d > 0:
            parts.append(f"{d}d")
        if h > 0 or d > 0:
            parts.append(f"{h}h")
        if m > 0 or h > 0 or d > 0:
            parts.append(f"{m}m")
        parts.append(f"{s}s")
        return " ".join(parts)


# Global singleton instance
system_monitor = SystemMonitorService()
