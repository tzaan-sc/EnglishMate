from flask import jsonify, request
from . import bp
from app.extensions import db
from app.backend.learning.models import Lesson


@bp.get("/lessons")
def api_get_lessons():
    """
    Lấy danh sách các bài học (Lessons) có hỗ trợ phân trang và lọc theo cấp độ/kỹ năng.
    ---
    tags:
      - Lessons
    parameters:
      - name: level
        in: query
        type: string
        required: false
        description: Lọc theo cấp độ CEFR (A1, A2, B1, B2, C1, C2)
      - name: skill
        in: query
        type: string
        required: false
        description: Lọc theo kỹ năng (Grammar, Vocabulary, Reading, Listening, Speaking, Writing)
      - name: search
        in: query
        type: string
        required: false
        description: Tìm kiếm theo tiêu đề hoặc mô tả
      - name: page
        in: query
        type: integer
        required: false
        default: 1
      - name: per_page
        in: query
        type: integer
        required: false
        default: 12
    responses:
      200:
        description: Danh sách bài học kèm thông tin phân trang
    """
    level = request.args.get("level", "").strip()
    skill = request.args.get("skill", "").strip()
    search = request.args.get("search", "").strip()
    
    try:
        page = max(1, int(request.args.get("page", 1)))
    except (ValueError, TypeError):
        page = 1
        
    try:
        per_page = min(50, max(1, int(request.args.get("per_page", 12))))
    except (ValueError, TypeError):
        per_page = 12

    query = Lesson.query

    if level:
        query = query.filter(Lesson.level == level.upper())
    if skill:
        query = query.filter(Lesson.skill.ilike(f"%{skill}%"))
    if search:
        query = query.filter(
            (Lesson.title.ilike(f"%{search}%")) |
            (Lesson.short_description.ilike(f"%{search}%"))
        )

    total = query.count()
    items = query.order_by(Lesson.id.asc()).offset((page - 1) * per_page).limit(per_page).all()

    data = []
    for item in items:
        data.append({
            "id": item.id,
            "title": item.title,
            "level": item.level,
            "skill": item.skill,
            "short_description": item.short_description,
            "view_count": getattr(item, "view_count", 0),
            "created_at": item.created_at.isoformat() if getattr(item, "created_at", None) else None,
        })

    return jsonify({
        "success": True,
        "data": data,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total_items": total,
            "total_pages": (total + per_page - 1) // per_page,
            "has_next": (page * per_page) < total,
            "has_prev": page > 1,
        }
    })


@bp.get("/lessons/<int:lesson_id>")
def api_get_lesson_detail(lesson_id):
    """
    Lấy nội dung chi tiết của một bài học theo ID.
    ---
    tags:
      - Lessons
    parameters:
      - name: lesson_id
        in: path
        type: integer
        required: true
        description: ID bài học
    responses:
      200:
        description: Chi tiết bài học
      404:
        description: Không tìm thấy bài học
    """
    lesson = db.session.get(Lesson, lesson_id)
    if not lesson:
        return jsonify({
            "success": False,
            "error": "Not Found",
            "message": f"Không tìm thấy bài học với ID {lesson_id}",
        }), 404

    return jsonify({
        "success": True,
        "data": {
            "id": lesson.id,
            "title": lesson.title,
            "level": lesson.level,
            "skill": lesson.skill,
            "short_description": lesson.short_description,
            "content": lesson.content,
            "examples": lesson.examples,
            "view_count": getattr(lesson, "view_count", 0),
            "skill_data": getattr(lesson, "skill_data", None),
        }
    })


@bp.get("/lessons/skills")
def api_get_lesson_skills():
    """
    Lấy danh sách các phân loại kỹ năng bài học có trong hệ thống.
    ---
    tags:
      - Lessons
    responses:
      200:
        description: Danh sách kỹ năng
    """
    results = db.session.query(Lesson.skill).filter(Lesson.skill.isnot(None)).distinct().all()
    skills = sorted(list({r[0] for r in results if r[0]}))
    return jsonify({
        "success": True,
        "data": skills
    })


@bp.get("/lessons/levels")
def api_get_lesson_levels():
    """
    Lấy danh sách các cấp độ CEFR có sẵn.
    ---
    tags:
      - Lessons
    responses:
      200:
        description: Danh sách cấp độ
    """
    results = db.session.query(Lesson.level).filter(Lesson.level.isnot(None)).distinct().all()
    levels = sorted(list({r[0] for r in results if r[0]}))
    return jsonify({
        "success": True,
        "data": levels
    })
