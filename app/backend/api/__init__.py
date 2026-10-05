"""
Package API cho toàn bộ hệ thống EnglishMate.
Cung cấp các phiên bản REST API chuẩn hóa (v1, v2...) hỗ trợ mobile app, frontend SPA, và tích hợp bên thứ ba.
"""
from .v1 import bp as api_v1_bp

__all__ = ["api_v1_bp"]
