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


@bp.get("/vocabulary")
@login_required
def vocabulary():
    active_tab = request.args.get("tab", "all").strip().lower()
    search = request.args.get("q", "").strip()
    selected_cat = request.args.get("cat", "").strip().lower()
    selected_subcat = request.args.get("subcat", "").strip().lower()
    level = request.args.get("level", "").strip()
    topic = request.args.get("topic", "").strip()

    # User progress mapping
    all_progress = VocabularyProgress.query.filter_by(user_id=current_user.id).all()
    progress_map = {p.vocabulary_id: p for p in all_progress}
    learned_ids = {p.vocabulary_id for p in all_progress if p.learned_count > 0 or p.review_count > 0}

    # Global vocabulary metrics
    total_vocab_count = Vocabulary.query.count()
    review_vocab_count = len(learned_ids)
    overall_progress_pct = round((review_vocab_count / total_vocab_count * 100)) if total_vocab_count > 0 else 0

    # Daily Goal & SRS Due
    today_date = date.today()
    today_learned_count = sum(1 for p in all_progress if p.learned_count > 0 and p.last_reviewed_at and p.last_reviewed_at.date() == today_date)
    today_reviewed_count = sum(1 for p in all_progress if p.review_count > 0 and p.last_reviewed_at and p.last_reviewed_at.date() == today_date)
    daily_goal = getattr(current_user, "daily_vocab_goal", 20) or 20
    daily_goal_pct = min(100, round(((today_learned_count + today_reviewed_count) / daily_goal) * 100)) if daily_goal > 0 else 0

    now_dt = datetime.utcnow()
    due_words_count = VocabularyProgress.query.filter(
        VocabularyProgress.user_id == current_user.id,
        (VocabularyProgress.learned_count > 0) | (VocabularyProgress.review_count > 0),
        (VocabularyProgress.next_review_at <= now_dt) | (VocabularyProgress.next_review_at.is_(None))
    ).count()

    # Fetch all vocab IDs and subcategories for quick calculation
    all_vocab_records = db.session.query(
        Vocabulary.id, Vocabulary.category, Vocabulary.subcategory, Vocabulary.lesson_unit, Vocabulary.topic, Vocabulary.level
    ).all()

    # Build Course Catalog with dynamic stats
    catalog = {}
    for cat_key, cat_data in VOCAB_CATEGORIES.items():
        cat_courses = []
        cat_total_words = 0
        cat_learned_words = 0

        for subcat_key, subcat_data in cat_data["subcategories"].items():
            # Find matching words
            matched_words = [
                v for v in all_vocab_records
                if (v.category and v.category.lower() == cat_key and v.subcategory and v.subcategory.lower() == subcat_key)
                or (cat_key == "cefr" and v.category and v.category.lower() == "cefr" and v.level and v.level.lower() == subcat_key)
            ]
            w_total = len(matched_words)
            w_learned = sum(1 for v in matched_words if v.id in learned_ids)
            w_pct = round((w_learned / w_total * 100)) if w_total > 0 else 0
            
            # Distinct units count
            units_set = {v.lesson_unit or v.topic for v in matched_words if v.lesson_unit or v.topic}
            units_count = len(units_set) if units_set else (1 if w_total > 0 else 0)

            cat_total_words += w_total
            cat_learned_words += w_learned

            cat_courses.append({
                "key": subcat_key,
                "title": subcat_data["title"],
                "level": subcat_data["level"],
                "icon": subcat_data["icon"],
                "color": subcat_data["color"],
                "description": subcat_data["description"],
                "target": subcat_data.get("target", ""),
                "total_words": w_total,
                "learned_words": w_learned,
                "progress_pct": w_pct,
                "units_count": units_count,
            })

        cat_pct = round((cat_learned_words / cat_total_words * 100)) if cat_total_words > 0 else 0
        catalog[cat_key] = {
            "key": cat_key,
            "title": cat_data["title"],
            "subtitle": cat_data["subtitle"],
            "badge": cat_data["badge"],
            "icon": cat_data["icon"],
            "color": cat_data["color"],
            "gradient": cat_data["gradient"],
            "description": cat_data["description"],
            "courses": cat_courses,
            "total_words": cat_total_words,
            "learned_words": cat_learned_words,
            "progress_pct": cat_pct,
        }

    # Query for filtered word list if user is searching / filtering
    query = Vocabulary.query
    has_filter = bool(search or selected_cat or selected_subcat or level or topic)
    if search:
        query = query.filter((Vocabulary.word.ilike(f"%{search}%")) | (Vocabulary.meaning_vi.ilike(f"%{search}%")))
    if selected_cat:
        query = query.filter(Vocabulary.category.ilike(selected_cat))
    if selected_subcat:
        query = query.filter(Vocabulary.subcategory.ilike(selected_subcat))
    if level:
        query = query.filter_by(level=level)
    if topic:
        query = query.filter_by(topic=topic)

    words_list = query.order_by(Vocabulary.word).limit(100).all() if has_filter else []

    # Flashcard sets query (personal and public sets)
    from .models import FlashcardSet
    flashcard_sets = FlashcardSet.query.filter(
        (FlashcardSet.user_id == current_user.id) | (FlashcardSet.is_public == True)
    ).order_by(FlashcardSet.created_at.desc()).all()
    my_sets_count = sum(1 for s in flashcard_sets if s.user_id == current_user.id)
    community_sets_count = sum(1 for s in flashcard_sets if s.user_id != current_user.id and s.is_public)

    return render_template(
        "learning/vocabulary.html",
        catalog=catalog,
        active_tab=active_tab,
        search=search,
        selected_cat=selected_cat,
        selected_subcat=selected_subcat,
        level=level,
        topic=topic,
        has_filter=has_filter,
        words=words_list,
        learned=learned_ids,
        form=ActionForm(),
        total_vocab_count=total_vocab_count,
        review_vocab_count=review_vocab_count,
        due_words_count=due_words_count,
        overall_progress_pct=overall_progress_pct,
        today_learned_count=today_learned_count,
        today_reviewed_count=today_reviewed_count,
        daily_goal=daily_goal,
        daily_goal_pct=daily_goal_pct,
        flashcard_sets=flashcard_sets,
        my_sets_count=my_sets_count,
        community_sets_count=community_sets_count,
    )


@bp.get("/vocabulary/courses/<cat_key>/<subcat_key>")
@login_required
def vocab_course_detail(cat_key, subcat_key):
    cat_info = get_category_info(cat_key)
    subcat_info = get_subcategory_info(cat_key, subcat_key)

    if not cat_info or not subcat_info:
        flash("Khóa học từ vựng không tồn tại hoặc đã được cập nhật.", "warning")
        return redirect(url_for("learning.vocabulary"))

    unit_filter = request.args.get("unit", "").strip()
    search = request.args.get("q", "").strip()

    # Query all words belonging to this course
    all_course_words = Vocabulary.query.filter(
        (Vocabulary.category.ilike(cat_key) & Vocabulary.subcategory.ilike(subcat_key))
        | (Vocabulary.category.ilike("cefr") & Vocabulary.level.ilike(subcat_key) if cat_key == "cefr" else False)
    ).order_by(Vocabulary.id).all()

    # If course words are empty in DB, fallback to words matching level or general pool
    if not all_course_words:
        target_level = subcat_info.get("level", "B1")
        all_course_words = Vocabulary.query.filter_by(level=target_level).order_by(Vocabulary.id).all()
        if not all_course_words:
            all_course_words = Vocabulary.query.order_by(Vocabulary.id).limit(60).all()

    # User progress
    all_progress = VocabularyProgress.query.filter_by(user_id=current_user.id).all()
    progress_map = {p.vocabulary_id: p for p in all_progress}
    learned_ids = {p.vocabulary_id for p in all_progress if p.learned_count > 0 or p.review_count > 0}
    favorite_ids = {p.vocabulary_id for p in all_progress if p.is_favorite}

    # Group words into Lesson Units of ~12 words (chunk size = 12)
    TOEIC_DEFAULT_UNITS = [
        ("Hợp Đồng", "ph-file-text", "#10b981"),
        ("Thị Trường", "ph-chart-line-up", "#3b82f6"),
        ("Sự Bảo Hành", "ph-shield-check", "#f59e0b"),
        ("Kế Hoạch Kinh Doanh", "ph-briefcase", "#8b5cf6"),
        ("Hội Nghị", "ph-users-three", "#ec4899"),
        ("Máy Vi Tính", "ph-desktop", "#06b6d4"),
        ("Công Nghệ Cho Công Sở", "ph-cpu", "#10b981"),
        ("Các Quy Trình Trong Công Sở", "ph-arrows-split", "#6366f1"),
        ("Điện Tử", "ph-lightning", "#f97316"),
        ("Thư Tín", "ph-envelope-simple", "#e11d48"),
        ("Quảng Cáo Việc Làm & Tuyển Dụng", "ph-megaphone", "#0d9488"),
        ("Ứng Tuyển và Phỏng Vấn", "ph-user-focus", "#4f46e5"),
        ("Tuyển Dụng và Đào Tạo", "ph-graduation-cap", "#d97706"),
        ("Lương và Các Chế Độ Đãi Ngộ", "ph-currency-circle-dollar", "#059669"),
        ("Thăng Chức, Lương Hưu và Thưởng", "ph-trophy", "#e11d48")
    ]

    CHUNK_SIZE = 12
    units = []
    
    # Check if words already have distinct lesson_unit assigned
    has_explicit_units = any(w.lesson_unit for w in all_course_words)
    
    # Helper to check if a word is due for review safely
    now_utc = datetime.now(timezone.utc)
    def check_is_due(w_id):
        p = progress_map.get(w_id)
        if not p or not p.next_review_at:
            return False
        dt = p.next_review_at
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt <= now_utc

    if has_explicit_units:
        units_dict = {}
        for w in all_course_words:
            u_name = w.lesson_unit or "Tổng quát"
            if u_name not in units_dict:
                units_dict[u_name] = []
            units_dict[u_name].append(w)
        
        for i, (u_name, w_list) in enumerate(units_dict.items()):
            u_learned = sum(1 for w in w_list if w.id in learned_ids)
            u_total = len(w_list)
            u_due = sum(1 for w in w_list if w.id in learned_ids and check_is_due(w.id))
            u_pct = round((u_learned / u_total * 100)) if u_total > 0 else 0
            u_meta = TOEIC_DEFAULT_UNITS[i % len(TOEIC_DEFAULT_UNITS)]
            units.append({
                "id": str(i + 1),
                "name": u_name,
                "icon": u_meta[1],
                "color": u_meta[2],
                "total": u_total,
                "learned": u_learned,
                "due_count": u_due,
                "pct": u_pct,
                "words": w_list
            })
    else:
        for i in range(0, len(all_course_words), CHUNK_SIZE):
            chunk_words = all_course_words[i:i + CHUNK_SIZE]
            u_index = i // CHUNK_SIZE
            u_meta = TOEIC_DEFAULT_UNITS[u_index % len(TOEIC_DEFAULT_UNITS)]
            u_name = chunk_words[0].topic if chunk_words and chunk_words[0].topic else u_meta[0]
            if "toeic" in cat_key.lower():
                u_name = u_meta[0]
            
            u_learned = sum(1 for w in chunk_words if w.id in learned_ids)
            u_total = len(chunk_words)
            u_due = sum(1 for w in chunk_words if w.id in learned_ids and check_is_due(w.id))
            u_pct = round((u_learned / u_total * 100)) if u_total > 0 else 0
            units.append({
                "id": str(u_index + 1),
                "name": u_name,
                "icon": u_meta[1],
                "color": u_meta[2],
                "total": u_total,
                "learned": u_learned,
                "due_count": u_due,
                "pct": u_pct,
                "words": chunk_words
            })

    selected_unit = None
    if unit_filter:
        selected_unit = next((u for u in units if u["id"] == unit_filter or u["name"] == unit_filter), None)
        words_list = selected_unit["words"] if selected_unit else all_course_words
    else:
        words_list = all_course_words

    if search:
        words_list = [w for w in words_list if search.lower() in w.word.lower() or search.lower() in w.meaning_vi.lower()]

    course_total_words = len(all_course_words)
    course_learned_words = sum(1 for w in all_course_words if w.id in learned_ids)
    total_due_count = sum(u["due_count"] for u in units)
    course_progress_pct = round((course_learned_words / course_total_words * 100)) if course_total_words > 0 else 0

    return render_template(
        "learning/vocab_course_detail.html",
        category=cat_info,
        subcategory=subcat_info,
        cat_key=cat_key,
        subcat_key=subcat_key,
        words=words_list,
        units=units,
        unit_filter=unit_filter,
        selected_unit=selected_unit,
        search=search,
        learned_ids=learned_ids,
        favorite_ids=favorite_ids,
        course_total_words=course_total_words,
        course_learned_words=course_learned_words,
        total_due_count=total_due_count,
        course_progress_pct=course_progress_pct,
        form=ActionForm(),
    )


@bp.post("/vocabulary/set-goal")
@login_required
def set_vocab_goal():
    goal = request.form.get("goal")
    if goal and goal.isdigit() and int(goal) in (20, 30, 40):
        current_user.daily_vocab_goal = int(goal)
        db.session.commit()
        flash(f"Đã cập nhật mục tiêu học từ vựng hàng ngày thành {goal} từ/ngày.", "success")
    else:
        flash("Mục tiêu từ vựng không hợp lệ (Vui lòng chọn 20, 30 hoặc 40 từ).", "danger")
    return redirect(request.referrer or url_for("learning.vocabulary"))


@bp.post("/vocabulary/<int:word_id>/learn")
@login_required
def learn_word(word_id):
    word = db.get_or_404(Vocabulary, word_id)
    form = ActionForm()
    if not form.validate_on_submit():
        abort(400)
    progress = VocabularyProgress.query.filter_by(user_id=current_user.id, vocabulary_id=word.id).first()
    if not progress:
        progress = VocabularyProgress(user_id=current_user.id, vocabulary_id=word.id, learned_count=0, review_count=0)
        db.session.add(progress)
    progress.learned_count = (progress.learned_count or 0) + 1
    progress.last_reviewed_at = func.now()
    db.session.commit()
    flash(f"Đã thêm “{word.word}” vào từ đã học.", "success")
    return redirect(request.referrer or url_for("learning.vocabulary"))


@bp.post("/vocabulary/<int:word_id>/toggle-learned")
@login_required
@csrf.exempt
def toggle_word_learned(word_id):
    word = db.get_or_404(Vocabulary, word_id)
    progress = VocabularyProgress.query.filter_by(user_id=current_user.id, vocabulary_id=word.id).first()
    if not progress:
        progress = VocabularyProgress(user_id=current_user.id, vocabulary_id=word.id, learned_count=0, review_count=0, srs_level=1)
        db.session.add(progress)
    
    is_currently_learned = (progress.learned_count > 0 or progress.review_count > 0)
    if is_currently_learned:
        progress.learned_count = 0
        progress.review_count = 0
        new_status = False
    else:
        progress.learned_count = (progress.learned_count or 0) + 1
        progress.last_reviewed_at = func.now()
        new_status = True

    db.session.commit()
    return jsonify({
        "success": True,
        "word_id": word.id,
        "is_learned": new_status
    })


@bp.post("/vocabulary/<int:word_id>/unlearn")
@login_required
def unlearn_word(word_id):
    word = db.get_or_404(Vocabulary, word_id)
    form = ActionForm()
    if not form.validate_on_submit():
        abort(400)
    progress = VocabularyProgress.query.filter_by(user_id=current_user.id, vocabulary_id=word.id).first()
    if progress:
        progress.learned_count = 0
        progress.review_count = 0
        db.session.commit()
    flash(f"Đã đặt lại “{word.word}” thành Chưa học.", "info")
    return redirect(request.referrer or url_for("learning.vocabulary"))


@bp.post("/vocabulary/courses/<cat_key>/<subcat_key>/reset-unit")
@login_required
def reset_unit_vocab(cat_key, subcat_key):
    form = ActionForm()
    if not form.validate_on_submit():
        abort(400)
    unit_id = request.form.get("unit_id")
    if not unit_id:
        abort(400)

    all_course_words = Vocabulary.query.filter(
        func.lower(Vocabulary.topic).ilike(f"%{subcat_key.replace('_', ' ')}%")
        | func.lower(Vocabulary.topic).ilike(f"%{cat_key}%")
    ).order_by(Vocabulary.id.asc()).all()

    if not all_course_words:
        all_course_words = Vocabulary.query.order_by(Vocabulary.id.asc()).limit(120).all()

    CHUNK_SIZE = 12
    target_words = []
    if "toeic" in cat_key.lower() and "600" in subcat_key.lower():
        units_dict = {}
        for w in all_course_words:
            u_name = w.topic if w.topic else "General"
            if u_name not in units_dict:
                units_dict[u_name] = []
            units_dict[u_name].append(w)
        
        for i, (u_name, w_list) in enumerate(units_dict.items()):
            if str(i + 1) == str(unit_id) or u_name == str(unit_id):
                target_words = w_list
                break
    else:
        try:
            u_idx = int(unit_id) - 1
            target_words = all_course_words[u_idx * CHUNK_SIZE : (u_idx + 1) * CHUNK_SIZE]
        except Exception:
            target_words = []

    if target_words:
        w_ids = [w.id for w in target_words]
        progs = VocabularyProgress.query.filter(
            VocabularyProgress.user_id == current_user.id,
            VocabularyProgress.vocabulary_id.in_(w_ids)
        ).all()
        for p in progs:
            p.learned_count = 0
            p.review_count = 0
        db.session.commit()
        flash("Đã đặt lại tất cả từ vựng trong bài học về trạng thái Chưa học.", "success")
    else:
        flash("Không tìm thấy từ vựng trong bài học này để đặt lại.", "warning")

    return redirect(request.referrer or url_for("learning.vocab_course_detail", cat_key=cat_key, subcat_key=subcat_key, unit=unit_id))


@bp.get("/vocabulary/study")
@login_required
def study_vocabulary():
    cat = request.args.get("cat", "").strip()
    subcat = request.args.get("subcat", "").strip()
    unit = request.args.get("unit", "").strip()
    level = request.args.get("level", "").strip()
    topic = request.args.get("topic", "").strip()
    
    try:
        index = int(request.args.get("index", 0))
    except ValueError:
        index = 0

    autoplay = request.args.get("autoplay", "0") == "1"
    show_meaning = request.args.get("show_meaning", "1") == "1"
    mode = request.args.get("mode", "study")

    words = []
    unit_title = ""
    course_title = ""

    if cat and subcat:
        subcat_info = get_subcategory_info(cat, subcat)
        if subcat_info:
            course_title = subcat_info.get("title", subcat)
        
        all_course_words = Vocabulary.query.filter(
            (Vocabulary.category.ilike(cat) & Vocabulary.subcategory.ilike(subcat))
            | (Vocabulary.category.ilike("cefr") & Vocabulary.level.ilike(subcat) if cat == "cefr" else False)
        ).order_by(Vocabulary.id).all()
        
        if not all_course_words:
            target_level = subcat_info.get("level", "B1") if subcat_info else "B1"
            all_course_words = Vocabulary.query.filter_by(level=target_level).order_by(Vocabulary.id).all()
            if not all_course_words:
                all_course_words = Vocabulary.query.order_by(Vocabulary.id).limit(60).all()

        CHUNK_SIZE = 12
        if unit:
            unit_words = [w for w in all_course_words if w.lesson_unit and (w.lesson_unit == unit or str(w.lesson_unit) == unit)]
            if not unit_words and unit.isdigit():
                u_idx = int(unit) - 1
                start_idx = max(0, u_idx * CHUNK_SIZE)
                unit_words = all_course_words[start_idx:start_idx + CHUNK_SIZE]
            
            words = unit_words if unit_words else all_course_words[:CHUNK_SIZE]
            unit_title = words[0].topic if words and words[0].topic else f"Bài {unit}"
        else:
            words = all_course_words[:CHUNK_SIZE]
            unit_title = course_title
    else:
        query = Vocabulary.query
        if level:
            query = query.filter_by(level=level)
        if topic:
            query = query.filter_by(topic=topic)
        words = query.order_by(Vocabulary.id).all()
        if not words:
            words = Vocabulary.query.order_by(Vocabulary.id).limit(12).all()
        unit_title = topic or (f"Cấp độ {level}" if level else "Học từ vựng")

    if not words:
        flash("Chưa có từ vựng nào trong bài học này.", "info")
        return redirect(url_for("learning.vocabulary"))

    if index < 0 or index >= len(words):
        index = 0

    current_word = words[index]
    progress = VocabularyProgress.query.filter_by(user_id=current_user.id, vocabulary_id=current_word.id).first()
    is_favorite = progress.is_favorite if progress else False
    is_learned = (progress.learned_count > 0 or progress.review_count > 0) if progress else False

    # Serialized words for smooth SPA flashcard experience
    words_data = []
    for w in words:
        p = VocabularyProgress.query.filter_by(user_id=current_user.id, vocabulary_id=w.id).first()
        words_data.append({
            "id": w.id,
            "word": w.word,
            "pronunciation": w.pronunciation,
            "part_of_speech": w.part_of_speech,
            "meaning_vi": w.meaning_vi,
            "example_en": w.example_en,
            "example_vi": w.example_vi,
            "image_url": w.image_url or "",
            "topic": w.topic,
            "level": w.level,
            "is_learned": (p.learned_count > 0 or p.review_count > 0) if p else False,
            "is_favorite": p.is_favorite if p else False,
        })

    back_url = url_for('learning.vocab_course_detail', cat_key=cat, subcat_key=subcat, unit=unit) if (cat and subcat) else url_for('learning.vocabulary')

    return render_template(
        "learning/study_vocabulary.html",
        word=current_word,
        words=words,
        words_data=words_data,
        index=index,
        total_words=len(words),
        unit_title=unit_title,
        course_title=course_title,
        cat=cat,
        subcat=subcat,
        unit=unit,
        back_url=back_url,
        level=level,
        topic=topic,
        autoplay=autoplay,
        show_meaning=show_meaning,
        mode=mode,
        is_favorite=is_favorite,
        is_learned=is_learned,
        form=ActionForm(),
    )


@bp.post("/vocabulary/<int:word_id>/rate")
@login_required
@csrf.exempt
def rate_word_study(word_id):
    word = db.get_or_404(Vocabulary, word_id)
    rating = request.json.get("rating") if request.is_json and request.json else request.form.get("rating", "mastered")
    
    progress = VocabularyProgress.query.filter_by(user_id=current_user.id, vocabulary_id=word.id).first()
    if not progress:
        progress = VocabularyProgress(user_id=current_user.id, vocabulary_id=word.id, learned_count=0, review_count=0, srs_level=1)
        db.session.add(progress)
    
    earned_xp = 0
    now_utc = datetime.now(timezone.utc)
    if rating == "mastered":
        progress.learned_count = (progress.learned_count or 0) + 1
        progress.srs_level = min(5, (progress.srs_level or 1) + 1)
        progress.next_review_at = now_utc + timedelta(days=3 * progress.srs_level)
        earned_xp = 5
        current_user.add_xp(5, reason="Học từ vựng thành thạo")
    elif rating == "review":
        progress.review_count = (progress.review_count or 0) + 1
        progress.next_review_at = now_utc + timedelta(days=1)
        earned_xp = 2
        current_user.add_xp(2, reason="Ôn tập từ vựng")
    else:
        progress.review_count = (progress.review_count or 0) + 1
        progress.srs_level = 1
        progress.next_review_at = now_utc + timedelta(hours=4)
    
    progress.last_reviewed_at = now_utc
    record_daily_activity(current_user)
    db.session.commit()
    streak_event = session.pop("streak_activated_popup", None)
    return jsonify({
        "success": True,
        "word_id": word.id,
        "rating": rating,
        "earned_xp": earned_xp,
        "srs_level": progress.srs_level,
        "streak_event": streak_event
    })



@bp.post("/vocabulary/<int:word_id>/favorite")
@login_required
@csrf.exempt
def favorite_word(word_id):
    word = db.get_or_404(Vocabulary, word_id)
    progress = VocabularyProgress.query.filter_by(user_id=current_user.id, vocabulary_id=word.id).first()
    if not progress:
        progress = VocabularyProgress(user_id=current_user.id, vocabulary_id=word.id, learned_count=0, review_count=0)
        db.session.add(progress)

    progress.is_favorite = not progress.is_favorite
    db.session.commit()
    if request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"success": True, "is_favorite": progress.is_favorite})
    msg = f"Đã thêm “{word.word}” vào mục yêu thích." if progress.is_favorite else f"Đã bỏ “{word.word}” khỏi danh sách yêu thích."
    flash(msg, "success")
    return redirect(request.referrer or url_for("learning.vocabulary"))


@bp.post("/vocabulary/<int:word_id>/skip")
@login_required
def skip_word(word_id):
    word = db.get_or_404(Vocabulary, word_id)
    progress = VocabularyProgress.query.filter_by(user_id=current_user.id, vocabulary_id=word.id).first()
    if not progress:
        progress = VocabularyProgress(user_id=current_user.id, vocabulary_id=word.id, learned_count=0, review_count=0)
        db.session.add(progress)

    progress.is_skipped = True
    db.session.commit()
    flash(f"Đã bỏ qua từ “{word.word}”.", "info")

    next_index = request.args.get("next_index", 0)
    level = request.args.get("level", "")
    topic = request.args.get("topic", "")
    return redirect(url_for("learning.study_vocabulary", index=next_index, level=level, topic=topic))


@bp.post("/vocabulary/<int:word_id>/report")
@login_required
def report_word(word_id):
    word = db.get_or_404(Vocabulary, word_id)
    reason = request.form.get("reason", "").strip() or "Báo cáo lỗi nội dung từ vựng"

    report = WordReport(user_id=current_user.id, vocabulary_id=word.id, reason=reason)
    db.session.add(report)
    db.session.commit()

    flash(f"Cảm ơn bạn đã báo cáo sai sót cho từ “{word.word}”. Ban quản trị sẽ kiểm tra lại.", "success")
    return redirect(request.referrer or url_for("learning.vocabulary"))


@bp.get("/vocabulary/<int:word_id>/detail")
@login_required
def vocab_word_detail_json(word_id):
    word = db.get_or_404(Vocabulary, word_id)
    progress = VocabularyProgress.query.filter_by(user_id=current_user.id, vocabulary_id=word.id).first()
    is_learned = (progress.learned_count > 0 or progress.review_count > 0) if progress else False
    is_favorite = progress.is_favorite if progress else False

    related = []
    if word.collocations:
        related.extend([c.strip() for c in word.collocations.split(",") if c.strip()])
    if word.synonyms:
        related.extend([s.strip() for s in word.synonyms.split(",") if s.strip()])
    if not related:
        w_clean = word.word.strip().lower()
        if len(w_clean) > 3:
            related = [w_clean]
            if not w_clean.endswith("ing"):
                related.append(f"{w_clean}ing")
            if not w_clean.endswith("ed"):
                related.append(f"{w_clean}ed")

    return jsonify({
        "id": word.id,
        "word": word.word,
        "pronunciation": word.pronunciation,
        "part_of_speech": word.part_of_speech,
        "meaning_vi": word.meaning_vi,
        "example_en": word.example_en or f"Please learn and remember the word '{word.word}'.",
        "example_vi": word.example_vi or f"Vui lòng ghi nhớ từ '{word.word}'.",
        "definition_en": f"To {word.meaning_vi.lower()} in context." if not word.example_en else f"1. Expressing {word.meaning_vi}.",
        "topic": word.topic,
        "level": word.level,
        "image_url": word.image_url or "",
        "is_learned": is_learned,
        "is_favorite": is_favorite,
        "personal_notes": progress.personal_notes if progress else "",
        "custom_example": progress.custom_example if progress else "",
        "related_words": related[:6]
    })


@bp.post("/vocabulary/<int:word_id>/toggle-learned")
@login_required
def toggle_word_learned_ajax(word_id):
    word = db.get_or_404(Vocabulary, word_id)
    progress = VocabularyProgress.query.filter_by(user_id=current_user.id, vocabulary_id=word.id).first()
    if not progress:
        progress = VocabularyProgress(user_id=current_user.id, vocabulary_id=word.id, learned_count=0, review_count=0)
        db.session.add(progress)

    if progress.learned_count > 0 or progress.review_count > 0:
        progress.learned_count = 0
        progress.review_count = 0
        is_learned = False
        msg = f"Đã đánh dấu '{word.word}' là chưa thuộc."
    else:
        progress.learned_count = 1
        progress.last_reviewed_at = func.now()
        is_learned = True
        msg = f"Đã đánh dấu '{word.word}' là đã học!"
        current_user.add_xp(5, reason="Học từ vựng")

    db.session.commit()
    return jsonify({
        "success": True,
        "is_learned": is_learned,
        "message": msg
    })



@bp.get("/flashcards")
@login_required
def flashcards():
    return redirect(url_for("learning.vocabulary", tab="flashcards"))


@bp.post("/flashcards/<int:word_id>/<action>")
@login_required
def review_flashcard(word_id, action):
    if action not in ("known", "review"):
        abort(404)
    word = db.get_or_404(Vocabulary, word_id)
    form = ActionForm()
    if not form.validate_on_submit():
        abort(400)
    progress = VocabularyProgress.query.filter_by(user_id=current_user.id, vocabulary_id=word.id).first()
    if not progress:
        progress = VocabularyProgress(user_id=current_user.id, vocabulary_id=word.id, learned_count=0, review_count=0)
        db.session.add(progress)
    if action == "known":
        progress.learned_count = (progress.learned_count or 0) + 1
        current_user.add_xp(5, reason="Học từ vựng")
        update_challenge_progress(current_user, "vocab", 1)
        check_user_badges(current_user)
    else:
        progress.review_count = (progress.review_count or 0) + 1
    progress.last_reviewed_at = func.now()
    db.session.commit()
    return ("", 204)




@bp.get("/flashcard-sets")
@login_required
def flashcard_sets():
    return redirect(url_for("learning.vocabulary", tab="flashcards"))


@bp.route("/flashcard-sets/new", methods=["GET", "POST"])
@login_required
def flashcard_set_create():
    if request.method == "POST":
        from .models import FlashcardSet, FlashcardItem
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        is_public = request.form.get("is_public") == "on"
        
        if not title:
            flash("Vui lòng nhập tiêu đề học phần.", "danger")
            return redirect(url_for("learning.flashcard_set_create"))
            
        new_set = FlashcardSet(
            title=title,
            description=description,
            is_public=is_public,
            user_id=current_user.id
        )
        db.session.add(new_set)
        db.session.flush() # Lấy new_set.id
        
        # Xử lý các Flashcard Items động
        terms = request.form.getlist("terms[]")
        definitions = request.form.getlist("definitions[]")
        images = request.form.getlist("images[]")
        
        for i in range(len(terms)):
            term = terms[i].strip()
            definition = definitions[i].strip()
            image_url = images[i].strip() if i < len(images) else None
            
            if term or definition: # Lưu nếu 1 trong 2 có dữ liệu
                item = FlashcardItem(
                    set_id=new_set.id,
                    term=term,
                    definition=definition,
                    image_url=image_url,
                    order=i
                )
                db.session.add(item)
                
        db.session.commit()
        flash(f"Học phần '{title}' đã được tạo thành công!", "success")
        return redirect(url_for("learning.vocabulary", tab="flashcards"))
        
    return render_template("learning/flashcard_create.html", fset=None)


@bp.route("/flashcard-sets/<int:set_id>/edit", methods=["GET", "POST"])
@login_required
def flashcard_set_edit(set_id):
    from .models import FlashcardSet, FlashcardItem
    fset = FlashcardSet.query.get_or_404(set_id)
    if fset.user_id != current_user.id:
        abort(403)
        
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        is_public = request.form.get("is_public") == "on"
        
        if not title:
            flash("Vui lòng nhập tiêu đề học phần.", "danger")
            return redirect(url_for("learning.flashcard_set_edit", set_id=fset.id))
            
        fset.title = title
        fset.description = description
        fset.is_public = is_public
        
        item_ids = request.form.getlist("item_ids[]")
        terms = request.form.getlist("terms[]")
        definitions = request.form.getlist("definitions[]")
        images = request.form.getlist("images[]")
        
        valid_item_ids = [int(i) for i in item_ids if i.strip().isdigit()]
        
        items_to_delete = FlashcardItem.query.filter(
            FlashcardItem.set_id == fset.id,
            ~FlashcardItem.id.in_(valid_item_ids) if valid_item_ids else True
        ).all()
        for item in items_to_delete:
            db.session.delete(item)
            
        for i in range(len(terms)):
            term = terms[i].strip()
            definition = definitions[i].strip()
            image_url = images[i].strip() if i < len(images) else None
            item_id = item_ids[i].strip() if i < len(item_ids) else ""
            
            if not term and not definition:
                continue
                
            if item_id and item_id.isdigit():
                item = FlashcardItem.query.filter_by(id=int(item_id), set_id=fset.id).first()
                if item:
                    item.term = term
                    item.definition = definition
                    item.image_url = image_url
                    item.order = i
            else:
                new_item = FlashcardItem(
                    set_id=fset.id,
                    term=term,
                    definition=definition,
                    image_url=image_url,
                    order=i
                )
                db.session.add(new_item)
                
        db.session.commit()
        flash(f"Học phần '{title}' đã được cập nhật!", "success")
        return redirect(url_for("learning.flashcard_set_view", set_id=fset.id))
        
    return render_template("learning/flashcard_create.html", fset=fset)


@bp.get("/flashcard-sets/<int:set_id>")
@login_required
def flashcard_set_view(set_id):
    from .models import FlashcardSet
    fset = FlashcardSet.query.get_or_404(set_id)
    # Check permissions
    if not fset.is_public and fset.user_id != current_user.id:
        abort(403)
    return render_template("learning/flashcard_view.html", fset=fset)


@bp.post("/flashcard-sets/<int:set_id>/sync")
@login_required
def flashcard_set_sync(set_id):
    from .models import FlashcardSet, FlashcardProgress
    fset = FlashcardSet.query.get_or_404(set_id)
    if not fset.is_public and fset.user_id != current_user.id:
        abort(403)

    data = request.get_json()
    if not data or "progress" not in data:
        return {"error": "Invalid payload"}, 400

    know_ids = data["progress"].get("know_ids", [])
    learning_ids = data["progress"].get("learning_ids", [])

    # Fetch existing progress for these items
    all_item_ids = know_ids + learning_ids
    if not all_item_ids:
        return {"status": "ok"}

    existing_progress = FlashcardProgress.query.filter(
        FlashcardProgress.user_id == current_user.id,
        FlashcardProgress.item_id.in_(all_item_ids)
    ).all()
    
    progress_map = {p.item_id: p for p in existing_progress}

    # Helper function to update or create progress
    def update_progress(item_id, is_known):
        p = progress_map.get(item_id)
        if not p:
            p = FlashcardProgress(user_id=current_user.id, item_id=item_id, review_count=0, srs_level=1)
            db.session.add(p)
        if p.review_count is None:
            p.review_count = 0
        if p.srs_level is None:
            p.srs_level = 1
        p.is_known = is_known
        p.review_count += 1
        p.last_reviewed_at = func.now()
        
        # SRS calculation
        curr_level = p.srs_level
        if is_known:
            p.srs_level = min(5, curr_level + 1)
        else:
            p.srs_level = 1
            
        intervals = {1: 1, 2: 3, 3: 7, 4: 14, 5: 30}
        days = intervals.get(p.srs_level, 1)
        p.next_review_at = datetime.utcnow() + timedelta(days=days)

    for item_id in know_ids:
        update_progress(item_id, True)

    for item_id in learning_ids:
        update_progress(item_id, False)

    db.session.commit()
    return {"status": "ok", "synced_items": len(all_item_ids)}


@bp.post("/flashcard-sets/<int:set_id>/delete")
@login_required
def flashcard_set_delete(set_id):
    from .models import FlashcardSet
    fset = FlashcardSet.query.get_or_404(set_id)
    if fset.user_id != current_user.id:
        abort(403)
        
    db.session.delete(fset)
    db.session.commit()
    flash(f"Học phần '{fset.title}' đã bị xóa.", "success")
    return redirect(url_for("learning.vocabulary", tab="flashcards"))


@bp.get("/flashcards/share/<share_code>")
@bp.get("/flashcard-sets/share/<share_code>")
def flashcard_share(share_code):
    from .models import FlashcardSet
    fset = FlashcardSet.query.filter_by(share_code=share_code).first()
    if not fset and share_code.isdigit():
        fset = FlashcardSet.query.get(int(share_code))
    if not fset:
        abort(404)
        
    # Ensure share_code exists for link sharing
    if not fset.share_code:
        fset.get_share_code()
        db.session.commit()
        
    return render_template("learning/flashcard_share.html", fset=fset)


@bp.post("/flashcards/share/<share_code>/clone")
@bp.post("/flashcard-sets/share/<share_code>/clone")
@login_required
def flashcard_share_clone(share_code):
    return _clone_flashcard_set(share_code=share_code)


@bp.post("/flashcard-sets/<int:set_id>/clone")
@login_required
def flashcard_set_clone_by_id(set_id):
    return _clone_flashcard_set(set_id=set_id)


def _clone_flashcard_set(share_code=None, set_id=None):
    from .models import FlashcardSet, FlashcardItem
    fset = None
    if set_id is not None:
        fset = FlashcardSet.query.get_or_404(set_id)
    elif share_code:
        fset = FlashcardSet.query.filter_by(share_code=share_code).first()
        if not fset and share_code.isdigit():
            fset = FlashcardSet.query.get(int(share_code))
        if not fset:
            abort(404)
    else:
        abort(400)

    # Permissions: allow if public or owner or has the direct share link
    if not fset.is_public and fset.user_id != current_user.id and fset.share_code != share_code:
        abort(403)

    cloned_title = fset.title
    if fset.user_id == current_user.id:
        cloned_title = f"{fset.title} (Bản sao)"

    cloned_set = FlashcardSet(
        title=cloned_title,
        description=fset.description,
        is_public=False,
        share_code=secrets.token_urlsafe(8),
        user_id=current_user.id
    )
    db.session.add(cloned_set)
    db.session.flush()

    for item in fset.items:
        new_item = FlashcardItem(
            set_id=cloned_set.id,
            term=item.term,
            definition=item.definition,
            image_url=item.image_url,
            order=item.order
        )
        db.session.add(new_item)

    db.session.commit()
    flash(f"Đã sao chép thành công bộ flashcard '{cloned_set.title}' vào tài khoản của bạn!", "success")
    return redirect(url_for("learning.flashcard_set_view", set_id=cloned_set.id))


@bp.post("/flashcard-sets/<int:set_id>/toggle-privacy")
@login_required
def flashcard_set_toggle_privacy(set_id):
    from .models import FlashcardSet
    fset = FlashcardSet.query.get_or_404(set_id)
    if fset.user_id != current_user.id:
        abort(403)

    fset.is_public = not fset.is_public
    db.session.commit()

    status_str = "Công khai (Hiển thị trên Thư viện cộng đồng)" if fset.is_public else "Riêng tư (Chỉ mình tôi)"
    msg = f"Đã chuyển bộ thẻ '{fset.title}' sang chế độ {status_str}."

    if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json:
        return jsonify({
            "status": "ok",
            "is_public": fset.is_public,
            "message": msg
        })

    flash(msg, "success")
    return redirect(request.referrer or url_for("learning.flashcard_set_view", set_id=fset.id))


# ==========================================
# GAME SYSTEM ROUTES
# ==========================================
import uuid
import json
from datetime import datetime, timedelta



@bp.get("/vocabulary/review")
@login_required
def review_vocabulary():
    mode = request.args.get("mode", "flashcard")
    try:
        index = int(request.args.get("index", 0))
    except ValueError:
        index = 0

    now_dt = datetime.utcnow()

    # Fetch due vocabulary progress records for current user
    due_progress = VocabularyProgress.query.filter(
        VocabularyProgress.user_id == current_user.id,
        (VocabularyProgress.learned_count > 0) | (VocabularyProgress.review_count > 0),
        (VocabularyProgress.next_review_at <= now_dt) | (VocabularyProgress.next_review_at.is_(None))
    ).order_by(VocabularyProgress.next_review_at.asc()).all()

    if not due_progress:
        due_progress = VocabularyProgress.query.filter(
            VocabularyProgress.user_id == current_user.id,
            (VocabularyProgress.learned_count > 0) | (VocabularyProgress.review_count > 0)
        ).all()

    if not due_progress:
        sample_words = Vocabulary.query.order_by(Vocabulary.id).limit(10).all()
        if not sample_words:
            flash("Chưa có từ vựng nào trong hệ thống.", "info")
            return redirect(url_for("learning.vocabulary"))
        due_word_ids = [w.id for w in sample_words]
    else:
        due_word_ids = [p.vocabulary_id for p in due_progress]

    total_words = len(due_word_ids)
    if index < 0 or index >= total_words:
        index = 0

    current_vocab_id = due_word_ids[index]
    word = db.get_or_404(Vocabulary, current_vocab_id)
    progress = VocabularyProgress.query.filter_by(user_id=current_user.id, vocabulary_id=word.id).first()

    if not progress:
        progress = VocabularyProgress(
            user_id=current_user.id,
            vocabulary_id=word.id,
            learned_count=0,
            review_count=0,
            srs_level=1,
            next_review_at=now_dt
        )
        db.session.add(progress)
        db.session.commit()

    choices = []
    if mode in ("meaning", "audio"):
        other_words = Vocabulary.query.filter(Vocabulary.id != word.id).all()
        sample_size = min(3, len(other_words))
        distractor_meanings = [w.meaning_vi for w in random.sample(other_words, sample_size)] if sample_size > 0 else []
        choices = distractor_meanings + [word.meaning_vi]
        random.shuffle(choices)

    return render_template(
        "learning/review_vocabulary.html",
        word=word,
        progress=progress,
        index=index,
        total_words=total_words,
        mode=mode,
        choices=choices,
        form=ActionForm()
    )


@bp.post("/vocabulary/review/submit")
@login_required
def review_vocabulary_submit():
    from flask import session
    word_id = request.form.get("word_id", type=int)
    rating = request.form.get("rating", "good")
    mode = request.form.get("mode", "flashcard")
    index = request.form.get("index", 0, type=int)
    total_words = request.form.get("total_words", 1, type=int)

    word = db.get_or_404(Vocabulary, word_id)
    progress = VocabularyProgress.query.filter_by(user_id=current_user.id, vocabulary_id=word.id).first()
    if not progress:
        progress = VocabularyProgress(user_id=current_user.id, vocabulary_id=word.id, learned_count=0, review_count=0)
        db.session.add(progress)

    now_dt = datetime.utcnow()
    algo = getattr(current_user, "vocab_srs_algorithm", "standard") or "standard"
    if algo == "aggressive":
        srs_intervals = {1: 2, 2: 4, 3: 7, 4: 14, 5: 30, 6: 60, 7: 120}
    elif algo == "conservative":
        srs_intervals = {1: 1, 2: 1, 3: 2, 4: 4, 5: 7, 6: 14, 7: 30}
    else:
        srs_intervals = {1: 1, 2: 2, 3: 4, 4: 7, 5: 14, 6: 30, 7: 90}

    if "srs_session" not in session:
        session["srs_session"] = {
            "total_reviewed": 0,
            "mastered_ids": [],
            "need_more_ids": []
        }

    sess_data = session["srs_session"]

    if rating != "skip":
        progress.review_count = (progress.review_count or 0) + 1
        progress.last_reviewed_at = now_dt
        curr_level = progress.srs_level or 1

        if rating == "easy":
            new_level = min(7, curr_level + 2)
            days = srs_intervals[new_level]
        elif rating in ("good", "correct"):
            new_level = min(7, curr_level + 1)
            days = srs_intervals[new_level]
        elif rating == "hard":
            new_level = max(1, curr_level)
            days = 1
            if word.id not in sess_data["need_more_ids"]:
                sess_data["need_more_ids"].append(word.id)
        elif rating == "incorrect":
            new_level = max(1, curr_level - 1)
            days = 1
            if word.id not in sess_data["need_more_ids"]:
                sess_data["need_more_ids"].append(word.id)

        progress.srs_level = new_level
        progress.next_review_at = now_dt + timedelta(days=days)
        sess_data["total_reviewed"] += 1

        if new_level == 7 and word.id not in sess_data["mastered_ids"]:
            sess_data["mastered_ids"].append(word.id)

        db.session.commit()
        record_daily_activity(current_user)
        session.modified = True

    if index + 1 < total_words:
        return redirect(url_for("learning.review_vocabulary", mode=mode, index=index + 1))
    else:
        return redirect(url_for("learning.review_summary"))


@bp.get("/vocabulary/review/summary")
@login_required
def review_summary():
    from flask import session
    sess_data = session.get("srs_session", {
        "total_reviewed": 0,
        "mastered_ids": [],
        "need_more_ids": []
    })

    mastered_words = Vocabulary.query.filter(Vocabulary.id.in_(sess_data["mastered_ids"])).all() if sess_data["mastered_ids"] else []
    need_more_words = Vocabulary.query.filter(Vocabulary.id.in_(sess_data["need_more_ids"])).all() if sess_data["need_more_ids"] else []

    total_revived = sess_data["total_reviewed"]
    session.pop("srs_session", None)

    return render_template(
        "learning/review_summary.html",
        total_reviewed=total_revived,
        mastered_words=mastered_words,
        need_more_words=need_more_words
    )


# ==========================================
# VOCABULARY MANAGEMENT ROUTES
# ==========================================

@bp.get("/vocabulary/manage")
@login_required
def manage_vocabulary():
    q = request.args.get("q", "").strip()
    level = request.args.get("level", "")
    topic = request.args.get("topic", "")
    status = request.args.get("status", "")
    srs_lvl_arg = request.args.get("srs_level", "")
    sort_by = request.args.get("sort", "alpha_asc")

    query = Vocabulary.query

    if q:
        query = query.filter(
            Vocabulary.word.ilike(f"%{q}%") | Vocabulary.meaning_vi.ilike(f"%{q}%")
        )

    if level:
        query = query.filter_by(level=level)

    if topic:
        query = query.filter_by(topic=topic)

    all_progress = VocabularyProgress.query.filter_by(user_id=current_user.id).all()
    progress_map = {p.vocabulary_id: p for p in all_progress}

    all_vocab = query.all()
    now_dt = datetime.utcnow()

    filtered_list = []
    for vocab in all_vocab:
        p = progress_map.get(vocab.id)
        learned_cnt = p.learned_count if p else 0
        review_cnt = p.review_count if p else 0
        srs_lvl = p.srs_level if p else 1
        next_rev = p.next_review_at if p else None

        if not p or (learned_cnt == 0 and review_cnt == 0):
            item_status = "new"
        elif srs_lvl >= 7 or (learned_cnt >= 3 and review_cnt >= 3):
            item_status = "mastered"
        elif next_rev and next_rev <= now_dt:
            item_status = "reviewing"
        else:
            item_status = "learning"

        if status and item_status != status:
            continue

        if srs_lvl_arg and srs_lvl_arg.isdigit():
            if srs_lvl != int(srs_lvl_arg):
                continue

        filtered_list.append({
            "vocab": vocab,
            "progress": p,
            "status": item_status,
            "srs_level": srs_lvl,
            "learned_count": learned_cnt,
            "review_count": review_cnt,
            "last_reviewed_at": p.last_reviewed_at if p else None,
            "next_review_at": next_rev,
            "personal_notes": p.personal_notes if p else "",
            "custom_example": p.custom_example if p else "",
        })

    if sort_by == "alpha_asc":
        filtered_list.sort(key=lambda x: x["vocab"].word.lower())
    elif sort_by == "alpha_desc":
        filtered_list.sort(key=lambda x: x["vocab"].word.lower(), reverse=True)
    elif sort_by == "learned_desc":
        filtered_list.sort(key=lambda x: x["last_reviewed_at"] or datetime.min, reverse=True)
    elif sort_by == "learned_asc":
        filtered_list.sort(key=lambda x: x["last_reviewed_at"] or datetime.min)
    elif sort_by == "review_desc":
        filtered_list.sort(key=lambda x: x["next_review_at"] or datetime.min, reverse=True)
    elif sort_by == "review_asc":
        filtered_list.sort(key=lambda x: x["next_review_at"] or datetime.min)

    topics = [r[0] for r in db.session.query(Vocabulary.topic).distinct().order_by(Vocabulary.topic).all()]
    levels = ["A1", "A2", "B1", "B2", "C1", "C2"]

    return render_template(
        "learning/manage_vocabulary.html",
        items=filtered_list,
        topics=topics,
        levels=levels,
        q=q,
        level=level,
        topic=topic,
        status=status,
        srs_level=srs_lvl_arg,
        sort=sort_by,
        form=ActionForm(),
    )


@bp.post("/vocabulary/<int:vocab_id>/notes")
@login_required
def update_word_notes(vocab_id):
    word = db.get_or_404(Vocabulary, vocab_id)
    notes = request.form.get("personal_notes", "").strip()
    custom_example = request.form.get("custom_example", "").strip()

    progress = VocabularyProgress.query.filter_by(user_id=current_user.id, vocabulary_id=word.id).first()
    if not progress:
        progress = VocabularyProgress(user_id=current_user.id, vocabulary_id=word.id)
        db.session.add(progress)

    progress.personal_notes = notes
    progress.custom_example = custom_example
    db.session.commit()

    flash(f"Đã cập nhật ghi chú cá nhân cho từ “{word.word}”.", "success")
    return redirect(request.referrer or url_for("learning.manage_vocabulary"))


@bp.post("/vocabulary/<int:vocab_id>/reset-progress")
@login_required
def reset_word_progress(vocab_id):
    word = db.get_or_404(Vocabulary, vocab_id)
    progress = VocabularyProgress.query.filter_by(user_id=current_user.id, vocabulary_id=word.id).first()
    if progress:
        progress.learned_count = 0
        progress.review_count = 0
        progress.srs_level = 1
        progress.next_review_at = datetime.utcnow()
        db.session.commit()

    flash(f"Đã đặt lại tiến độ học cho từ “{word.word}”.", "info")
    return redirect(request.referrer or url_for("learning.manage_vocabulary"))


@bp.post("/vocabulary/<int:vocab_id>/delete-progress")
@login_required
def delete_word_progress(vocab_id):
    word = db.get_or_404(Vocabulary, vocab_id)
    progress = VocabularyProgress.query.filter_by(user_id=current_user.id, vocabulary_id=word.id).first()
    if progress:
        db.session.delete(progress)
        db.session.commit()

    flash(f"Đã xóa từ “{word.word}” khỏi danh sách học cá nhân.", "warning")
    return redirect(request.referrer or url_for("learning.manage_vocabulary"))


@bp.post("/vocabulary/bulk-action")
@login_required
def bulk_vocab_action():
    action = request.form.get("bulk_action", "")
    vocab_ids = request.form.getlist("vocab_ids")

    valid_ids = [int(vid) for vid in vocab_ids if vid.isdigit()]
    if not valid_ids or not action:
        flash("Vui lòng chọn ít nhất một từ vựng và hành động tương ứng.", "warning")
        return redirect(request.referrer or url_for("learning.manage_vocabulary"))

    now_dt = datetime.utcnow()
    count = 0

    for vid in valid_ids:
        progress = VocabularyProgress.query.filter_by(user_id=current_user.id, vocabulary_id=vid).first()
        if action == "learn":
            if not progress:
                progress = VocabularyProgress(user_id=current_user.id, vocabulary_id=vid)
                db.session.add(progress)
            progress.learned_count = (progress.learned_count or 0) + 1
            progress.last_reviewed_at = now_dt
            count += 1
        elif action == "reset":
            if progress:
                progress.learned_count = 0
                progress.review_count = 0
                progress.srs_level = 1
                progress.next_review_at = now_dt
                count += 1
        elif action == "delete":
            if progress:
                db.session.delete(progress)
                count += 1

    db.session.commit()
    flash(f"Đã thực hiện thao tác hàng loạt thành công trên {count} từ vựng.", "success")
    return redirect(request.referrer or url_for("learning.manage_vocabulary"))


# ==========================================
# VOCABULARY STATISTICS ROUTES
# ==========================================

@bp.get("/vocabulary/stats")
@login_required
def vocabulary_stats():
    current_streak = getattr(current_user, "current_streak", 0) or 0
    longest_streak = getattr(current_user, "longest_streak", 0) or 0

    user_progress = VocabularyProgress.query.filter_by(user_id=current_user.id).all()
    progress_map = {p.vocabulary_id: p for p in user_progress}

    srs_distribution = {lvl: 0 for lvl in range(1, 8)}
    learned_words_count = 0
    mastered_count = 0
    retention_count = 0

    for p in user_progress:
        if p.learned_count > 0 or p.review_count > 0:
            learned_words_count += 1
            lvl = p.srs_level if p.srs_level in range(1, 8) else 1
            srs_distribution[lvl] += 1
            if lvl >= 7 or (p.learned_count >= 3 and p.review_count >= 3):
                mastered_count += 1
            if lvl >= 4:
                retention_count += 1

    accuracy_rate = round((mastered_count / learned_words_count * 100)) if learned_words_count > 0 else 100
    review_success_rate = round((sum(1 for p in user_progress if p.srs_level >= 3) / learned_words_count * 100)) if learned_words_count > 0 else 100
    retention_rate = round((retention_count / learned_words_count * 100)) if learned_words_count > 0 else 100

    all_topics = [r[0] for r in db.session.query(Vocabulary.topic).distinct().order_by(Vocabulary.topic).all()]
    topic_breakdown = []

    for t in all_topics:
        topic_words = Vocabulary.query.filter_by(topic=t).all()
        t_total = len(topic_words)
        if t_total == 0:
            continue
        t_mastered = sum(
            1 for w in topic_words
            if w.id in progress_map and (progress_map[w.id].srs_level >= 7 or progress_map[w.id].learned_count >= 3)
        )
        t_pct = round((t_mastered / t_total) * 100)
        topic_breakdown.append({
            "topic": t,
            "total": t_total,
            "mastered": t_mastered,
            "pct": t_pct
        })

    topic_breakdown.sort(key=lambda x: x["pct"], reverse=True)
    weak_topics = sorted([tb for tb in topic_breakdown if tb["pct"] < 100], key=lambda x: x["pct"])[:3]

    mastered_progress = [
        p for p in user_progress
        if p.srs_level >= 7 or (p.learned_count >= 3 and p.review_count >= 3)
    ]
    mastered_progress.sort(key=lambda p: p.last_reviewed_at or datetime.min, reverse=True)

    mastered_timeline = []
    for p in mastered_progress[:15]:
        v = Vocabulary.query.get(p.vocabulary_id)
        if v:
            mastered_timeline.append({
                "vocab": v,
                "date": p.last_reviewed_at
            })

    today = date.today()
    daily_labels = []
    daily_values = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        daily_labels.append(day.strftime("%d/%m"))
        cnt = sum(
            1 for p in user_progress
            if p.last_reviewed_at and p.last_reviewed_at.date() <= day
        )
        daily_values.append(cnt)

    weekly_labels = ["Tuần 4 trước", "Tuần 3 trước", "Tuần 2 trước", "Tuần này"]
    weekly_values = []
    for i in range(3, -1, -1):
        target_date = today - timedelta(weeks=i)
        cnt = sum(
            1 for p in user_progress
            if p.last_reviewed_at and p.last_reviewed_at.date() <= target_date
        )
        weekly_values.append(cnt)

    monthly_labels = ["M1", "M2", "M3", "M4", "M5", "M6"]
    monthly_values = []
    for i in range(5, -1, -1):
        target_date = today - timedelta(days=30 * i)
        monthly_labels[5 - i] = target_date.strftime("T%m/%Y")
        cnt = sum(
            1 for p in user_progress
            if p.last_reviewed_at and p.last_reviewed_at.date() <= target_date
        )
        monthly_values.append(cnt)

    return render_template(
        "learning/vocabulary_stats.html",
        current_streak=current_streak,
        longest_streak=longest_streak,
        learned_words_count=learned_words_count,
        mastered_count=mastered_count,
        accuracy_rate=accuracy_rate,
        review_success_rate=review_success_rate,
        retention_rate=retention_rate,
        srs_distribution=srs_distribution,
        topic_breakdown=topic_breakdown,
        weak_topics=weak_topics,
        mastered_timeline=mastered_timeline,
        daily_labels=daily_labels,
        daily_values=daily_values,
        weekly_labels=weekly_labels,
        weekly_values=weekly_values,
        monthly_labels=monthly_labels,
        monthly_values=monthly_values,
    )


# ==========================================
# VOCABULARY SETTINGS ROUTES
# ==========================================

@bp.route("/vocabulary/settings", methods=["GET", "POST"])
@login_required
def vocabulary_settings():
    if request.method == "POST":
        goal = request.form.get("daily_vocab_goal", type=int)
        if goal and 10 <= goal <= 50:
            current_user.daily_vocab_goal = goal

        priority = request.form.get("vocab_review_priority", "due_date")
        if priority in ("due_date", "srs_level_asc", "srs_level_desc", "random"):
            current_user.vocab_review_priority = priority

        current_user.vocab_auto_play_audio = (request.form.get("vocab_auto_play_audio") == "on")

        accent = request.form.get("vocab_accent", "en-US")
        if accent in ("en-US", "en-GB"):
            current_user.vocab_accent = accent

        display_mode = request.form.get("vocab_display_mode", "flashcard")
        if display_mode in ("flashcard", "list"):
            current_user.vocab_display_mode = display_mode

        review_time = request.form.get("vocab_review_time", "anytime")
        if review_time in ("morning", "evening", "anytime"):
            current_user.vocab_review_time = review_time

        srs_algo = request.form.get("vocab_srs_algorithm", "standard")
        if srs_algo in ("standard", "aggressive", "conservative"):
            current_user.vocab_srs_algorithm = srs_algo

        current_user.vocab_notify_review_due = (request.form.get("vocab_notify_review_due") == "on")
        current_user.vocab_reminder_enabled = (request.form.get("vocab_reminder_enabled") == "on")
        reminder_time = request.form.get("vocab_reminder_time", "09:00")
        if reminder_time:
            current_user.vocab_reminder_time = reminder_time[:10]

        db.session.commit()
        flash("Đã cập nhật các cài đặt từ vựng cá nhân thành công!", "success")
        return redirect(url_for("learning.vocabulary_settings"))

    return render_template("learning/vocabulary_settings.html")


@bp.get("/api/vocabulary/notification-check")
@login_required
def vocabulary_notification_check():
    now_dt = datetime.now(timezone.utc)
    due_count = VocabularyProgress.query.filter(
        VocabularyProgress.user_id == current_user.id,
        (VocabularyProgress.learned_count > 0) | (VocabularyProgress.review_count > 0),
        (VocabularyProgress.next_review_at <= now_dt) | (VocabularyProgress.next_review_at.is_(None))
    ).count()

    is_enabled = getattr(current_user, "vocab_reminder_enabled", True)
    reminder_time = getattr(current_user, "vocab_reminder_time", "09:00") or "09:00"

    title = "EnglishMate - Nhắc nhở ôn tập từ vựng 🔔"
    if due_count > 0:
        body = f"Bạn đang có {due_count} từ vựng đến hạn ôn tập SRS hôm nay. Dành 5 phút ôn luyện để duy trì trí nhớ nhé!"
    else:
        body = "Tuyệt vời! Bạn không có từ vựng nào tồn đọng đến hạn ôn tập hôm nay."

    return jsonify({
        "success": True,
        "enabled": is_enabled,
        "reminder_time": reminder_time,
        "due_count": due_count,
        "has_due": due_count > 0,
        "title": title,
        "body": body,
        "review_url": url_for("learning.review_vocabulary"),
        "icon": url_for("static", filename="images/brand-icon.png", _external=False),
    })


@bp.post("/api/vocabulary/subscribe-push")
@login_required
def vocabulary_subscribe_push():
    data = request.get_json(silent=True) or request.form.to_dict()
    subscription_data = data.get("subscription")
    if subscription_data:
        import json
        if isinstance(subscription_data, (dict, list)):
            current_user.vocab_push_subscription = json.dumps(subscription_data)
        else:
            current_user.vocab_push_subscription = str(subscription_data)

    if "enabled" in data:
        current_user.vocab_reminder_enabled = bool(data.get("enabled"))

    db.session.commit()
    return jsonify({"success": True, "message": "Cập nhật đăng ký nhận thông báo Web Push thành công."})


@bp.post("/api/vocabulary/send-test-notification")
@login_required
def vocabulary_send_test_notification():
    now_dt = datetime.now(timezone.utc)
    due_count = VocabularyProgress.query.filter(
        VocabularyProgress.user_id == current_user.id,
        (VocabularyProgress.learned_count > 0) | (VocabularyProgress.review_count > 0),
        (VocabularyProgress.next_review_at <= now_dt) | (VocabularyProgress.next_review_at.is_(None))
    ).count()

    return jsonify({
        "success": True,
        "title": "EnglishMate - Kiểm tra thông báo trình duyệt 🔔",
        "body": f"Thông báo Web Push hoạt động hoàn hảo! Hiện có {due_count} từ vựng sẵn sàng để ôn tập.",
        "due_count": due_count,
        "review_url": url_for("learning.review_vocabulary"),
        "icon": url_for("static", filename="images/brand-icon.png", _external=False),
    })


# ==========================================
# GOAL REMINDER API & CONTROLS
# ==========================================

@bp.get("/api/goal/notification-check")
@login_required
def goal_notification_check():
    """
    Checks if current student needs an in-app popup or browser notification reminder
    before 24:00 midnight for Daily Goal completion.
    """
    if current_user.is_admin:
        return jsonify({"success": False, "reason": "admin_excluded"})

    from .goal_reminder import check_user_goal_reminder_alert, get_user_daily_goal_status, get_vietnam_time
    force_hour = request.args.get("force_hour", type=int)
    alert_info = check_user_goal_reminder_alert(current_user, force_hour=force_hour)
    status = alert_info.get("status") or get_user_daily_goal_status(current_user)

    from flask import session
    dismissed_date = session.get("goal_reminder_dismissed_date")
    today_str = str(get_vietnam_time().date())
    is_dismissed = (dismissed_date == today_str)

    should_show_popup = bool(alert_info.get("should_popup") and not is_dismissed)

    return jsonify({
        "success": True,
        "should_remind": alert_info.get("should_remind", False),
        "should_popup": should_show_popup,
        "is_evening_near_deadline": alert_info.get("is_evening_near_deadline", False),
        "is_dismissed": is_dismissed,
        "title": alert_info.get("title", "⏰ Sắp hết ngày! Nhắc nhở Mục tiêu học tập"),
        "message": alert_info.get("message", ""),
        "status": status,
        "learn_url": alert_info.get("learn_url", url_for("learning.lessons")),
        "review_url": alert_info.get("review_url", url_for("learning.review_vocabulary")),
        "reward_url": alert_info.get("reward_url", url_for("learning.gamification_hub", tab="challenges")),
        "icon": url_for("static", filename="images/brand-icon.png", _external=False),
    })


@bp.post("/api/goal/dismiss-popup")
@login_required
def goal_dismiss_popup():
    """
    Marks the goal reminder popup as dismissed for today's session.
    """
    from .goal_reminder import get_vietnam_time
    from flask import session
    today_str = str(get_vietnam_time().date())
    session["goal_reminder_dismissed_date"] = today_str
    return jsonify({"success": True, "dismissed_date": today_str})


@bp.post("/api/goal/settings")
@login_required
def goal_update_settings():
    """
    Updates user's daily goal reminder preferences and target XP.
    """
    if current_user.is_admin:
        return jsonify({"success": False, "message": "Quản trị viên không áp dụng mục tiêu ngày."}), 403

    data = request.get_json(silent=True) or request.form.to_dict()
    
    if "enabled" in data:
        val = data.get("enabled")
        current_user.daily_goal_reminder_enabled = val in [True, 1, "1", "true", "True", "on"]
    if "reminder_time" in data and data.get("reminder_time"):
        current_user.daily_goal_reminder_time = str(data.get("reminder_time")).strip()
    if "email_enabled" in data:
        val = data.get("email_enabled")
        current_user.daily_goal_reminder_email = val in [True, 1, "1", "true", "True", "on"]
    if "popup_enabled" in data:
        val = data.get("popup_enabled")
        current_user.daily_goal_reminder_popup = val in [True, 1, "1", "true", "True", "on"]
    if "daily_goal_xp" in data:
        try:
            val = int(data.get("daily_goal_xp"))
            if 10 <= val <= 500:
                current_user.daily_goal_xp = val
        except (ValueError, TypeError):
            pass

    db.session.commit()
    return jsonify({
        "success": True,
        "message": "Đã lưu cài đặt Nhắc nhở Mục tiêu ngày thành công!",
        "settings": {
            "daily_goal_reminder_enabled": current_user.daily_goal_reminder_enabled,
            "daily_goal_reminder_time": current_user.daily_goal_reminder_time,
            "daily_goal_reminder_email": current_user.daily_goal_reminder_email,
            "daily_goal_reminder_popup": current_user.daily_goal_reminder_popup,
            "daily_goal_xp": current_user.daily_goal_xp,
        }
    })


@bp.post("/api/goal/send-test-reminder")
@login_required
def goal_send_test_reminder():
    """
    Sends a test goal reminder email to current user and returns sample popup data.
    """
    if current_user.is_admin:
        return jsonify({"success": False, "message": "Quản trị viên không áp dụng tính năng này."}), 400

    from .goal_reminder import check_user_goal_reminder_alert, send_daily_goal_reminders
    result = send_daily_goal_reminders(force=True, target_user_id=current_user.id)
    alert = check_user_goal_reminder_alert(current_user, force_hour=21)

    return jsonify({
        "success": True,
        "message": f"Đã gửi email nhắc nhở thử nghiệm tới {current_user.email}!",
        "result": result,
        "sample_alert": alert,
    })


# ==========================================
# GRAMMAR LEARNING ROUTES
# ==========================================

