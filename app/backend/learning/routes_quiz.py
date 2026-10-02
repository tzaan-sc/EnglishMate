import uuid
import io
import json
import logging
import math
import os
import random
import re
import secrets
from datetime import date, datetime, timedelta, timezone
from difflib import SequenceMatcher

from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

from flask import (
    Blueprint, abort, current_app, flash, jsonify, redirect,
    render_template, request, send_file, session, url_for
)
from flask_login import current_user, login_required
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy import func, or_

from ...extensions import csrf, db
from ..auth.models import record_daily_activity
from .models import (
    Badge, Challenge, FlashcardSet, GrammarErrorLog,
    GrammarExerciseAttempt, GrammarProgress, GrammarRule, GrammarRuleBookmark,
    GrammarTopic, Lesson, LessonBookmark, LessonFavorite, LessonNote,
    LessonProgress, LessonRating, LessonReport, Question, Quiz, QuizAttempt,
    QuizAttemptAnswer, ReadingAnnotation, UserBadge, UserChallenge, Vocabulary,
    VocabularyProgress, WordReport, WritingSubmission
)
from .vocab_catalog import (
    VOCAB_CATEGORIES, get_category_info, get_subcategory_info,
    normalize_category_key, normalize_subcategory_key
)
from . import bp
from .forms import ActionForm, QuizStartForm
from .grammar_checker import check_grammar_and_spelling, evaluate_writing_submission
from .routes_gamification import (
    check_user_badges, get_or_create_user_challenges, update_challenge_progress
)
from .routes_grammar import ensure_initial_grammar_questions


@bp.route("/quiz", methods=["GET", "POST"])
@login_required
def quiz():
    if request.method == "POST" and request.form.get("question_ids"):
        ids = [int(x) for x in request.form["question_ids"].split(",") if x.isdigit()]
        questions = Question.query.filter(Question.id.in_(ids)).all()
        order = {qid: i for i, qid in enumerate(ids)}
        questions.sort(key=lambda q: order[q.id])
        if not questions:
            abort(400)
        score = sum(request.form.get(f"question_{q.id}") == q.correct_option for q in questions)
        attempt = QuizAttempt(user_id=current_user.id, level=request.form.get("level") or "Mixed",
                              topic=request.form.get("topic") or "Mixed", score=score,
                              total_questions=len(questions))
        db.session.add(attempt)
        db.session.flush()
        for q in questions:
            selected = request.form.get(f"question_{q.id}")
            db.session.add(QuizAttemptAnswer(attempt_id=attempt.id, question_id=q.id,
                                             selected_option=selected, is_correct=selected == q.correct_option))
        earned_xp = score * 5 + 10
        current_user.add_xp(earned_xp, reason="Hoàn thành bài kiểm tra Quiz")
        update_challenge_progress(current_user, "quiz", 1)
        check_user_badges(current_user)
        db.session.commit()
        return redirect(url_for("learning.quiz_results", attempt_id=attempt.id))

    return redirect(url_for("learning.quiz_dashboard"))


@bp.get("/quiz/result/<int:attempt_id>")
@login_required
def quiz_result(attempt_id):
    return redirect(url_for("learning.quiz_results", attempt_id=attempt_id))




# QUIZ DASHBOARD ROUTES (Section 4.1)
# ==========================================

def ensure_initial_user_quiz_attempts(user):
    if QuizAttempt.query.filter_by(user_id=user.id).count() > 0:
        return

    sample_attempts = [
        QuizAttempt(user_id=user.id, level="A1", topic="Vocabulary", score=9, total_questions=10, duration_seconds=120, created_at=datetime.utcnow() - timedelta(days=2)),
        QuizAttempt(user_id=user.id, level="A2", topic="Grammar", score=5, total_questions=10, duration_seconds=180, created_at=datetime.utcnow() - timedelta(days=1)),
        QuizAttempt(user_id=user.id, level="B1", topic="TOEIC", score=8, total_questions=10, duration_seconds=210, created_at=datetime.utcnow()),
        QuizAttempt(user_id=user.id, level="B1", topic="Reading", score=4, total_questions=10, duration_seconds=240, created_at=datetime.utcnow()),
    ]
    db.session.add_all(sample_attempts)
    db.session.commit()


def calculate_quiz_dashboard_metrics(user_id):
    attempts = QuizAttempt.query.filter_by(user_id=user_id).order_by(QuizAttempt.created_at.desc()).all()

    total_quizzes_completed = len(attempts)
    total_score = sum(a.score for a in attempts)
    total_questions = sum(a.total_questions for a in attempts)
    total_duration = sum(a.duration_seconds or 0 for a in attempts)

    overall_accuracy_rate = int((total_score / total_questions) * 100) if total_questions > 0 else 0
    avg_time_seconds = int(total_duration / total_quizzes_completed) if total_quizzes_completed > 0 else 0

    dates_with_quiz = sorted({a.created_at.date() for a in attempts if a.created_at}, reverse=True)
    streak = 0
    today = date.today()
    current_check = today

    if dates_with_quiz:
        if dates_with_quiz[0] == today or dates_with_quiz[0] == (today - timedelta(days=1)):
            current_check = dates_with_quiz[0]
            while current_check in dates_with_quiz:
                streak += 1
                current_check -= timedelta(days=1)

    category_map = {}
    for a in attempts:
        cat = a.topic or "General"
        if cat not in category_map:
            category_map[cat] = {"count": 0, "score": 0, "total_q": 0, "duration": 0}
        category_map[cat]["count"] += 1
        category_map[cat]["score"] += a.score
        category_map[cat]["total_q"] += a.total_questions
        category_map[cat]["duration"] += (a.duration_seconds or 0)

    category_stats = []
    weak_categories = []

    for cat, data in category_map.items():
        cat_acc = int((data["score"] / data["total_q"]) * 100) if data["total_q"] > 0 else 0
        cat_item = {
            "name": cat,
            "count": data["count"],
            "score": data["score"],
            "total_q": data["total_q"],
            "accuracy_rate": cat_acc,
            "avg_time": int(data["duration"] / data["count"]) if data["count"] > 0 else 0
        }
        category_stats.append(cat_item)

        if cat_acc < 60:
            weak_categories.append(cat_item)

    category_stats.sort(key=lambda x: x["count"], reverse=True)
    weak_categories.sort(key=lambda x: x["accuracy_rate"])

    return {
        "total_quizzes_completed": total_quizzes_completed,
        "overall_score": total_score,
        "total_questions": total_questions,
        "accuracy_rate": overall_accuracy_rate,
        "avg_time_seconds": avg_time_seconds,
        "quiz_streak": max(streak, 1) if total_quizzes_completed > 0 else 0,
        "category_stats": category_stats,
        "weak_categories": weak_categories,
        "recent_attempts": attempts[:10]
    }


@bp.route("/quizzes/dashboard")
@bp.route("/quizzes")
@login_required
def quiz_dashboard():
    ensure_initial_user_quiz_attempts(current_user)
    metrics = calculate_quiz_dashboard_metrics(current_user.id)

    return render_template(
        "learning/quiz_dashboard.html",
        metrics=metrics,
        form=ActionForm()
    )


# ==========================================
# QUIZ LIST & BROWSE ROUTES (Section 4.2)
# ==========================================

def ensure_initial_quizzes():
    if Quiz.query.count() > 0:
        return

    sample_quizzes = [
        Quiz(
            title="Kiểm Tra Ngữ Pháp Tổng Hợp A1",
            category="Grammar",
            level="A1",
            skill="Grammar",
            difficulty="Easy",
            description="Bài kiểm tra kiến thức ngữ pháp cơ bản mức độ A1: Thì hiện tại đơn, danh từ số nhiều, đại từ nhân xưng.",
            question_count=10,
            duration_minutes=10,
            view_count=1450
        ),
        Quiz(
            title="Từ Vựng Tiếng Anh Giao Tiếp Hàng Ngày A2",
            category="Vocabulary",
            level="A2",
            skill="Vocabulary",
            difficulty="Easy",
            description="Đánh giá vốn từ vựng chủ đề giao tiếp cơ bản: Mua sắm, hỏi đường, đặt đồ ăn và thời tiết.",
            question_count=10,
            duration_minutes=12,
            view_count=980
        ),
        Quiz(
            title="TOEIC Reading Mini Test Part 5 & 6 (B1)",
            category="TOEIC",
            level="B1",
            skill="Reading",
            difficulty="Medium",
            description="Luyện tập câu hỏi điền từ vào câu và đoạn văn chuẩn cấu trúc đề thi TOEIC Reading mới nhất.",
            question_count=15,
            duration_minutes=15,
            view_count=2100
        ),
        Quiz(
            title="Ngữ Pháp Nâng Cao: Mệnh Đề Quan Hệ & Câu Điều Kiện B2",
            category="Grammar",
            level="B2",
            skill="Grammar",
            difficulty="Hard",
            description="Thử thách kiến thức ngữ pháp phức tạp mức B2: Mệnh đề quan hệ rút gọn, câu điều kiện hỗn hợp.",
            question_count=12,
            duration_minutes=15,
            view_count=1890
        ),
        Quiz(
            title="Listening Comprehension Business English C1",
            category="Listening",
            level="C1",
            skill="Listening",
            difficulty="Hard",
            description="Bài kiểm tra kỹ năng nghe hiểu tiếng Anh thương mại nâng cao: Đàm phán, thuyết trình và họp chiến lược.",
            question_count=10,
            duration_minutes=20,
            view_count=760
        )
    ]
    db.session.add_all(sample_quizzes)
    db.session.commit()


@bp.route("/quizzes/list")
@bp.route("/quizzes/browse")
@login_required
def quiz_list():
    ensure_initial_quizzes()

    q = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    level = request.args.get("level", "").strip()
    skill = request.args.get("skill", "").strip()
    difficulty = request.args.get("difficulty", "").strip()
    status = request.args.get("status", "").strip()
    sort = request.args.get("sort", "recent").strip()

    categories = [r[0] for r in db.session.query(Quiz.category).distinct().all()]
    levels = ["A1", "A2", "B1", "B2", "C1", "C2"]
    skills = ["Grammar", "Vocabulary", "Reading", "Listening", "Speaking", "Writing"]
    difficulties = ["Easy", "Medium", "Hard"]

    query = Quiz.query.filter_by(is_active=True)

    if q:
        query = query.filter(Quiz.title.ilike(f"%{q}%") | Quiz.description.ilike(f"%{q}%"))
    if category:
        query = query.filter_by(category=category)
    if level:
        query = query.filter_by(level=level)
    if skill:
        query = query.filter_by(skill=skill)
    if difficulty:
        query = query.filter_by(difficulty=difficulty)

    if sort == "popularity":
        query = query.order_by(Quiz.view_count.desc(), Quiz.id.desc())
    else:
        query = query.order_by(Quiz.created_at.desc(), Quiz.id.desc())

    quizzes_all = query.all()

    user_attempts = QuizAttempt.query.filter_by(user_id=current_user.id).order_by(QuizAttempt.created_at.desc()).all()
    user_attempts_by_topic = {}
    for att in user_attempts:
        if att.topic not in user_attempts_by_topic:
            user_attempts_by_topic[att.topic] = att

    in_progress_quiz_ids = session.get("in_progress_quizzes", [])

    final_quizzes = []
    for quiz in quizzes_all:
        att = user_attempts_by_topic.get(quiz.title) or user_attempts_by_topic.get(quiz.category)
        if att:
            q_status = "completed"
            last_attempt_id = att.id
        elif quiz.id in in_progress_quiz_ids:
            q_status = "in_progress"
            last_attempt_id = None
        else:
            q_status = "new"
            last_attempt_id = None

        if status and q_status != status:
            continue

        final_quizzes.append({
            "model": quiz,
            "status": q_status,
            "last_attempt_id": last_attempt_id
        })

    return render_template(
        "learning/quiz_list.html",
        quizzes=final_quizzes,
        categories=categories,
        levels=levels,
        skills=skills,
        difficulties=difficulties,
        q=q,
        category=category,
        level=level,
        skill=skill,
        difficulty=difficulty,
        status=status,
        sort=sort
    )


@bp.route("/quizzes/<int:quiz_id>/preview")
@login_required
def quiz_detail_preview(quiz_id):
    quiz = db.session.get(Quiz, quiz_id)
    if not quiz:
        return jsonify({"success": False, "message": "Không tìm thấy bài quiz."}), 404

    quiz.view_count = (quiz.view_count or 0) + 1
    db.session.commit()

    return jsonify({
        "success": True,
        "quiz": {
            "id": quiz.id,
            "title": quiz.title,
            "category": quiz.category,
            "level": quiz.level,
            "skill": quiz.skill,
            "difficulty": quiz.difficulty,
            "description": quiz.description,
            "question_count": quiz.question_count,
            "duration_minutes": quiz.duration_minutes,
            "view_count": quiz.view_count
        }
    })


# ==========================================
# QUIZ TAKING ROUTES (Section 4.3)
# ==========================================

@bp.route("/quizzes/<int:quiz_id>/start")
@login_required
def quiz_start_session(quiz_id):
    quiz = db.session.get(Quiz, quiz_id)
    if not quiz:
        flash("Không tìm thấy bài quiz.", "danger")
        return redirect(url_for("learning.quiz_list"))

    ensure_initial_grammar_questions()
    questions = Question.query.filter_by(level=quiz.level).limit(quiz.question_count).all()
    if not questions:
        questions = Question.query.limit(quiz.question_count).all()

    questions_data = []
    for q in questions:
        q_text = getattr(q, 'question_text', getattr(q, 'text', ''))
        questions_data.append({
            "id": q.id,
            "text": q_text,
            "option_a": q.option_a,
            "option_b": q.option_b,
            "option_c": q.option_c,
            "option_d": q.option_d,
            "correct_option": q.correct_option,
            "explanation": q.explanation
        })

    sess_key = f"quiz_session_{quiz.id}"
    session[sess_key] = {
        "quiz_id": quiz.id,
        "title": quiz.title,
        "category": quiz.category,
        "level": quiz.level,
        "skill": quiz.skill,
        "difficulty": quiz.difficulty,
        "duration_minutes": quiz.duration_minutes,
        "duration_seconds": quiz.duration_minutes * 60,
        "questions": questions_data,
        "answers": {},
        "marked_reviews": [],
        "current_idx": 0,
        "start_time": datetime.utcnow().isoformat(),
        "elapsed_seconds": 0,
        "is_paused": False
    }

    in_prog = session.get("in_progress_quizzes", [])
    if quiz.id not in in_prog:
        in_prog.append(quiz.id)
        session["in_progress_quizzes"] = in_prog

    return redirect(url_for("learning.quiz_take", quiz_id=quiz.id))


@bp.route("/quizzes/<int:quiz_id>/take")
@login_required
def quiz_take(quiz_id):
    sess_key = f"quiz_session_{quiz_id}"
    q_sess = session.get(sess_key)

    if not q_sess:
        return redirect(url_for("learning.quiz_start_session", quiz_id=quiz_id))

    current_idx = request.args.get("q_idx", type=int)
    if current_idx is not None and 0 <= current_idx < len(q_sess["questions"]):
        q_sess["current_idx"] = current_idx
        session.modified = True

    current_idx = q_sess.get("current_idx", 0)
    current_question = q_sess["questions"][current_idx] if q_sess["questions"] else None

    answers = q_sess.get("answers", {})
    marked = q_sess.get("marked_reviews", [])
    total_q = len(q_sess["questions"])
    answered_count = len([k for k, v in answers.items() if v])
    unanswered_count = total_q - answered_count
    marked_count = len(marked)

    return render_template(
        "learning/quiz_take.html",
        quiz_session=q_sess,
        quiz_id=quiz_id,
        current_idx=current_idx,
        current_question=current_question,
        total_questions=total_q,
        answered_count=answered_count,
        unanswered_count=unanswered_count,
        marked_count=marked_count,
        answers=answers,
        marked_reviews=marked,
        form=ActionForm()
    )


@bp.post("/quizzes/<int:quiz_id>/answer")
@login_required
def quiz_save_answer(quiz_id):
    sess_key = f"quiz_session_{quiz_id}"
    q_sess = session.get(sess_key)
    if not q_sess:
        return jsonify({"success": False, "message": "Phiên bài quiz đã hết hạn."}), 404

    data = request.get_json() or request.form
    q_idx = int(data.get("q_idx", q_sess.get("current_idx", 0)))
    option = data.get("option")
    toggle_mark = data.get("toggle_mark")
    elapsed = data.get("elapsed_seconds")

    if elapsed is not None:
        q_sess["elapsed_seconds"] = int(elapsed)

    if option is not None:
        q_sess["answers"][str(q_idx)] = option

    if toggle_mark:
        marked = q_sess.get("marked_reviews", [])
        if q_idx in marked:
            marked.remove(q_idx)
        else:
            marked.append(q_idx)
        q_sess["marked_reviews"] = marked

    q_sess["current_idx"] = q_idx
    session.modified = True

    if request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({
            "success": True,
            "q_idx": q_idx,
            "answers": q_sess["answers"],
            "marked_reviews": q_sess["marked_reviews"],
            "answered_count": len([k for k, v in q_sess["answers"].items() if v]),
            "marked_count": len(q_sess["marked_reviews"])
        })

    return redirect(url_for("learning.quiz_take", quiz_id=quiz_id, q_idx=q_idx))


@bp.post("/quizzes/<int:quiz_id>/pause")
@login_required
def quiz_pause_session(quiz_id):
    sess_key = f"quiz_session_{quiz_id}"
    q_sess = session.get(sess_key)
    if not q_sess:
        return jsonify({"success": False, "message": "Không tìm thấy phiên bài quiz."}), 404

    data = request.get_json() or request.form
    is_paused = data.get("is_paused")
    elapsed = data.get("elapsed_seconds")

    if elapsed is not None:
        q_sess["elapsed_seconds"] = int(elapsed)

    if is_paused is not None:
        q_sess["is_paused"] = bool(is_paused)
    else:
        q_sess["is_paused"] = not q_sess.get("is_paused", False)

    session.modified = True
    return jsonify({"success": True, "is_paused": q_sess["is_paused"], "elapsed_seconds": q_sess["elapsed_seconds"]})


@bp.post("/quizzes/<int:quiz_id>/submit")
@login_required
def quiz_submit_session(quiz_id):
    sess_key = f"quiz_session_{quiz_id}"
    q_sess = session.get(sess_key)

    if not q_sess:
        flash("Phiên bài quiz không khả dụng hoặc đã nộp.", "warning")
        return redirect(url_for("learning.quiz_list"))

    questions = q_sess.get("questions", [])
    answers = q_sess.get("answers", {})
    elapsed = request.form.get("elapsed_seconds") or q_sess.get("elapsed_seconds", 0)
    duration_sec = int(elapsed) if elapsed else 0

    score = 0
    total_q = len(questions)

    attempt = QuizAttempt(
        user_id=current_user.id,
        level=q_sess.get("level", "A1"),
        topic=q_sess.get("title", "General"),
        score=0,
        total_questions=total_q,
        duration_seconds=duration_sec,
        created_at=datetime.utcnow()
    )
    db.session.add(attempt)
    db.session.flush()

    for idx, q_item in enumerate(questions):
        user_ans = answers.get(str(idx), "")
        is_corr = (user_ans.upper() == q_item["correct_option"].upper()) if user_ans else False
        if is_corr:
            score += 1

        db.session.add(QuizAttemptAnswer(
            attempt_id=attempt.id,
            question_id=q_item["id"],
            selected_option=user_ans,
            is_correct=is_corr
        ))

    attempt.score = score
    record_daily_activity(current_user)
    db.session.commit()

    in_prog = session.get("in_progress_quizzes", [])
    if quiz_id in in_prog:
        in_prog.remove(quiz_id)
        session["in_progress_quizzes"] = in_prog
    session.pop(sess_key, None)

    flash("Chúc mừng bạn đã hoàn thành và nộp bài Quiz!", "success")
    return redirect(url_for("learning.quiz_results", attempt_id=attempt.id))


# ==========================================
# QUIZ RESULTS ROUTES (Section 4.4)
# ==========================================

@bp.route("/quizzes/results/<int:attempt_id>")
@bp.route("/quizzes/summary/<int:attempt_id>")
@login_required
def quiz_results(attempt_id):
    attempt = db.session.get(QuizAttempt, attempt_id)
    if not attempt or attempt.user_id != current_user.id:
        flash("Không tìm thấy kết quả lượt làm bài quiz.", "danger")
        return redirect(url_for("learning.quiz_dashboard"))

    answers = attempt.answers or []
    total_questions = attempt.total_questions or len(answers)
    score = attempt.score or 0

    correct_count = sum(1 for a in answers if a.is_correct)
    incorrect_count = sum(1 for a in answers if not a.is_correct and a.selected_option)
    unanswered_count = max(0, total_questions - (correct_count + incorrect_count))

    accuracy_rate = int((score / total_questions) * 100) if total_questions > 0 else 0
    duration_sec = attempt.duration_seconds or 0
    avg_time_per_q = int(duration_sec / total_questions) if total_questions > 0 else 0

    if accuracy_rate >= 90:
        grade = {"text": "Xuất sắc 🌟", "color": "bg-success"}
    elif accuracy_rate >= 80:
        grade = {"text": "Giỏi 🎯", "color": "bg-primary"}
    elif accuracy_rate >= 60:
        grade = {"text": "Khá 👍", "color": "bg-warning text-dark"}
    else:
        grade = {"text": "Cần cố gắng 💡", "color": "bg-danger"}

    # Automatically add incorrect answers to error log
    for ans in answers:
        if not ans.is_correct:
            existing_log = GrammarErrorLog.query.filter_by(
                user_id=current_user.id,
                question_id=ans.question_id,
                attempt_id=attempt.id
            ).first()
            if not existing_log:
                db.session.add(GrammarErrorLog(
                    user_id=current_user.id,
                    question_id=ans.question_id,
                    attempt_id=attempt.id,
                    user_answer=ans.selected_option or "",
                    correct_answer=ans.question.correct_option if ans.question else "A",
                    is_resolved=False
                ))
    db.session.commit()

    matching_quiz = Quiz.query.filter_by(title=attempt.topic).first()

    return render_template(
        "learning/quiz_results.html",
        attempt=attempt,
        answers=answers,
        total_questions=total_questions,
        correct_count=correct_count,
        incorrect_count=incorrect_count,
        unanswered_count=unanswered_count,
        accuracy_rate=accuracy_rate,
        duration_sec=duration_sec,
        avg_time_per_q=avg_time_per_q,
        grade=grade,
        matching_quiz=matching_quiz,
        form=ActionForm()
    )


@bp.route("/quizzes/results/<int:attempt_id>/pdf")
@login_required
def quiz_results_pdf(attempt_id):
    attempt = db.session.get(QuizAttempt, attempt_id)
    if not attempt or attempt.user_id != current_user.id:
        flash("Không tìm thấy kết quả lượt làm bài.", "danger")
        return redirect(url_for("learning.quiz_dashboard"))

    answers = attempt.answers or []
    accuracy_rate = int((attempt.score / attempt.total_questions) * 100) if attempt.total_questions > 0 else 0

    return render_template(
        "learning/quiz_results_pdf.html",
        attempt=attempt,
        answers=answers,
        accuracy_rate=accuracy_rate
    )


# ==============================================================================
# GAMIFICATION ENGINE & ROUTES (SECTION 5.2)
