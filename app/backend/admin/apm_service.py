"""
Application Performance Monitoring (APM) Service for EnglishMate.
Provides real-time route latency tracking, throughput calculation, p95/p99 percentiles,
slowest endpoints detection, status code distribution, and system resource metrics.
"""

import time
import threading
from collections import deque, defaultdict
from datetime import datetime
from typing import Dict, List, Any, Optional

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


class APMMonitor:
    def __init__(self, max_history: int = 2000, slow_threshold_ms: float = 500.0):
        self.lock = threading.Lock()
        self.max_history = max_history
        self.slow_threshold_ms = slow_threshold_ms
        self.start_time = datetime.now()
        
        # Aggregated stats per endpoint (name: endpoint)
        # Structure: {endpoint: {'count': int, 'total_ms': float, 'min_ms': float, 'max_ms': float, 'errors': int, 'samples': deque}}
        self.endpoint_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "count": 0,
            "total_ms": 0.0,
            "min_ms": float("inf"),
            "max_ms": 0.0,
            "errors": 0,
            "samples": deque(maxlen=200),
            "methods": set(),
            "paths": set(),
        })
        
        # Status code counters
        self.status_codes: Dict[str, int] = {
            "2xx": 0,
            "3xx": 0,
            "4xx": 0,
            "5xx": 0,
        }
        
        # Recent requests log
        self.recent_requests: deque = deque(maxlen=max_history)
        
        # Recent slow requests log (> slow_threshold_ms)
        self.slow_requests: deque = deque(maxlen=200)
        
        # Total counts
        self.total_requests = 0
        self.total_errors = 0
        self.all_latencies: deque = deque(maxlen=max_history)
        
        # Minute throughput tracking: {minute_timestamp: count}
        self.minute_buckets: Dict[int, int] = defaultdict(int)

    def record_request(
        self,
        endpoint: Optional[str],
        path: str,
        method: str,
        status_code: int,
        duration_ms: float,
        client_ip: str = "127.0.0.1"
    ) -> None:
        """Record an incoming HTTP request metrics."""
        # Ignore static asset noise in core APM charts if requested, or keep it lightweight
        ep = endpoint or path or "unknown"
        now = datetime.now()
        timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S")
        minute_key = int(time.time() // 60)
        is_error = status_code >= 400
        is_slow = duration_ms >= self.slow_threshold_ms

        req_record = {
            "timestamp": timestamp_str,
            "endpoint": ep,
            "path": path,
            "method": method,
            "status_code": status_code,
            "duration_ms": round(duration_ms, 2),
            "client_ip": client_ip,
            "is_slow": is_slow,
            "is_error": is_error,
        }

        with self.lock:
            self.total_requests += 1
            if is_error:
                self.total_errors += 1
            
            # Status code grouping
            if 200 <= status_code < 300:
                self.status_codes["2xx"] += 1
            elif 300 <= status_code < 400:
                self.status_codes["3xx"] += 1
            elif 400 <= status_code < 500:
                self.status_codes["4xx"] += 1
            elif status_code >= 500:
                self.status_codes["5xx"] += 1

            self.all_latencies.append(duration_ms)
            self.minute_buckets[minute_key] += 1
            
            # Keep minute buckets clean (last 60 mins)
            cutoff_minute = minute_key - 60
            for k in list(self.minute_buckets.keys()):
                if k < cutoff_minute:
                    del self.minute_buckets[k]

            # Endpoint stats
            stats = self.endpoint_stats[ep]
            stats["count"] += 1
            stats["total_ms"] += duration_ms
            stats["min_ms"] = min(stats["min_ms"], duration_ms)
            stats["max_ms"] = max(stats["max_ms"], duration_ms)
            if is_error:
                stats["errors"] += 1
            stats["samples"].append(duration_ms)
            stats["methods"].add(method)
            if len(stats["paths"]) < 5:
                stats["paths"].add(path)

            self.recent_requests.append(req_record)
            if is_slow:
                self.slow_requests.append(req_record)

    def _calc_percentiles(self, samples: List[float]) -> Dict[str, float]:
        if not samples:
            return {"p50": 0.0, "p90": 0.0, "p95": 0.0, "p99": 0.0}
        s = sorted(samples)
        n = len(s)
        def get_p(p):
            idx = int(n * p)
            return round(s[min(idx, n - 1)], 2)
        return {
            "p50": get_p(0.50),
            "p90": get_p(0.90),
            "p95": get_p(0.95),
            "p99": get_p(0.99),
        }

    def get_summary(self) -> Dict[str, Any]:
        """Return high-level summary metrics of system performance."""
        with self.lock:
            total_reqs = self.total_requests
            lat_list = list(self.all_latencies)
            avg_latency = round(sum(lat_list) / len(lat_list), 2) if lat_list else 0.0
            percentiles = self._calc_percentiles(lat_list)
            
            # Requests per minute (RPM) over last 5 minutes
            current_min = int(time.time() // 60)
            last_5_mins_count = sum(self.minute_buckets.get(current_min - i, 0) for i in range(5))
            current_rpm = round(last_5_mins_count / 5.0, 1) if last_5_mins_count > 0 else (total_reqs if total_reqs < 5 else 0.0)

            # Error rate
            error_rate = round((self.total_errors / total_reqs * 100), 2) if total_reqs > 0 else 0.0
            uptime_seconds = int((datetime.now() - self.start_time).total_seconds())

            # System resource metrics
            sys_metrics = self.get_system_metrics()

            return {
                "uptime_seconds": uptime_seconds,
                "uptime_formatted": self._format_uptime(uptime_seconds),
                "total_requests": total_reqs,
                "total_errors": self.total_errors,
                "error_rate_pct": error_rate,
                "avg_latency_ms": avg_latency,
                "min_latency_ms": round(min(lat_list), 2) if lat_list else 0.0,
                "max_latency_ms": round(max(lat_list), 2) if lat_list else 0.0,
                "p50_latency_ms": percentiles["p50"],
                "p90_latency_ms": percentiles["p90"],
                "p95_latency_ms": percentiles["p95"],
                "p99_latency_ms": percentiles["p99"],
                "current_rpm": current_rpm,
                "status_codes": dict(self.status_codes),
                "slow_requests_count": len(self.slow_requests),
                "tracked_endpoints_count": len(self.endpoint_stats),
                "system": sys_metrics,
            }

    def get_slowest_endpoints(self, limit: int = 15) -> List[Dict[str, Any]]:
        """Return the slowest endpoints ranked by average response time."""
        with self.lock:
            results = []
            for ep, stats in self.endpoint_stats.items():
                cnt = stats["count"]
                if cnt == 0:
                    continue
                avg_ms = round(stats["total_ms"] / cnt, 2)
                p_stats = self._calc_percentiles(list(stats["samples"]))
                min_ms = round(stats["min_ms"], 2) if stats["min_ms"] != float("inf") else 0.0
                max_ms = round(stats["max_ms"], 2)
                err_rate = round((stats["errors"] / cnt) * 100, 1)

                results.append({
                    "endpoint": ep,
                    "methods": list(stats["methods"]),
                    "sample_path": list(stats["paths"])[0] if stats["paths"] else ep,
                    "count": cnt,
                    "avg_ms": avg_ms,
                    "min_ms": min_ms,
                    "max_ms": max_ms,
                    "p95_ms": p_stats["p95"],
                    "p99_ms": p_stats["p99"],
                    "errors": stats["errors"],
                    "error_rate_pct": err_rate,
                })

            # Sort by average latency descending
            results.sort(key=lambda x: x["avg_ms"], reverse=True)
            return results[:limit]

    def get_recent_requests(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Return latest recorded requests."""
        with self.lock:
            items = list(self.recent_requests)
            return items[-limit:][::-1]

    def get_recent_slow_requests(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Return latest recorded slow requests."""
        with self.lock:
            items = list(self.slow_requests)
            return items[-limit:][::-1]

    def reset_metrics(self) -> None:
        """Reset APM metrics to fresh state."""
        with self.lock:
            self.endpoint_stats.clear()
            self.status_codes = {"2xx": 0, "3xx": 0, "4xx": 0, "5xx": 0}
            self.recent_requests.clear()
            self.slow_requests.clear()
            self.all_latencies.clear()
            self.minute_buckets.clear()
            self.total_requests = 0
            self.total_errors = 0
            self.start_time = datetime.now()

    def get_system_metrics(self) -> Dict[str, Any]:
        """Fetch host CPU, Memory, and Process metrics."""
        if not HAS_PSUTIL:
            return {
                "cpu_percent": 0.0,
                "memory_used_mb": 0.0,
                "memory_total_mb": 0.0,
                "memory_percent": 0.0,
                "thread_count": threading.active_count(),
                "available": False,
            }
        try:
            mem = psutil.virtual_memory()
            cpu = psutil.cpu_percent(interval=None)
            proc = psutil.Process()
            proc_mem = proc.memory_info().rss / (1024 * 1024)
            return {
                "cpu_percent": round(cpu, 1),
                "memory_used_mb": round(proc_mem, 1),
                "memory_total_mb": round(mem.total / (1024 * 1024), 1),
                "memory_percent": round(mem.percent, 1),
                "system_memory_used_mb": round(mem.used / (1024 * 1024), 1),
                "thread_count": threading.active_count(),
                "available": True,
            }
        except Exception:
            return {
                "cpu_percent": 0.0,
                "memory_used_mb": 0.0,
                "memory_total_mb": 0.0,
                "memory_percent": 0.0,
                "thread_count": threading.active_count(),
                "available": False,
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


# Global APM Monitor Instance
apm_monitor = APMMonitor(max_history=3000, slow_threshold_ms=500.0)


def init_apm(app):
    """Initialize APM tracking hooks on the Flask application."""
    @app.before_request
    def _apm_before_request():
        import time
        from flask import g
        g._apm_start_time = time.perf_counter()

    @app.after_request
    def _apm_after_request(response):
        import time
        from flask import request, g
        try:
            start_t = getattr(g, "_apm_start_time", None)
            if start_t is not None:
                duration_ms = (time.perf_counter() - start_t) * 1000.0
                endpoint = request.endpoint or "unknown"
                path = request.path
                method = request.method
                status_code = response.status_code
                client_ip = request.headers.get("X-Forwarded-For", request.remote_addr or "127.0.0.1").split(",")[0].strip()
                
                # Record to APM monitor
                apm_monitor.record_request(
                    endpoint=endpoint,
                    path=path,
                    method=method,
                    status_code=status_code,
                    duration_ms=duration_ms,
                    client_ip=client_ip
                )
                # Add APM Response header
                response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"
        except Exception:
            pass
        return response
