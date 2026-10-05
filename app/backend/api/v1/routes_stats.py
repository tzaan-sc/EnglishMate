from flask import jsonify, request
from flask_login import current_user
from . import bp
from app.extensions import db
from app.backend.learning.models import Lesson, Vocabulary, Question, LessonProgress, QuizAttempt
from app.backend.auth.models import User


@bp.get("/stats")
def api_get_platform_stats():
    """
    Lấy thông tin thống kê tổng quan về nội dung học tập trên nền tảng EnglishMate.
    ---
    tags:
      - Statistics
    responses:
      200:
        description: Thống kê số lượng bài học, từ vựng, câu hỏi trắc nghiệm
    """
    total_lessons = Lesson.query.count()
    total_vocab = Vocabulary.query.count()
    total_questions = Question.query.count()
    total_users = User.query.count()

    # Topic breakdown
    vocab_topics_count = db.session.query(Vocabulary.topic).filter(Vocabulary.topic.isnot(None)).distinct().count()

    return jsonify({
        "success": True,
        "data": {
            "total_lessons": total_lessons,
            "total_vocabulary": total_vocab,
            "total_questions": total_questions,
            "total_users": total_users,
            "total_vocabulary_topics": vocab_topics_count,
        }
    })


@bp.get("/user/stats")
def api_get_user_stats():
    """
    Lấy thông tin tiến độ học tập và chỉ số của người dùng hiện tại (nếu đã đăng nhập).
    ---
    tags:
      - Statistics
    responses:
      200:
        description: Thông tin tiến độ người dùng
      401:
        description: Chưa đăng nhập
    """
    if not current_user.is_authenticated:
        return jsonify({
            "success": False,
            "error": "Unauthorized",
            "message": "Vui lòng đăng nhập để xem tiến độ học tập cá nhân.",
        }), 401

    completed_lessons = LessonProgress.query.filter_by(user_id=current_user.id).count()
    total_quizzes_taken = QuizAttempt.query.filter_by(user_id=current_user.id).count()
    
    # Calculate average quiz score
    avg_score_res = db.session.query(db.func.avg(QuizAttempt.score)).filter(QuizAttempt.user_id == current_user.id).scalar()
    avg_score = round(float(avg_score_res), 1) if avg_score_res is not None else 0.0

    return jsonify({
        "success": True,
        "data": {
            "user_id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "role": current_user.role,
            "current_streak": current_user.get_current_streak(),
            "completed_lessons": completed_lessons,
            "total_quizzes_taken": total_quizzes_taken,
            "average_quiz_score": avg_score,
            "target_level": getattr(current_user, "target_level", "A2"),
            "daily_goal_minutes": getattr(current_user, "daily_goal_minutes", 15),
        }
    })
