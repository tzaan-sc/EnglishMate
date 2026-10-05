import random
from flask import jsonify, request
from . import bp
from app.extensions import db
from app.backend.learning.models import Question


@bp.get("/quizzes")
def api_get_quizzes():
    """
    Lấy danh sách các chủ đề và bộ đề trắc nghiệm có trong hệ thống kèm số lượng câu hỏi.
    ---
    tags:
      - Quizzes
    parameters:
      - name: level
        in: query
        type: string
        required: false
        description: Cấp độ CEFR
    responses:
      200:
        description: Thống kê các chủ đề trắc nghiệm
    """
    level = request.args.get("level", "").strip()
    
    query = db.session.query(
        Question.topic,
        Question.level,
        db.func.count(Question.id).label("total_questions")
    ).group_by(Question.topic, Question.level)

    if level:
        query = query.filter(Question.level == level.upper())

    results = query.all()
    data = []
    for topic, q_level, count in results:
        data.append({
            "topic": topic or "General",
            "level": q_level or "A1",
            "total_questions": count,
        })

    return jsonify({
        "success": True,
        "data": data,
        "total_sets": len(data),
    })


@bp.get("/quizzes/questions")
def api_get_quiz_questions():
    """
    Lấy danh sách câu hỏi trắc nghiệm để làm bài kiểm tra hoặc luyện tập.
    ---
    tags:
      - Quizzes
    parameters:
      - name: topic
        in: query
        type: string
        required: false
        description: Chủ đề trắc nghiệm
      - name: level
        in: query
        type: string
        required: false
        description: Cấp độ CEFR
      - name: limit
        in: query
        type: integer
        required: false
        default: 10
        description: Số lượng câu hỏi (tối đa 50)
      - name: randomize
        in: query
        type: boolean
        required: false
        default: true
        description: Trộn ngẫu nhiên câu hỏi
      - name: include_answers
        in: query
        type: boolean
        required: false
        default: false
        description: Bao gồm đáp án đúng (dành cho chế độ ôn luyện)
    responses:
      200:
        description: Danh sách câu hỏi trắc nghiệm
    """
    topic = request.args.get("topic", "").strip()
    level = request.args.get("level", "").strip()
    randomize = request.args.get("randomize", "true").lower() in ("true", "1", "yes")
    include_answers = request.args.get("include_answers", "false").lower() in ("true", "1", "yes")

    try:
        limit = min(50, max(1, int(request.args.get("limit", 10))))
    except (ValueError, TypeError):
        limit = 10

    query = Question.query
    if topic:
        query = query.filter(Question.topic == topic)
    if level:
        query = query.filter(Question.level == level.upper())

    if randomize:
        all_ids = [row[0] for row in query.with_entities(Question.id).all()]
        sampled_ids = random.sample(all_ids, min(limit, len(all_ids)))
        questions = Question.query.filter(Question.id.in_(sampled_ids)).all() if sampled_ids else []
    else:
        questions = query.order_by(Question.id.asc()).limit(limit).all()

    data = []
    for q in questions:
        item = {
            "id": q.id,
            "question_text": q.question_text,
            "options": {
                "A": q.option_a,
                "B": q.option_b,
                "C": q.option_c,
                "D": q.option_d,
            },
            "level": q.level,
            "topic": q.topic,
        }
        if include_answers:
            item["correct_option"] = q.correct_option
            item["explanation"] = q.explanation
        data.append(item)

    return jsonify({
        "success": True,
        "data": data,
        "count": len(data),
    })


@bp.get("/quizzes/topics")
def api_get_quiz_topics():
    """
    Lấy danh sách các chủ đề trắc nghiệm có sẵn.
    ---
    tags:
      - Quizzes
    responses:
      200:
        description: Danh sách chủ đề
    """
    results = db.session.query(Question.topic).filter(Question.topic.isnot(None)).distinct().all()
    topics = sorted(list({r[0] for r in results if r[0]}))
    return jsonify({
        "success": True,
        "data": topics
    })
