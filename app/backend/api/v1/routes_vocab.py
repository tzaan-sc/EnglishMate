import random
from flask import jsonify, request
from . import bp
from app.extensions import db
from app.backend.learning.models import Vocabulary


@bp.get("/vocabulary")
def api_get_vocabulary():
    """
    Lấy danh sách từ vựng trong từ điển kèm phân trang, tìm kiếm và bộ lọc theo chủ đề/cấp độ.
    ---
    tags:
      - Vocabulary
    parameters:
      - name: search
        in: query
        type: string
        required: false
        description: Tìm kiếm theo từ tiếng Anh hoặc nghĩa tiếng Việt
      - name: topic
        in: query
        type: string
        required: false
        description: Lọc theo chủ đề
      - name: level
        in: query
        type: string
        required: false
        description: Lọc theo cấp độ CEFR (A1, A2, B1, B2, C1, C2)
      - name: part_of_speech
        in: query
        type: string
        required: false
        description: Loại từ (noun, verb, adjective, adverb...)
      - name: page
        in: query
        type: integer
        required: false
        default: 1
      - name: per_page
        in: query
        type: integer
        required: false
        default: 20
    responses:
      200:
        description: Danh sách từ vựng kèm phân trang
    """
    search = request.args.get("search", "").strip()
    topic = request.args.get("topic", "").strip()
    level = request.args.get("level", "").strip()
    pos = request.args.get("part_of_speech", "").strip()

    try:
        page = max(1, int(request.args.get("page", 1)))
    except (ValueError, TypeError):
        page = 1

    try:
        per_page = min(100, max(1, int(request.args.get("per_page", 20))))
    except (ValueError, TypeError):
        per_page = 20

    query = Vocabulary.query

    if search:
        query = query.filter(
            (Vocabulary.word.ilike(f"%{search}%")) |
            (Vocabulary.meaning_vi.ilike(f"%{search}%"))
        )
    if topic:
        query = query.filter(Vocabulary.topic == topic)
    if level:
        query = query.filter(Vocabulary.level == level.upper())
    if pos:
        query = query.filter(Vocabulary.part_of_speech == pos.lower())

    total = query.count()
    items = query.order_by(Vocabulary.word.asc()).offset((page - 1) * per_page).limit(per_page).all()

    data = []
    for v in items:
        data.append({
            "id": v.id,
            "word": v.word,
            "pronunciation": v.pronunciation,
            "part_of_speech": v.part_of_speech,
            "meaning_vi": v.meaning_vi,
            "example_en": v.example_en,
            "example_vi": v.example_vi,
            "topic": v.topic,
            "level": v.level,
            "category": v.category,
            "image_url": v.image_url,
            "collocations": v.collocations,
            "synonyms": v.synonyms,
            "antonyms": v.antonyms,
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


@bp.get("/vocabulary/<int:vocab_id>")
def api_get_vocab_detail(vocab_id):
    """
    Lấy thông tin chi tiết một từ vựng theo ID.
    ---
    tags:
      - Vocabulary
    parameters:
      - name: vocab_id
        in: path
        type: integer
        required: true
        description: ID từ vựng
    responses:
      200:
        description: Chi tiết từ vựng
      404:
        description: Không tìm thấy từ vựng
    """
    v = db.session.get(Vocabulary, vocab_id)
    if not v:
        return jsonify({
            "success": False,
            "error": "Not Found",
            "message": f"Không tìm thấy từ vựng với ID {vocab_id}",
        }), 404

    return jsonify({
        "success": True,
        "data": {
            "id": v.id,
            "word": v.word,
            "pronunciation": v.pronunciation,
            "part_of_speech": v.part_of_speech,
            "meaning_vi": v.meaning_vi,
            "example_en": v.example_en,
            "example_vi": v.example_vi,
            "topic": v.topic,
            "level": v.level,
            "category": v.category,
            "subcategory": v.subcategory,
            "lesson_unit": v.lesson_unit,
            "image_url": v.image_url,
            "collocations": v.collocations,
            "synonyms": v.synonyms,
            "antonyms": v.antonyms,
        }
    })


@bp.get("/vocabulary/topics")
def api_get_vocab_topics():
    """
    Lấy danh sách tất cả các chủ đề từ vựng trong hệ thống.
    ---
    tags:
      - Vocabulary
    responses:
      200:
        description: Danh sách chủ đề
    """
    results = db.session.query(Vocabulary.topic).filter(Vocabulary.topic.isnot(None)).distinct().all()
    topics = sorted(list({r[0] for r in results if r[0]}))
    return jsonify({
        "success": True,
        "data": topics
    })


@bp.get("/vocabulary/random")
def api_get_random_vocabulary():
    """
    Lấy ngẫu nhiên một số từ vựng để luyện tập nhanh hoặc làm bài kiểm tra hàng ngày.
    ---
    tags:
      - Vocabulary
    parameters:
      - name: count
        in: query
        type: integer
        required: false
        default: 5
        description: Số lượng từ ngẫu nhiên cần lấy (tối đa 20)
      - name: level
        in: query
        type: string
        required: false
        description: Cấp độ CEFR
    responses:
      200:
        description: Danh sách từ vựng ngẫu nhiên
    """
    try:
        count = min(20, max(1, int(request.args.get("count", 5))))
    except (ValueError, TypeError):
        count = 5

    level = request.args.get("level", "").strip()

    query = Vocabulary.query
    if level:
        query = query.filter(Vocabulary.level == level.upper())

    total = query.count()
    if total == 0:
        return jsonify({"success": True, "data": []})

    all_ids = [row[0] for row in query.with_entities(Vocabulary.id).all()]
    sampled_ids = random.sample(all_ids, min(count, len(all_ids)))

    items = Vocabulary.query.filter(Vocabulary.id.in_(sampled_ids)).all()
    data = [{
        "id": v.id,
        "word": v.word,
        "pronunciation": v.pronunciation,
        "part_of_speech": v.part_of_speech,
        "meaning_vi": v.meaning_vi,
        "example_en": v.example_en,
        "example_vi": v.example_vi,
        "topic": v.topic,
        "level": v.level,
    } for v in items]

    return jsonify({
        "success": True,
        "data": data,
        "count": len(data),
    })
