"""
Log Analysis & Retention Engine for EnglishMate.
Provides multi-source log reading, parsing, regex keyword filtering, level distribution,
file rotation, compression (gzip), and automated cleanup of expired log archives.
"""

import os
import re
import gzip
import shutil
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional

from .log_service import get_log_retention_days

logger = logging.getLogger("englishmate.log_analysis")

# Default max log file size before rotation (10 MB)
DEFAULT_MAX_LOG_BYTES = 10 * 1024 * 1024


class LogAnalysisService:
    @staticmethod
    def get_log_directory() -> str:
        """Get absolute path to instance/logs directory."""
        try:
            from flask import current_app
            if current_app:
                base = os.path.join(current_app.instance_path, "logs")
                os.makedirs(base, exist_ok=True)
                return base
        except Exception:
            pass
        base = os.path.abspath("instance/logs")
        os.makedirs(base, exist_ok=True)
        return base

    @classmethod
    def get_available_log_files(cls) -> List[Dict[str, Any]]:
        """List all log files with sizes, modification dates, and line counts."""
        log_dir = cls.get_log_directory()
        files = []
        if not os.path.exists(log_dir):
            return files

        for fname in os.listdir(log_dir):
            fpath = os.path.join(log_dir, fname)
            if os.path.isfile(fpath):
                stat = os.stat(fpath)
                size_mb = round(stat.st_size / (1024 * 1024), 2)
                size_kb = round(stat.st_size / 1024, 1)
                mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                is_compressed = fname.endswith(".gz") or fname.endswith(".zip")
                
                # Approximate line count for non-compressed
                line_count = 0
                if not is_compressed and stat.st_size < 20 * 1024 * 1024:
                    try:
                        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                            line_count = sum(1 for _ in f)
                    except Exception:
                        line_count = 0

                files.append({
                    "filename": fname,
                    "path": fpath,
                    "size_mb": size_mb,
                    "size_kb": size_kb,
                    "size_bytes": stat.st_size,
                    "modified_at": mtime,
                    "line_count": line_count,
                    "is_compressed": is_compressed,
                })

        files.sort(key=lambda x: x["modified_at"], reverse=True)
        return files

    @classmethod
    def search_and_analyze_logs(
        cls,
        filename: Optional[str] = None,
        level: str = "ALL",
        keyword: str = "",
        date_range: str = "all",  # today, 7days, 30days, all
        limit: int = 200,
    ) -> Dict[str, Any]:
        """
        Search and parse log files with multi-criteria filtering.
        Returns matching log entries and distribution stats.
        """
        log_dir = cls.get_log_directory()
        target_files = []

        if filename and filename != "ALL":
            target_path = os.path.join(log_dir, filename)
            if os.path.exists(target_path):
                target_files.append((filename, target_path))
        else:
            for f in os.listdir(log_dir):
                if f.endswith(".log"):
                    target_files.append((f, os.path.join(log_dir, f)))

        level_filter = level.upper() if level else "ALL"
        keyword_clean = keyword.strip().lower() if keyword else ""

        # Compute cutoff timestamp
        now = datetime.now()
        cutoff_dt = None
        if date_range == "today":
            cutoff_dt = datetime(now.year, now.month, now.day)
        elif date_range == "7days":
            cutoff_dt = now - timedelta(days=7)
        elif date_range == "30days":
            cutoff_dt = now - timedelta(days=30)

        entries = []
        level_counts = {"DEBUG": 0, "INFO": 0, "WARNING": 0, "ERROR": 0, "CRITICAL": 0, "UNKNOWN": 0}
        total_scanned_lines = 0

        # Pattern matches: [2026-10-06 09:15:30] [LEVEL] [LOGGER] Message OR [2026-10-06 09:15:30] Message
        log_pattern = re.compile(
            r"^\[(?P<timestamp>\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}(?:\.\d+)?)\]\s*(?:\[(?P<level>[A-Z]+)\])?\s*(?:\[(?P<logger>[^\]]+)\])?\s*(?P<message>.*)$"
        )

        for fname, fpath in target_files:
            try:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
                    total_scanned_lines += len(lines)

                    for idx, raw_line in enumerate(lines):
                        line = raw_line.strip()
                        if not line:
                            continue

                        m = log_pattern.match(line)
                        if m:
                            ts_str = m.group("timestamp")
                            lvl = (m.group("level") or "INFO").upper()
                            log_name = m.group("logger") or fname
                            msg = m.group("message")
                        else:
                            ts_str = ""
                            lvl = "INFO"
                            if "error" in line.lower() or "exception" in line.lower():
                                lvl = "ERROR"
                            elif "warn" in line.lower():
                                lvl = "WARNING"
                            elif "crit" in line.lower() or "fatal" in line.lower():
                                lvl = "CRITICAL"
                            elif "debug" in line.lower():
                                lvl = "DEBUG"
                            log_name = fname
                            msg = line

                        # Level count aggregation
                        if lvl in level_counts:
                            level_counts[lvl] += 1
                        else:
                            level_counts["UNKNOWN"] += 1

                        # Filters:
                        # 1. Level Filter
                        if level_filter != "ALL" and lvl != level_filter:
                            continue

                        # 2. Date Filter
                        if cutoff_dt and ts_str:
                            try:
                                entry_dt = datetime.strptime(ts_str[:19], "%Y-%m-%d %H:%M:%S")
                                if entry_dt < cutoff_dt:
                                    continue
                            except Exception:
                                pass

                        # 3. Keyword Filter
                        if keyword_clean and (keyword_clean not in msg.lower() and keyword_clean not in log_name.lower()):
                            continue

                        entries.append({
                            "source_file": fname,
                            "line_number": idx + 1,
                            "timestamp": ts_str or now.strftime("%Y-%m-%d %H:%M:%S"),
                            "level": lvl,
                            "logger": log_name,
                            "message": msg,
                            "raw": line,
                        })

            except Exception as e:
                logger.warning(f"Error reading log file {fpath}: {e}")

        # Reverse sort by line / timestamp
        entries = entries[-limit:][::-1]

        return {
            "total_scanned_lines": total_scanned_lines,
            "matching_count": len(entries),
            "level_counts": level_counts,
            "entries": entries,
            "filters": {
                "filename": filename or "ALL",
                "level": level_filter,
                "keyword": keyword,
                "date_range": date_range,
            }
        }

    @classmethod
    def rotate_log_file(cls, filename: str) -> Dict[str, Any]:
        """Rotate and compress a specific log file to .gz archive."""
        log_dir = cls.get_log_directory()
        src_path = os.path.join(log_dir, filename)

        if not os.path.exists(src_path) or not os.path.isfile(src_path):
            return {"success": False, "error": f"Tệp nhật ký {filename} không tồn tại."}

        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_name = f"{filename}.{timestamp_str}.gz"
        archive_path = os.path.join(log_dir, archive_name)

        try:
            with open(src_path, "rb") as f_in:
                with gzip.open(archive_path, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)

            # Truncate source file
            with open(src_path, "w", encoding="utf-8") as f_trunc:
                f_trunc.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [INFO] [LogRotation] Log rotated and archived to {archive_name}\n")

            return {
                "success": True,
                "rotated_file": filename,
                "archive_name": archive_name,
                "archive_path": archive_path,
                "message": f"Đã xoay vòng và nén tệp {filename} thành {archive_name} thành công."
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @classmethod
    def cleanup_expired_log_archives(cls, retention_days: Optional[int] = None) -> Dict[str, Any]:
        """Delete rotated log archives older than retention days."""
        days = retention_days if (retention_days is not None and retention_days >= 0) else get_log_retention_days()
        cutoff_date = datetime.now() - timedelta(days=days)
        log_dir = cls.get_log_directory()

        deleted_files = []
        freed_bytes = 0

        for fname in os.listdir(log_dir):
            if fname.endswith(".gz") or fname.endswith(".bak") or fname.endswith(".zip"):
                fpath = os.path.join(log_dir, fname)
                try:
                    stat = os.stat(fpath)
                    mtime = datetime.fromtimestamp(stat.st_mtime)
                    if mtime < cutoff_date:
                        freed_bytes += stat.st_size
                        os.remove(fpath)
                        deleted_files.append(fname)
                except Exception:
                    pass

        return {
            "success": True,
            "retention_days": days,
            "cutoff_date": cutoff_date.strftime("%Y-%m-%d %H:%M:%S"),
            "deleted_count": len(deleted_files),
            "deleted_files": deleted_files,
            "freed_mb": round(freed_bytes / (1024 * 1024), 2),
            "message": f"Đã dọn dẹp {len(deleted_files)} tệp lưu trữ nhật ký cũ hơn {days} ngày (Giải phóng {round(freed_bytes / (1024 * 1024), 2)} MB)."
        }

    @classmethod
    def get_log_storage_overview(cls) -> Dict[str, Any]:
        """Get summary of total disk usage used by system logs."""
        log_dir = cls.get_log_directory()
        files = cls.get_available_log_files()
        total_bytes = sum(f["size_bytes"] for f in files)
        active_logs = [f for f in files if not f["is_compressed"]]
        archive_logs = [f for f in files if f["is_compressed"]]

        return {
            "log_dir": log_dir,
            "total_files_count": len(files),
            "active_logs_count": len(active_logs),
            "archive_logs_count": len(archive_logs),
            "total_size_mb": round(total_bytes / (1024 * 1024), 2),
            "retention_days": get_log_retention_days(),
            "files": files,
        }


# Singleton alias
log_analysis_service = LogAnalysisService()
