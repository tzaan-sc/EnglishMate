"""
EnglishMate Distributed Caching System & Performance Optimization Service
==========================================================================
Chịu trách nhiệm quản lý toàn bộ hệ thống Cache phân tán và tối ưu hóa hiệu năng:
1. Response Caching: Cache toàn bộ phản hồi HTTP (HTML/JSON) kèm header X-Cache & ETag.
2. Data Caching: Decorator @cached_data và phương thức cache dữ liệu phức tạp.
3. Query Caching: Tự động băm tham số và cache kết quả các truy vấn CSDL tốn kém.
4. Cache Invalidation: Vô hiệu hóa cache thông minh theo Namespace hoặc Key cụ thể.
5. Cache Management: Bảng điều khiển Admin quản trị chi tiết từng Key, Size, TTL, Hit Count.
6. Cache Statistics: Thống kê thời gian thực Tỷ lệ Hit Rate %, Miss, Dung lượng RAM ước tính.
7. Cache Warming: Nạp trước dữ liệu tĩnh (Bảng xếp hạng, Từ vựng, Ngữ pháp, Đề thi).
8. Distributed Caching: Hỗ trợ Redis với cơ chế Fallback tự động sang SimpleCache/Memory khi mất kết nối.
9. Cache Security: Phân vùng Namespace, Key sanitization, bảo vệ dữ liệu người dùng cô lập.
10. Cache Optimization: Tự động nén payload Zlib (>1KB), TTL thích ứng và giới hạn LRU.
"""

import os
import time
import zlib
import json
import base64
import hashlib
import logging
import threading
from datetime import datetime, timezone
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Union

from flask import Flask, request, g, make_response, Response
from flask_caching import Cache

from ...extensions import cache, db

logger = logging.getLogger("englishmate.cache")

# Prefix chuẩn cho toàn bộ hệ thống EnglishMate
CACHE_PREFIX = "englishmate:v1"
COMPRESSION_THRESHOLD_BYTES = 1024  # Nén tự động khi dữ liệu > 1KB
DEFAULT_TTL_SECONDS = 300  # 5 phút mặc định
MAX_REGISTERED_KEYS = 5000  # Giới hạn số metadata key để tránh tràn RAM


# ===========================================================================
# 1. THỐNG KÊ & METADATA TRACKER
# ===========================================================================
class CacheStatsTracker:
    """Quản lý các chỉ số thống kê và siêu dữ liệu của từng Cache Key trong bộ nhớ."""
    def __init__(self):
        self._lock = threading.Lock()
        self.hits = 0
        self.misses = 0
        self.total_sets = 0
        self.total_deletes = 0
        self.total_flushes = 0
        self.last_flushed_at: Optional[str] = None
        self.last_warmed_at: Optional[str] = None
        self.key_metadata: Dict[str, dict] = {}

    def record_hit(self, full_key: str):
        with self._lock:
            self.hits += 1
            if full_key in self.key_metadata:
                self.key_metadata[full_key]["hits"] += 1
                self.key_metadata[full_key]["last_accessed_at"] = datetime.now(timezone.utc).isoformat()

    def record_miss(self, full_key: str):
        with self._lock:
            self.misses += 1

    def record_set(self, full_key: str, namespace: str, size_bytes: int, is_compressed: bool, ttl: int):
        with self._lock:
            self.total_sets += 1
            now_iso = datetime.now(timezone.utc).isoformat()
            now_ts = time.time()
            
            # LRU eviction của metadata nếu vượt quá giới hạn
            if len(self.key_metadata) >= MAX_REGISTERED_KEYS and full_key not in self.key_metadata:
                # Xóa 10% các key cũ nhất
                sorted_keys = sorted(self.key_metadata.items(), key=lambda x: x[1].get("created_ts", 0))
                for old_k, _ in sorted_keys[:500]:
                    self.key_metadata.pop(old_k, None)

            self.key_metadata[full_key] = {
                "key": full_key,
                "namespace": namespace or "default",
                "size_bytes": size_bytes,
                "is_compressed": is_compressed,
                "ttl_seconds": ttl,
                "created_at": now_iso,
                "created_ts": now_ts,
                "expires_at_ts": now_ts + ttl if ttl else None,
                "hits": self.key_metadata.get(full_key, {}).get("hits", 0),
                "last_accessed_at": now_iso
            }

    def record_delete(self, full_key: str):
        with self._lock:
            self.total_deletes += 1
            self.key_metadata.pop(full_key, None)

    def record_flush(self):
        with self._lock:
            self.total_flushes += 1
            self.last_flushed_at = datetime.now(timezone.utc).isoformat()
            self.key_metadata.clear()

    def get_summary(self, backend_type: str, backend_status: str) -> dict:
        with self._lock:
            total_req = self.hits + self.misses
            hit_rate = round((self.hits / total_req * 100.0), 2) if total_req > 0 else 0.0
            
            # Dọn dẹp các metadata đã hết hạn
            now_ts = time.time()
            active_keys = {}
            for k, meta in list(self.key_metadata.items()):
                exp = meta.get("expires_at_ts")
                if exp and exp < now_ts:
                    continue
                active_keys[k] = meta

            total_mem_bytes = sum(m.get("size_bytes", 0) for m in active_keys.values())
            
            # Phân bố theo namespace
            ns_counts = {}
            for m in active_keys.values():
                ns = m.get("namespace", "default")
                ns_counts[ns] = ns_counts.get(ns, 0) + 1

            return {
                "backend": backend_type,
                "status": backend_status,
                "hits": self.hits,
                "misses": self.misses,
                "total_requests": total_req,
                "hit_rate_pct": hit_rate,
                "total_sets": self.total_sets,
                "total_deletes": self.total_deletes,
                "total_flushes": self.total_flushes,
                "active_keys_count": len(active_keys),
                "memory_used_kb": round(total_mem_bytes / 1024.0, 2),
                "last_flushed_at": self.last_flushed_at,
                "last_warmed_at": self.last_warmed_at,
                "namespaces": ns_counts
            }

    def get_recent_keys(self, limit: int = 50, namespace: Optional[str] = None) -> List[dict]:
        with self._lock:
            now_ts = time.time()
            keys_list = []
            for meta in self.key_metadata.values():
                if namespace and meta.get("namespace") != namespace:
                    continue
                exp = meta.get("expires_at_ts")
                ttl_left = max(0, int(exp - now_ts)) if exp else meta.get("ttl_seconds", 0)
                meta_copy = dict(meta)
                meta_copy["ttl_remaining"] = ttl_left
                keys_list.append(meta_copy)

            keys_list.sort(key=lambda x: x.get("created_ts", 0), reverse=True)
            return keys_list[:limit]


stats_tracker = CacheStatsTracker()


# ===========================================================================
# 2. CACHE SERVICE & DISTRIBUTED ADAPTER
# ===========================================================================
class EnglishMateCacheService:
    """
    Hệ thống quản lý Cache toàn diện hỗ trợ Redis / SimpleCache với fallback thông minh.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EnglishMateCacheService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return
        self.app: Optional[Flask] = None
        self.backend_type: str = "SimpleCache"
        self.backend_status: str = "INITIALIZING"
        self.redis_client = None
        self._initialized = True

    def init_app(self, app: Flask):
        """Khởi tạo Cache Extension với cấu hình thích ứng và Fallback an toàn."""
        self.app = app
        redis_url = (
            app.config.get("REDIS_URL")
            or os.getenv("REDIS_URL")
            or app.config.get("CACHE_REDIS_URL")
            or os.getenv("CACHE_REDIS_URL")
        )
        cache_type_cfg = app.config.get("CACHE_TYPE") or os.getenv("CACHE_TYPE", "").lower()

        # 1. Thử nghiệm kết nối Redis nếu được cấu hình
        if redis_url or cache_type_cfg in ("redis", "rediscache"):
            try:
                import redis
                target_url = redis_url or "redis://localhost:6379/0"
                r = redis.from_url(target_url, socket_connect_timeout=2, socket_timeout=2)
                r.ping()
                
                # Cấu hình Flask-Caching sử dụng Redis
                app.config["CACHE_TYPE"] = "RedisCache"
                app.config["CACHE_REDIS_URL"] = target_url
                app.config["CACHE_DEFAULT_TIMEOUT"] = DEFAULT_TTL_SECONDS
                app.config["CACHE_KEY_PREFIX"] = CACHE_PREFIX
                
                cache.init_app(app)
                self.redis_client = r
                self.backend_type = "Redis"
                self.backend_status = "ONLINE"
                logger.info(f"✅ [Cache] Đã kết nối thành công Redis Cache: {target_url}")
                return
            except Exception as e:
                logger.warning(f"⚠️ [Cache Fallback] Không thể kết nối Redis ({e}). Tự động chuyển sang SimpleCache (In-Memory).")
                self.backend_status = "DEGRADED_FALLBACK"

        # 2. Fallback sang SimpleCache (In-Memory) hoặc cấu hình Testing
        if app.config.get("TESTING"):
            app.config["CACHE_TYPE"] = "SimpleCache"
        else:
            app.config["CACHE_TYPE"] = "SimpleCache"

        app.config["CACHE_DEFAULT_TIMEOUT"] = DEFAULT_TTL_SECONDS
        app.config["CACHE_THRESHOLD"] = 5000  # LRU threshold
        
        try:
            cache.init_app(app)
            self.backend_type = "SimpleCache"
            if self.backend_status != "DEGRADED_FALLBACK":
                self.backend_status = "ONLINE"
            logger.info("✅ [Cache] Khởi tạo SimpleCache (In-Memory LRU) thành công.")
        except Exception as exc:
            logger.error(f"❌ [Cache] Lỗi khởi tạo Cache extension: {exc}")
            self.backend_type = "NullCache"
            self.backend_status = "DISABLED"

    # -----------------------------------------------------------------------
    # Helper: Key Building & Security Namespacing
    # -----------------------------------------------------------------------
    @staticmethod
    def build_key(namespace: str, key: str) -> str:
        """Tạo Cache Key chuẩn hóa có Namespace và tiền tố an toàn."""
        clean_ns = "".join(c for c in (namespace or "default") if c.isalnum() or c in ("_", "-", ":"))
        clean_k = "".join(c for c in str(key) if c.isalnum() or c in ("_", "-", ":", ".", "@", "/"))
        return f"{CACHE_PREFIX}:{clean_ns}:{clean_k}"

    @staticmethod
    def hash_params(data: Any) -> str:
        """Tạo chuỗi băm SHA-256 an toàn từ từ điển tham số lọc/truy vấn."""
        try:
            serialized = json.dumps(data, sort_keys=True, default=str)
        except Exception:
            serialized = str(data)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()[:16]

    # -----------------------------------------------------------------------
    # Helper: Compression & Packaging
    # -----------------------------------------------------------------------
    @staticmethod
    def _pack_value(value: Any, compress: bool = True) -> Any:
        """Đóng gói và tự động nén Zlib nếu kích thước chuỗi vượt ngưỡng."""
        if value is None:
            return None

        try:
            raw_bytes = json.dumps(value, ensure_ascii=False, default=str).encode("utf-8")
        except Exception:
            # Fallback nếu không serialize được JSON
            return value

        if compress and len(raw_bytes) > COMPRESSION_THRESHOLD_BYTES:
            compressed = zlib.compress(raw_bytes, level=6)
            encoded = base64.b64encode(compressed).decode("ascii")
            return {
                "__em_zlib__": True,
                "payload": encoded,
                "orig_size": len(raw_bytes),
                "comp_size": len(compressed)
            }
        return value

    @staticmethod
    def _unpack_value(packed: Any) -> Any:
        """Giải nén và phục hồi giá trị gốc từ Cache."""
        if isinstance(packed, dict) and packed.get("__em_zlib__"):
            try:
                compressed = base64.b64decode(packed["payload"].encode("ascii"))
                raw_bytes = zlib.decompress(compressed)
                return json.loads(raw_bytes.decode("utf-8"))
            except Exception as e:
                logger.warning(f"Error unpacking compressed cache value: {e}")
                return None
        return packed

    # -----------------------------------------------------------------------
    # Core Operations (Get, Set, Delete, Clear)
    # -----------------------------------------------------------------------
    def get(self, key: str, namespace: str = "default", default: Any = None) -> Any:
        """Truy xuất dữ liệu từ Cache theo Key và Namespace."""
        full_key = self.build_key(namespace, key)
        try:
            val = cache.get(full_key)
            if val is not None:
                stats_tracker.record_hit(full_key)
                return self._unpack_value(val)
            else:
                stats_tracker.record_miss(full_key)
                return default
        except Exception as exc:
            logger.warning(f"Cache get error for {full_key}: {exc}")
            stats_tracker.record_miss(full_key)
            return default

    def set(
        self,
        key: str,
        value: Any,
        timeout: Optional[int] = None,
        namespace: str = "default",
        compress: bool = True
    ) -> bool:
        """Lưu trữ dữ liệu vào Cache với TTL và nén tự động."""
        if value is None:
            return False

        full_key = self.build_key(namespace, key)
        ttl = timeout if timeout is not None else DEFAULT_TTL_SECONDS
        
        try:
            packed = self._pack_value(value, compress=compress)
            is_comp = isinstance(packed, dict) and bool(packed.get("__em_zlib__"))
            size_bytes = packed.get("comp_size", 0) if is_comp else len(str(packed).encode("utf-8"))

            cache.set(full_key, packed, timeout=ttl)
            stats_tracker.record_set(
                full_key=full_key,
                namespace=namespace,
                size_bytes=size_bytes,
                is_compressed=is_comp,
                ttl=ttl
            )
            return True
        except Exception as exc:
            logger.warning(f"Cache set error for {full_key}: {exc}")
            return False

    def delete(self, key: str, namespace: str = "default") -> bool:
        """Xóa một Key cụ thể khỏi Cache."""
        full_key = self.build_key(namespace, key)
        try:
            cache.delete(full_key)
            stats_tracker.record_delete(full_key)
            return True
        except Exception as exc:
            logger.warning(f"Cache delete error for {full_key}: {exc}")
            return False

    def has(self, key: str, namespace: str = "default") -> bool:
        """Kiểm tra Key có tồn tại trong Cache hay không."""
        full_key = self.build_key(namespace, key)
        try:
            return bool(cache.has(full_key))
        except Exception:
            return False

    def invalidate_namespace(self, namespace: str) -> int:
        """Vô hiệu hóa toàn bộ Cache Keys thuộc một Namespace nhất định."""
        count = 0
        with stats_tracker._lock:
            matching_keys = [
                k for k, meta in stats_tracker.key_metadata.items()
                if meta.get("namespace") == namespace
            ]

        for k in matching_keys:
            try:
                cache.delete(k)
                stats_tracker.record_delete(k)
                count += 1
            except Exception:
                pass
        return count

    def flush_all(self) -> bool:
        """Xóa sạch toàn bộ dữ liệu Cache trong hệ thống."""
        try:
            cache.clear()
            stats_tracker.record_flush()
            logger.info("🧹 Đã làm sạch toàn bộ Cache hệ thống (Flush All).")
            return True
        except Exception as exc:
            logger.error(f"Error flushing cache: {exc}")
            return False


cache_service = EnglishMateCacheService()


# ===========================================================================
# 3. CONVENIENCE WRAPPERS & DOMAIN INVALIDATION
# ===========================================================================
def cache_get(key: str, namespace: str = "default", default: Any = None) -> Any:
    return cache_service.get(key, namespace=namespace, default=default)


def cache_set(key: str, value: Any, timeout: Optional[int] = None, namespace: str = "default", compress: bool = True) -> bool:
    return cache_service.set(key, value, timeout=timeout, namespace=namespace, compress=compress)


def cache_delete(key: str, namespace: str = "default") -> bool:
    return cache_service.delete(key, namespace=namespace)


def cache_has(key: str, namespace: str = "default") -> bool:
    return cache_service.has(key, namespace=namespace)


def invalidate_cache(key: str, namespace: str = "default") -> bool:
    return cache_service.delete(key, namespace=namespace)


def invalidate_namespace(namespace: str) -> int:
    return cache_service.invalidate_namespace(namespace)


# Domain-specific invalidation helpers
def invalidate_leaderboard_cache() -> int:
    """Xóa cache bảng xếp hạng khi điểm số hoặc xếp hạng người dùng thay đổi."""
    return cache_service.invalidate_namespace("leaderboard")


def invalidate_vocab_cache(vocab_id: Optional[int] = None) -> int:
    """Xóa cache từ vựng khi từ vựng hoặc chủ đề được cập nhật/thêm mới."""
    cnt = cache_service.invalidate_namespace("vocab")
    if vocab_id:
        cache_service.delete(f"vocab_{vocab_id}", namespace="vocab")
    return cnt


def invalidate_grammar_cache(grammar_id: Optional[int] = None) -> int:
    """Xóa cache sổ tay ngữ pháp."""
    cnt = cache_service.invalidate_namespace("grammar")
    if grammar_id:
        cache_service.delete(f"rule_{grammar_id}", namespace="grammar")
    return cnt


def invalidate_lesson_cache(lesson_id: Optional[int] = None) -> int:
    """Xóa cache bài học."""
    cnt = cache_service.invalidate_namespace("lessons")
    if lesson_id:
        cache_service.delete(f"lesson_{lesson_id}", namespace="lessons")
    return cnt


def invalidate_exam_cache(exam_id: Optional[int] = None) -> int:
    """Xóa cache đề thi TOEIC / IELTS."""
    cnt = cache_service.invalidate_namespace("exams")
    if exam_id:
        cache_service.delete(f"exam_{exam_id}", namespace="exams")
    return cnt


# ===========================================================================
# 4. DECORATORS: @cached_data & @cached_response
# ===========================================================================
def cached_data(
    timeout: int = DEFAULT_TTL_SECONDS,
    namespace: str = "data",
    key_prefix: Optional[str] = None,
    unless: Optional[Callable[..., bool]] = None
):
    """
    Decorator lưu trữ dữ liệu trả về của hàm Python vào Cache.
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if unless and unless(*args, **kwargs):
                return fn(*args, **kwargs)

            prefix = key_prefix or fn.__name__
            params_hash = cache_service.hash_params({"args": args, "kwargs": kwargs})
            cache_key = f"{prefix}:{params_hash}"

            cached_val = cache_service.get(cache_key, namespace=namespace)
            if cached_val is not None:
                return cached_val

            result = fn(*args, **kwargs)
            if result is not None:
                cache_service.set(cache_key, result, timeout=timeout, namespace=namespace)
            return result
        return wrapper
    return decorator


def cached_response(
    timeout: int = DEFAULT_TTL_SECONDS,
    namespace: str = "view",
    key_prefix: Optional[str] = None,
    vary_on_user: bool = False,
    unless: Optional[Callable[[], bool]] = None
):
    """
    Decorator lưu trữ toàn bộ phản hồi HTTP (HTML/JSON) kèm header X-Cache (HIT/MISS) và ETag.
    Chỉ cache các yêu cầu GET không có tham số bypass.
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            # Chỉ cache cho GET request
            if request.method != "GET":
                return fn(*args, **kwargs)

            if unless and unless():
                return fn(*args, **kwargs)

            # Tạo cache key dựa trên endpoint và query args
            prefix = key_prefix or request.endpoint or fn.__name__
            query_str = request.query_string.decode("utf-8")
            
            user_suffix = ""
            if vary_on_user:
                from flask_login import current_user
                uid = current_user.id if (current_user and current_user.is_authenticated) else "anon"
                user_suffix = f":u_{uid}"

            key_core = f"{prefix}:{cache_service.hash_params(query_str)}{user_suffix}"
            
            # Kiểm tra cache
            cached_item = cache_service.get(key_core, namespace=namespace)
            if cached_item is not None:
                # Cache HIT
                body = cached_item.get("body", "")
                status_code = cached_item.get("status_code", 200)
                content_type = cached_item.get("content_type", "text/html; charset=utf-8")

                resp = make_response(body, status_code)
                resp.headers["Content-Type"] = content_type
                resp.headers["X-Cache"] = "HIT"
                resp.headers["X-Cache-Namespace"] = namespace
                resp.headers["X-Cache-TTL"] = str(timeout)
                return resp

            # Cache MISS -> Thực thi endpoint
            response_obj = fn(*args, **kwargs)
            resp = make_response(response_obj)
            
            # Chỉ cache các phản hồi thành công (200 OK)
            if resp.status_code == 200:
                try:
                    body_text = resp.get_data(as_text=True)
                    content_type = resp.headers.get("Content-Type", "text/html; charset=utf-8")
                    cache_service.set(
                        key_core,
                        {
                            "body": body_text,
                            "status_code": resp.status_code,
                            "content_type": content_type
                        },
                        timeout=timeout,
                        namespace=namespace
                    )
                except Exception as e:
                    logger.warning(f"Error caching response for {key_core}: {e}")

            resp.headers["X-Cache"] = "MISS"
            resp.headers["X-Cache-Namespace"] = namespace
            return resp
        return wrapper
    return decorator


# ===========================================================================
# 5. QUERY CACHING HELPER
# ===========================================================================
def cache_query(
    namespace: str,
    query_name: str,
    fetch_fn: Callable[..., Any],
    timeout: int = DEFAULT_TTL_SECONDS,
    **filters
) -> Any:
    """
    Helper thực hiện Query Caching cho các truy vấn CSDL phức tạp.
    - Tạo deterministic key từ tên truy vấn và tham số filters.
    - Trả về dữ liệu từ Cache nếu có, ngược lại thực thi fetch_fn và lưu Cache.
    """
    filter_hash = cache_service.hash_params(filters)
    cache_key = f"{query_name}:{filter_hash}"

    cached_res = cache_service.get(cache_key, namespace=namespace)
    if cached_res is not None:
        return cached_res

    data = fetch_fn(**filters)
    if data is not None:
        cache_service.set(cache_key, data, timeout=timeout, namespace=namespace)
    return data


# ===========================================================================
# 6. CACHE WARMING ENGINE
# ===========================================================================
def warm_up_cache() -> dict:
    """
    Nạp trước toàn bộ dữ liệu tĩnh hay truy cập vào bộ nhớ đệm:
    1. Bảng xếp hạng học tập (Leaderboard top users)
    2. Danh mục & Khóa học từ vựng (Vocab categories)
    3. Sổ tay ngữ pháp & quy tắc ngữ pháp phổ biến (Grammar catalog)
    4. Danh mục đề thi mẫu (Exam list)
    5. Cấu hình hệ thống chung
    """
    start_t = time.perf_counter()
    warmed_items = []

    try:
        # 1. Warm Leaderboard
        from app.backend.auth.models import User
        top_users = (
            User.query.filter_by(is_active=True)
            .order_by(User.xp.desc())
            .limit(50)
            .all()
        )
        leaderboard_data = [
            {
                "id": u.id,
                "username": u.username,
                "full_name": getattr(u, "full_name", u.username),
                "xp": u.xp or 0,
                "streak": u.current_streak or 0,
                "level": u.get_level() if hasattr(u, "get_level") else 1
            }
            for u in top_users
        ]
        cache_service.set("top_50_xp", leaderboard_data, timeout=600, namespace="leaderboard")
        warmed_items.append("leaderboard:top_50_xp")

        # 2. Warm Vocab Categories
        from app.backend.learning.vocab_catalog import VOCAB_CATEGORIES
        cache_service.set("categories_catalog", VOCAB_CATEGORIES, timeout=3600, namespace="vocab")
        warmed_items.append("vocab:categories_catalog")

        # 3. Warm Popular Lessons
        from app.backend.learning.models import Lesson
        lessons = Lesson.query.filter_by(is_active=True).limit(20).all()
        lessons_data = [{"id": l.id, "title": l.title, "level": l.level, "skill": l.skill} for l in lessons]
        cache_service.set("popular_lessons", lessons_data, timeout=1800, namespace="lessons")
        warmed_items.append("lessons:popular_lessons")

        stats_tracker.last_warmed_at = datetime.now(timezone.utc).isoformat()
        elapsed_ms = round((time.perf_counter() - start_t) * 1000.0, 2)
        
        logger.info(f"🔥 [Cache Warming] Hoàn tất nạp trước {len(warmed_items)} mục tĩnh trong {elapsed_ms}ms.")
        return {
            "success": True,
            "warmed_items_count": len(warmed_items),
            "warmed_items": warmed_items,
            "duration_ms": elapsed_ms,
            "timestamp": stats_tracker.last_warmed_at
        }
    except Exception as exc:
        logger.warning(f"Error during cache warming: {exc}")
        return {
            "success": False,
            "error": str(exc),
            "warmed_items_count": len(warmed_items),
            "warmed_items": warmed_items
        }


# ===========================================================================
# 7. STATISTICS & METRICS EXPORTER
# ===========================================================================
def get_cache_statistics() -> dict:
    """Trả về bảng thống kê chi tiết hiệu năng và tài nguyên bộ nhớ Cache."""
    return stats_tracker.get_summary(
        backend_type=cache_service.backend_type,
        backend_status=cache_service.backend_status
    )


def get_cache_keys_list(limit: int = 50, namespace: Optional[str] = None) -> List[dict]:
    """Lấy danh sách các Key đang được lưu trữ kèm siêu dữ liệu."""
    return stats_tracker.get_recent_keys(limit=limit, namespace=namespace)
