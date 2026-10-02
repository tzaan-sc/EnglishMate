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


@bp.get("/games")
@bp.get("/games/lobby")
@login_required
def game_lobby():
    from .models import FlashcardSet, GameSession, FlashcardProgress
    sets = FlashcardSet.query.filter_by(user_id=current_user.id).order_by(FlashcardSet.created_at.desc()).all()
    history = GameSession.query.filter_by(user_id=current_user.id).order_by(GameSession.created_at.desc()).limit(10).all()
    
    # Calculate SRS due cards
    now_time = datetime.utcnow()
    srs_count = FlashcardProgress.query.filter(
        FlashcardProgress.user_id == current_user.id,
        FlashcardProgress.next_review_at <= now_time
    ).count()
    
    return render_template("learning/game_lobby.html", sets=sets, history=history, srs_count=srs_count)

@bp.post("/games/calculate-stats")
@login_required
def game_calculate_stats():
    data = request.json
    set_id = data.get("set_id")
    status = data.get("status")
    
    from .models import FlashcardItem, FlashcardSet, FlashcardProgress
    query = db.session.query(FlashcardItem).join(FlashcardSet).filter(FlashcardSet.user_id == current_user.id)
    
    if set_id and set_id != "all":
        query = query.filter(FlashcardSet.id == int(set_id))
        
    items = query.all()
    total_count = len(items)
    
    progress_records = {p.item_id: p for p in FlashcardProgress.query.filter_by(user_id=current_user.id).all()}
    
    learned_count = 0
    available_items = []
    now_dt = datetime.utcnow()
    
    for item in items:
        p = progress_records.get(item.id)
        is_known = p.is_known if p else False
        if is_known:
            learned_count += 1
            
        if status == "learning" and is_known:
            continue
        if status == "known" and not is_known:
            continue
        if status == "srs_due":
            is_due = (not p) or (p.next_review_at and p.next_review_at <= now_dt)
            if not is_due:
                continue
        # (Chưa implement Đánh dấu sao)
        
        available_items.append(item)
        
    return {
        "available_count": len(available_items),
        "total_count": total_count,
        "learned_count": learned_count
    }

@bp.post("/games/start")
@login_required
def game_start():
    set_id = request.form.get("set_id")
    status = request.form.get("status")
    sort_by = request.form.get("sort_by")
    quantity = request.form.get("quantity")
    game_type = request.form.get("game_type")
    
    from .models import FlashcardItem, FlashcardSet, FlashcardProgress
    query = db.session.query(FlashcardItem).join(FlashcardSet).filter(FlashcardSet.user_id == current_user.id)
    
    if set_id and set_id != "all":
        query = query.filter(FlashcardSet.id == int(set_id))
        
    items = query.all()
    progress_records = {p.item_id: p for p in FlashcardProgress.query.filter_by(user_id=current_user.id).all()}
    
    filtered = []
    now_dt = datetime.utcnow()
    for item in items:
        p = progress_records.get(item.id)
        is_known = p.is_known if p else False
        if status == "learning" and is_known: continue
        if status == "known" and not is_known: continue
        if status == "srs_due":
            is_due = (not p) or (p.next_review_at and p.next_review_at <= now_dt)
            if not is_due: continue
        filtered.append(item)
        
    if sort_by == "random":
        random.shuffle(filtered)
    elif sort_by == "az":
        filtered.sort(key=lambda x: x.term.lower())
    elif sort_by == "newest":
        filtered.sort(key=lambda x: x.id, reverse=True)
    elif sort_by == "oldest":
        filtered.sort(key=lambda x: x.id)
        
    if quantity != "all" and quantity.isdigit():
        filtered = filtered[:int(quantity)]
        
    if not filtered:
        flash("Không có thẻ nào thỏa mãn điều kiện lọc.", "warning")
        return redirect(url_for("learning.game_lobby"))
        
    session_id = str(uuid.uuid4())
    from flask import session
    session[f"game_{session_id}"] = {
        "item_ids": [i.id for i in filtered],
        "game_type": game_type
    }
    
    return redirect(url_for("learning.game_play", session_id=session_id))

@bp.get("/games/play/<session_id>")
@login_required
def game_play(session_id):
    from flask import session
    game_data = session.get(f"game_{session_id}")
    if not game_data:
        flash("Phiên chơi không hợp lệ hoặc đã hết hạn.", "danger")
        return redirect(url_for("learning.game_lobby"))
        
    return render_template("learning/game_play.html", session_id=session_id, game_type=game_data["game_type"])

@bp.get("/games/api/data/<session_id>")
@login_required
def game_api_data(session_id):
    from flask import session
    game_data = session.get(f"game_{session_id}")
    if not game_data:
        return {"error": "Invalid session"}, 400
        
    from .models import FlashcardItem
    items = FlashcardItem.query.filter(FlashcardItem.id.in_(game_data["item_ids"])).all()
    # Sort items based on the original list order to preserve random/sort options
    items_dict = {item.id: item for item in items}
    sorted_items = [items_dict[item_id] for item_id in game_data["item_ids"] if item_id in items_dict]
    
    all_terms = [i.term for i in items]
    all_defs = [i.definition for i in items]
    
    data = []
    for item in sorted_items:
        # Generate random distractors for quiz
        distractors = []
        if len(all_defs) >= 4:
            pool = [d for d in all_defs if d != item.definition]
            distractors = random.sample(pool, min(3, len(pool)))
            
        data.append({
            "id": item.id,
            "term": item.term,
            "definition": item.definition,
            "image_url": item.image_url,
            "distractors": distractors
        })

    grammar_items = []
    if game_data.get("game_type") == "GRAMMAR_RACE":
        from .models import Question
        q_pool = Question.query.all()
        if q_pool:
            sampled_q = random.sample(q_pool, min(len(q_pool), len(sorted_items) if sorted_items else 10))
            for q in sampled_q:
                correct_text = getattr(q, f"option_{q.correct_option.lower()}", q.option_a)
                grammar_items.append({
                    "id": q.id,
                    "prompt": q.question_text,
                    "options": [q.option_a, q.option_b, q.option_c, q.option_d],
                    "correct": correct_text,
                    "explanation": q.explanation or ""
                })

    return {"status": "ok", "game_type": game_data["game_type"], "items": data, "grammar_items": grammar_items}

@bp.post("/games/submit")
@login_required
def game_submit():
    data = request.json
    from .models import GameSession
    
    gs = GameSession(
        user_id=current_user.id,
        session_id=data.get("session_id"),
        game_type=data.get("game_type"),
        total_questions=data.get("total_questions", 0),
        correct_answers=data.get("correct_answers", 0),
        accuracy_rate=data.get("accuracy_rate", 0.0),
        duration_seconds=data.get("duration_seconds", 0)
    )
    db.session.add(gs)
    current_user.add_xp(25, reason=f"Chơi game {gs.game_type}")
    update_challenge_progress(current_user, "game", 1)
    check_user_badges(current_user)
    db.session.commit()
    
    # Optional: Clear session data
    from flask import session
    session_key = f"game_{data.get('session_id')}"
    if session_key in session:
        session.pop(session_key)
        
    return {"status": "ok"}


# ==========================================
# VOCABULARY REVIEW (SRS) ROUTES
# ==========================================

