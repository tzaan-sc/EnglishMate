from datetime import datetime, timezone
from flask import jsonify, request
from . import bp
from app.extensions import limiter


@bp.get("/meta")
def api_meta():
    """
    Lấy thông tin siêu dữ liệu (Metadata) và phiên bản của EnglishMate REST API.
    ---
    tags:
      - System & Meta
    responses:
      200:
        description: Thông tin phiên bản và tài nguyên API
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            version:
              type: string
              example: "v1"
            name:
              type: string
              example: "EnglishMate REST API"
            server_time:
              type: string
            docs_url:
              type: string
              example: "/api/v1/docs"
    """
    return jsonify({
        "success": True,
        "name": "EnglishMate REST API",
        "version": "v1.0.0",
        "description": "RESTful API cung cấp dữ liệu bài học, từ vựng, trắc nghiệm và thống kê học tập.",
        "server_time": datetime.now(timezone.utc).isoformat(),
        "docs_url": "/api/v1/docs",
        "endpoints": {
            "meta": "/api/v1/meta",
            "health": "/api/v1/health",
            "lessons": "/api/v1/lessons",
            "vocabulary": "/api/v1/vocabulary",
            "quizzes": "/api/v1/quizzes",
            "stats": "/api/v1/stats",
        }
    })


@bp.get("/health")
def api_health():
    """
    Kiểm tra trạng thái hoạt động (Healthcheck) của máy chủ API và kết nối CSDL.
    ---
    tags:
      - System & Meta
    responses:
      200:
        description: Trạng thái máy chủ khỏe mạnh (Healthy)
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            status:
              type: string
              example: "healthy"
            database:
              type: string
              example: "connected"
    """
    from app.extensions import db
    db_status = "connected"
    try:
        db.session.execute(db.text("SELECT 1")).fetchone()
    except Exception as e:
        db_status = f"error: {str(e)}"

    return jsonify({
        "success": True,
        "status": "healthy" if db_status == "connected" else "degraded",
        "database": db_status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


@bp.get("/ping")
@limiter.limit("120 per minute")
def api_ping():
    """
    Endpoint phản hồi nhanh kiểm tra độ trễ (Ping).
    ---
    tags:
      - System & Meta
    responses:
      200:
        description: Pong response
        schema:
          type: object
          properties:
            pong:
              type: boolean
              example: true
    """
    return jsonify({"pong": True, "time": datetime.now(timezone.utc).isoformat()})
