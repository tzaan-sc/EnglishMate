"""
Slow Query Performance Logger for EnglishMate.
Hooks into SQLAlchemy Engine execution events to detect and record slow database queries (>500ms).
Supports in-memory ring buffer, parameter masking, query template normalization, and file logging.
"""

import time
import os
import re
import threading
import logging
from collections import deque, defaultdict
from datetime import datetime
from typing import Dict, List, Any, Optional

from sqlalchemy import event
from sqlalchemy.engine import Engine

logger = logging.getLogger("englishmate.slow_queries")

# Default slow query threshold in milliseconds
DEFAULT_SLOW_QUERY_THRESHOLD_MS = 500.0


class SlowQueryMonitor:
    def __init__(self, max_history: int = 500, default_threshold_ms: float = DEFAULT_SLOW_QUERY_THRESHOLD_MS):
        self.lock = threading.Lock()
        self.max_history = max_history
        self.threshold_ms = default_threshold_ms
        self.slow_queries: deque = deque(maxlen=max_history)
        self.total_slow_queries_count = 0
        self.max_query_ms = 0.0
        self.total_slow_duration_ms = 0.0
        
        # Aggregated stats by normalized query template
        self.query_templates: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "count": 0,
            "total_ms": 0.0,
            "max_ms": 0.0,
            "min_ms": float("inf"),
            "sample_statement": "",
            "last_seen": "",
        })

    def record_slow_query(
        self,
        statement: str,
        duration_ms: float,
        parameters: Any = None,
        context: Optional[str] = None
    ) -> None:
        """Record a slow database query."""
        now = datetime.now()
        timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S")
        norm_template = self._normalize_sql(statement)
        sanitized_params = self._sanitize_parameters(parameters)

        record = {
            "timestamp": timestamp_str,
            "statement": statement.strip(),
            "normalized_template": norm_template,
            "duration_ms": round(duration_ms, 2),
            "parameters": sanitized_params,
            "context": context or "SQLAlchemy Engine",
        }

        with self.lock:
            self.total_slow_queries_count += 1
            self.total_slow_duration_ms += duration_ms
            self.max_query_ms = max(self.max_query_ms, duration_ms)
            self.slow_queries.append(record)

            # Template aggregation
            t_stats = self.query_templates[norm_template]
            t_stats["count"] += 1
            t_stats["total_ms"] += duration_ms
            t_stats["max_ms"] = max(t_stats["max_ms"], duration_ms)
            t_stats["min_ms"] = min(t_stats["min_ms"], duration_ms)
            t_stats["sample_statement"] = statement.strip()[:300]
            t_stats["last_seen"] = timestamp_str

        # Write to log file if instance/logs directory exists
        self._write_to_log_file(record)

    def get_summary(self) -> Dict[str, Any]:
        """Get high-level statistics about slow queries."""
        with self.lock:
            avg_ms = round(self.total_slow_duration_ms / self.total_slow_queries_count, 2) if self.total_slow_queries_count > 0 else 0.0
            return {
                "total_slow_queries": self.total_slow_queries_count,
                "current_buffer_count": len(self.slow_queries),
                "threshold_ms": self.threshold_ms,
                "max_query_ms": round(self.max_query_ms, 2),
                "avg_query_ms": avg_ms,
                "distinct_slow_templates": len(self.query_templates),
            }

    def get_recent_slow_queries(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Return the most recent slow queries in reverse chronological order."""
        with self.lock:
            items = list(self.slow_queries)
            return items[-limit:][::-1]

    def get_top_slow_templates(self, limit: int = 15) -> List[Dict[str, Any]]:
        """Return the slowest SQL query templates ranked by total/average time."""
        with self.lock:
            results = []
            for template, stats in self.query_templates.items():
                cnt = stats["count"]
                if cnt == 0:
                    continue
                avg_ms = round(stats["total_ms"] / cnt, 2)
                results.append({
                    "template": template,
                    "sample_statement": stats["sample_statement"],
                    "count": cnt,
                    "avg_ms": avg_ms,
                    "max_ms": round(stats["max_ms"], 2),
                    "min_ms": round(stats["min_ms"], 2) if stats["min_ms"] != float("inf") else 0.0,
                    "total_ms": round(stats["total_ms"], 2),
                    "last_seen": stats["last_seen"],
                })

            # Sort by total time descending
            results.sort(key=lambda x: x["total_ms"], reverse=True)
            return results[:limit]

    def reset_metrics(self) -> None:
        """Reset all slow query statistics."""
        with self.lock:
            self.slow_queries.clear()
            self.query_templates.clear()
            self.total_slow_queries_count = 0
            self.max_query_ms = 0.0
            self.total_slow_duration_ms = 0.0

    def set_threshold(self, threshold_ms: float) -> None:
        """Update slow query threshold."""
        if threshold_ms > 0:
            self.threshold_ms = float(threshold_ms)

    @staticmethod
    def _normalize_sql(sql: str) -> str:
        """Normalize SQL query by replacing numbers, quoted strings, and parameter placeholders."""
        cleaned = re.sub(r"\s+", " ", sql).strip()
        # Replace string literals
        cleaned = re.sub(r"'[^']*'", "'?'", cleaned)
        # Replace numeric literals
        cleaned = re.sub(r"\b\d+\b", "?", cleaned)
        # Replace IN (...) lists
        cleaned = re.sub(r"\bIN\s*\([^\)]+\)", "IN (...) ", cleaned, flags=re.IGNORECASE)
        return cleaned[:300]

    @staticmethod
    def _sanitize_parameters(params: Any) -> Any:
        """Sanitize query parameters for safe logging."""
        if params is None:
            return None
        if isinstance(params, (list, tuple)):
            return [str(p)[:50] for p in params[:10]]
        if isinstance(params, dict):
            return {k: (str(v)[:50] if "password" not in str(k).lower() else "***") for k, v in list(params.items())[:10]}
        return str(params)[:100]

    def _write_to_log_file(self, record: Dict[str, Any]) -> None:
        """Append slow query record to instance/logs/slow_queries.log."""
        try:
            from flask import current_app
            log_dir = os.path.join(current_app.instance_path, "logs") if current_app else "instance/logs"
        except Exception:
            log_dir = "instance/logs"

        try:
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, "slow_queries.log")
            line = f"[{record['timestamp']}] [{record['duration_ms']}ms] {record['statement']}\n"
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(line)
        except Exception:
            pass


# Global singleton monitor
slow_query_monitor = SlowQueryMonitor()


def init_slow_query_logger(app):
    """Register SQLAlchemy Engine listeners to measure query execution duration."""
    threshold = float(app.config.get("SLOW_QUERY_THRESHOLD_MS", DEFAULT_SLOW_QUERY_THRESHOLD_MS))
    slow_query_monitor.set_threshold(threshold)

    @event.listens_for(Engine, "before_cursor_execute")
    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        conn.info.setdefault("query_start_time", []).append(time.perf_counter())

    @event.listens_for(Engine, "after_cursor_execute")
    def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        try:
            start_times = conn.info.get("query_start_time", [])
            if start_times:
                start_t = start_times.pop()
                duration_ms = (time.perf_counter() - start_t) * 1000.0
                
                # Check threshold
                if duration_ms >= slow_query_monitor.threshold_ms:
                    slow_query_monitor.record_slow_query(
                        statement=statement,
                        duration_ms=duration_ms,
                        parameters=parameters,
                        context="SQLAlchemy Engine"
                    )
        except Exception:
            pass
