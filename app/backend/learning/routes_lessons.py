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


@bp.get("/lessons")
@login_required
def lessons():
    level = request.args.get("level", "").strip()
    raw_skill = request.args.get("skill", "All").strip()
    status = request.args.get("status", "").strip()
    sort = request.args.get("sort", "").strip()
    accent = request.args.get("accent", "").strip()
    search = (request.args.get("search") or request.args.get("q") or "").strip()
    q = search

    # Validate and normalize skill
    valid_skills = ["All", "Listening", "Reading", "Speaking", "Writing"]
    matched_skill = next((s for s in valid_skills if s.lower() == raw_skill.lower()), None)
    if matched_skill:
        current_skill = matched_skill
    elif raw_skill in ["Vocabulary", "Grammar"]:
        current_skill = raw_skill
    else:
        current_skill = "All"

    all_lessons = Lesson.query.filter_by(is_active=True).order_by(Lesson.level, Lesson.id).all()
    user_progress_list = LessonProgress.query.filter_by(user_id=current_user.id).all()
    done = {p.lesson_id for p in user_progress_list}
    favorites = LessonFavorite.query.filter_by(user_id=current_user.id).all()
    favorite_ids = {f.lesson_id for f in favorites}

    # Skill counts for tab badges
    skill_counts = {
        "All": len(all_lessons),
        "Listening": sum(1 for l in all_lessons if l.skill == "Listening"),
        "Reading": sum(1 for l in all_lessons if l.skill == "Reading"),
        "Speaking": sum(1 for l in all_lessons if l.skill == "Speaking"),
        "Writing": sum(1 for l in all_lessons if l.skill == "Writing"),
    }

    # Scoped stats for current active skill
    if current_skill == "All":
        scoped_lessons = all_lessons
    else:
        scoped_lessons = [l for l in all_lessons if l.skill == current_skill]

    scoped_total = len(scoped_lessons)
    scoped_completed = sum(1 for l in scoped_lessons if l.id in done)
    scoped_in_progress = max(0, scoped_total - scoped_completed)
    scoped_favorites = sum(1 for l in scoped_lessons if l.id in favorite_ids)
    scoped_completion_rate = round((scoped_completed / scoped_total * 100)) if scoped_total > 0 else 0

    statistics = {
        "total": scoped_total,
        "completed": scoped_completed,
        "in_progress": scoped_in_progress,
        "favorite_count": scoped_favorites,
        "completion_rate": scoped_completion_rate,
        "audio_minutes": scoped_completed * 5 if current_skill == "Listening" else 0
    }

    # Hero Banner Configurations
    hero_configs = {
        "All": {
            "title": "Thư viện Bài học",
            "subtitle": "Khám phá và luyện tập tất cả các kỹ năng tiếng Anh trong một thư viện học tập thống nhất.",
            "badge": "LỘ TRÌNH BÀI HỌC TOÀN DIỆN",
            "icon": "ph-bold ph-graduation-cap",
            "gradient": "linear-gradient(135deg, #065f46 0%, #047857 50%, #059669 100%)",
            "card_class": "hero-all",
            "stat_label_3": "Tiến độ chung",
            "stat_val_3": f"{scoped_completion_rate}%",
            "stat_icon_3": "ph-bold ph-chart-donut",
            "stat_color_3": "text-info",
            "stat_label_4": "Yêu thích",
            "stat_val_4": f"{scoped_favorites} bài",
            "stat_icon_4": "ph-bold ph-heart",
            "stat_color_4": "text-danger"
        },
        "Listening": {
            "title": "Luyện Nghe",
            "subtitle": "Cải thiện khả năng nghe hiểu thông qua hội thoại, thông báo, podcast và các bài nghe theo cấp độ.",
            "badge": "KỸ NĂNG NGHE HIỂU · LISTENING",
            "icon": "ph-bold ph-headphones",
            "gradient": "linear-gradient(135deg, #312e81 0%, #4338ca 50%, #6366f1 100%)",
            "card_class": "hero-listening",
            "stat_label_3": "Tỷ lệ hoàn thành",
            "stat_val_3": f"{scoped_completion_rate}%",
            "stat_icon_3": "ph-bold ph-chart-line-up",
            "stat_color_3": "text-info",
            "stat_label_4": "Thời lượng audio đã học",
            "stat_val_4": f"{scoped_completed * 5} phút",
            "stat_icon_4": "ph-bold ph-clock",
            "stat_color_4": "text-warning"
        },
        "Reading": {
            "title": "Đọc hiểu",
            "subtitle": "Phát triển khả năng đọc hiểu thông qua các đoạn văn, email, bài báo và nội dung theo cấp độ CEFR.",
            "badge": "KỸ NĂNG ĐỌC HIỂU · READING",
            "icon": "ph-bold ph-book-open-text",
            "gradient": "linear-gradient(135deg, #0f766e 0%, #0d9488 50%, #14b8a6 100%)",
            "card_class": "hero-reading",
            "stat_label_3": "Tỷ lệ hoàn thành",
            "stat_val_3": f"{scoped_completion_rate}%",
            "stat_icon_3": "ph-bold ph-chart-line-up",
            "stat_color_3": "text-info",
            "stat_label_4": "Thời gian đọc tích lũy",
            "stat_val_4": f"{scoped_completed * 4} phút",
            "stat_icon_4": "ph-bold ph-clock",
            "stat_color_4": "text-warning"
        },
        "Speaking": {
            "title": "Luyện Nói",
            "subtitle": "Luyện giao tiếp, phát âm, ngữ điệu và phản xạ tiếng Anh thông qua các tình huống thực tế.",
            "badge": "KỸ NĂNG GIAO TIẾP & NÓI · SPEAKING",
            "icon": "ph-bold ph-chats-circle",
            "gradient": "linear-gradient(135deg, #9a3412 0%, #c2410c 50%, #ea580c 100%)",
            "card_class": "hero-speaking",
            "stat_label_3": "Tỷ lệ hoàn thành",
            "stat_val_3": f"{scoped_completion_rate}%",
            "stat_icon_3": "ph-bold ph-chart-line-up",
            "stat_color_3": "text-info",
            "stat_label_4": "Thời lượng luyện nói",
            "stat_val_4": f"{scoped_completed * 5} phút",
            "stat_icon_4": "ph-bold ph-microphone",
            "stat_color_4": "text-warning"
        },
        "Writing": {
            "title": "Luyện Viết",
            "subtitle": "Rèn luyện khả năng viết câu, đoạn văn, email và các nội dung tiếng Anh theo chủ đề.",
            "badge": "KỸ NĂNG VIẾT ỨNG DỤNG · WRITING",
            "icon": "ph-bold ph-pen-nib",
            "gradient": "linear-gradient(135deg, #881337 0%, #be123c 50%, #e11d48 100%)",
            "card_class": "hero-writing",
            "stat_label_3": "Tỷ lệ hoàn thành",
            "stat_val_3": f"{scoped_completion_rate}%",
            "stat_icon_3": "ph-bold ph-chart-line-up",
            "stat_color_3": "text-info",
            "stat_label_4": "Số từ đã thực hành",
            "stat_val_4": f"{scoped_completed * 120} từ",
            "stat_icon_4": "ph-bold ph-pencil-line",
            "stat_color_4": "text-warning"
        }
    }
    hero = hero_configs.get(current_skill, hero_configs["All"])

    # Level progress breakdown (A1-C2)
    levels = ["A1", "A2", "B1", "B2", "C1", "C2"]
    level_stats = []
    for lvl in levels:
        lvl_lessons = [l for l in scoped_lessons if l.level == lvl]
        lvl_total = len(lvl_lessons)
        lvl_done = sum(1 for l in lvl_lessons if l.id in done)
        lvl_pct = round((lvl_done / lvl_total * 100)) if lvl_total > 0 else 0
        level_stats.append({
            "level": lvl,
            "total": lvl_total,
            "done": lvl_done,
            "pct": lvl_pct
        })

    # Backward compatibility skill_stats
    skill_stats = []
    for sk in ["Vocabulary", "Grammar", "Reading", "Listening", "Speaking", "Writing"]:
        sk_lessons = [l for l in all_lessons if l.skill == sk]
        sk_total = len(sk_lessons)
        sk_done = sum(1 for l in sk_lessons if l.id in done)
        sk_pct = round((sk_done / sk_total * 100)) if sk_total > 0 else 0
        skill_stats.append({
            "skill": sk,
            "total": sk_total,
            "done": sk_done,
            "pct": sk_pct
        })

    # Filtered query for lesson display
    query = Lesson.query.filter_by(is_active=True)
    if current_skill != "All":
        query = query.filter_by(skill=current_skill)
    if level and level in levels:
        query = query.filter_by(level=level)
    if search:
        query = query.filter(
            Lesson.title.ilike(f"%{search}%") | 
            Lesson.short_description.ilike(f"%{search}%") | 
            Lesson.content.ilike(f"%{search}%")
        )

    lessons_list = query.all()

    # Assign accent and audio duration for listening lessons
    duration_pool = ["02:15", "02:45", "03:10", "03:35", "04:15", "04:50"]
    for idx, l in enumerate(lessons_list):
        if l.skill == "Listening":
            l.accent = "UK" if (l.id % 2 == 0) else "US"
            l.audio_duration = duration_pool[l.id % len(duration_pool)]

    if current_skill == "Listening" and accent in ["US", "UK"]:
        lessons_list = [l for l in lessons_list if getattr(l, "accent", "US") == accent]

    # Filter by status
    if status == "completed":
        lessons_list = [l for l in lessons_list if l.id in done]
    elif status in ["new", "not_started"]:
        lessons_list = [l for l in lessons_list if l.id not in done]
    elif status == "favorite":
        lessons_list = [l for l in lessons_list if l.id in favorite_ids]

    # Recommended next lesson (based on filtered list if available, else scoped lessons)
    recommended_pool = lessons_list if lessons_list else scoped_lessons
    recommended_lesson = None
    for l in recommended_pool:
        if l.id not in done:
            recommended_lesson = l
            break
    if not recommended_lesson and recommended_pool:
        recommended_lesson = recommended_pool[0]

    # Sorting
    level_rank = {"A1": 1, "A2": 2, "B1": 3, "B2": 4, "C1": 5, "C2": 6}
    if sort == "popularity":
        lessons_list.sort(key=lambda l: (l.view_count or 0), reverse=True)
    elif sort == "difficulty_asc":
        lessons_list.sort(key=lambda l: (level_rank.get(l.level, 99), l.id))
    elif sort == "difficulty_desc":
        lessons_list.sort(key=lambda l: (level_rank.get(l.level, 99), l.id), reverse=True)
    elif sort == "recent":
        lessons_list.sort(key=lambda l: (l.created_at or datetime.min), reverse=True)
    else:
        lessons_list.sort(key=lambda l: (level_rank.get(l.level, 99), l.id))

    # Daily lesson goal
    today_date = date.today()
    today_completed_lessons = sum(1 for p in user_progress_list if p.completed_at and p.completed_at.date() == today_date)
    daily_lesson_goal = 2
    daily_goal_pct = min(100, round((today_completed_lessons / daily_lesson_goal * 100))) if daily_lesson_goal > 0 else 0

    return render_template(
        "learning/lessons.html",
        lessons=lessons_list,
        current_skill=current_skill,
        skill=current_skill if current_skill != "All" else "",
        skill_param=current_skill,
        level=level,
        status=status,
        accent=accent,
        sort=sort,
        search=search,
        q=q,
        done=done,
        progress_map={p.lesson_id: p for p in user_progress_list},
        favorite_ids=favorite_ids,
        skill_counts=skill_counts,
        statistics=statistics,
        hero=hero,
        total_lessons=scoped_total,
        completed_count=scoped_completed,
        in_progress_count=scoped_in_progress,
        level_stats=level_stats,
        skill_stats=skill_stats,
        recommended_lesson=recommended_lesson,
        today_completed_lessons=today_completed_lessons,
        daily_lesson_goal=daily_lesson_goal,
        daily_goal_pct=daily_goal_pct,
        form=ActionForm()
    )


@bp.post("/lessons/<int:lesson_id>/favorite")
@login_required
def favorite_lesson(lesson_id):
    lesson = Lesson.query.filter_by(id=lesson_id, is_active=True).first_or_404()
    fav = LessonFavorite.query.filter_by(user_id=current_user.id, lesson_id=lesson.id).first()
    if fav:
        db.session.delete(fav)
        db.session.commit()
        is_fav = False
        msg = "Đã bỏ bài học khỏi danh sách yêu thích."
    else:
        db.session.add(LessonFavorite(user_id=current_user.id, lesson_id=lesson.id))
        db.session.commit()
        is_fav = True
        msg = "Đã thêm bài học vào danh sách yêu thích!"

    if request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"success": True, "is_favorite": is_fav, "message": msg})

    flash(msg, "success" if is_fav else "info")
    return redirect(request.referrer or url_for("learning.lessons"))


@bp.get("/lessons/<int:lesson_id>/preview")
@login_required
def preview_lesson(lesson_id):
    lesson = Lesson.query.filter_by(id=lesson_id, is_active=True).first_or_404()
    is_done = LessonProgress.query.filter_by(user_id=current_user.id, lesson_id=lesson.id).first() is not None
    is_fav = LessonFavorite.query.filter_by(user_id=current_user.id, lesson_id=lesson.id).first() is not None
    return jsonify({
        "id": lesson.id,
        "title": lesson.title,
        "level": lesson.level,
        "skill": lesson.skill,
        "url": lesson.url,
        "short_description": lesson.short_description,
        "examples": lesson.examples,
        "content_preview": (lesson.content[:200] + "...") if lesson.content and len(lesson.content) > 200 else lesson.content,
        "view_count": lesson.view_count or 0,
        "is_done": is_done,
        "is_favorite": is_fav
    })


def _render_lesson_page(lesson):
    lesson.view_count = (lesson.view_count or 0) + 1
    db.session.commit()

    # Listening specific properties
    transcript_lines = []
    sd = getattr(lesson, "skill_data", None) or {}
    if lesson.skill == "Listening":
        lesson.accent = sd.get("accent") or ("UK" if (lesson.id % 2 == 0) else "US")
        duration_pool = ["02:15", "02:45", "03:10", "03:35", "04:15", "04:50"]
        lesson.audio_duration = sd.get("audio_duration") or duration_pool[lesson.id % len(duration_pool)]
        lesson.audio_url = getattr(lesson, "audio_url", None) or sd.get("audio_url") or ""
        lesson.audio_url_uk = getattr(lesson, "audio_url_uk", None) or sd.get("audio_url_uk") or ""

        raw_source = sd.get("transcript") or lesson.examples or lesson.content or ""
        lines = [l.strip() for l in raw_source.splitlines() if l.strip()]
        for idx, line in enumerate(lines):
            speaker = None
            text = line
            if ":" in line:
                parts = line.split(":", 1)
                if len(parts[0]) <= 25 and not parts[0].startswith("http"):
                    speaker = parts[0].strip()
                    text = parts[1].strip()
            transcript_lines.append({
                "index": idx + 1,
                "speaker": speaker,
                "text": text,
                "full_line": line
            })

    # Reading specific properties
    reading_passage = ""
    reading_guideline = ""
    reading_paragraphs = []
    reading_vocab = []
    reading_questions = []

    if lesson.skill == "Reading":
        if sd.get("passage"):
            reading_passage = sd.get("passage").strip()
            reading_guideline = lesson.content.strip() if lesson.content else ""
        elif lesson.examples and len(lesson.examples.strip()) > 30:
            reading_passage = lesson.examples.strip()
            reading_guideline = lesson.content.strip() if lesson.content else ""
        else:
            reading_passage = lesson.content.strip() if lesson.content else ""
            reading_guideline = ""

        reading_paragraphs = [p.strip() for p in reading_passage.split("\n\n") if p.strip()]
        if not reading_paragraphs:
            reading_paragraphs = [p.strip() for p in reading_passage.split("\n") if p.strip()]
        if not reading_paragraphs:
            reading_paragraphs = [reading_passage]

        READING_DATA = {
            18: {
                "genre": "Bưu thiếp (Postcard)",
                "est_minutes": 2,
                "vocab": [
                    {"word": "postcard", "ipa": "/ˈpoʊst.kɑːrd/", "pos": "noun", "vi": "bưu thiếp", "ex": "She sent me a postcard from Paris."},
                    {"word": "weather", "ipa": "/ˈweð.ɚ/", "pos": "noun", "vi": "thời tiết", "ex": "The weather is sunny and warm today."},
                    {"word": "visit", "ipa": "/ˈvɪz.ɪt/", "pos": "verb", "vi": "thăm quan, ghé thăm", "ex": "We visited the museum yesterday."},
                    {"word": "lovely", "ipa": "/ˈlʌv.li/", "pos": "adjective", "vi": "dễ thương, tuyệt vời", "ex": "They had a lovely time in London."}
                ],
                "questions": [
                    {
                        "id": 1,
                        "question": "Where is the sender writing the postcard from?",
                        "options": ["Paris", "London", "Tokyo", "New York"],
                        "answer": 1,
                        "explanation": "Trong bài viết: 'Greetings from London!' cho biết người gửi đang ở London."
                    },
                    {
                        "id": 2,
                        "question": "Which famous landmark did the author visit?",
                        "options": ["Eiffel Tower", "Big Ben", "Statue of Liberty", "Colosseum"],
                        "answer": 1,
                        "explanation": "Đoạn trích: 'We visited Big Ben and rode the London Eye'."
                    }
                ]
            },
            19: {
                "genre": "Thông tin khách sạn (Brochure)",
                "est_minutes": 3,
                "vocab": [
                    {"word": "breakfast", "ipa": "/ˈbrek.fəst/", "pos": "noun", "vi": "bữa sáng", "ex": "Breakfast is served from 6:30 to 10:00 AM on the 2nd floor."},
                    {"word": "available", "ipa": "/əˈveɪ.lə.bəl/", "pos": "adjective", "vi": "có sẵn, sử dụng được", "ex": "Free Wi-Fi is available across all rooms."},
                    {"word": "check-out", "ipa": "/ˈtʃek.aʊt/", "pos": "noun", "vi": "thời gian trả phòng", "ex": "Check-out time is before 11:00 AM."},
                    {"word": "floor", "ipa": "/flɔːr/", "pos": "noun", "vi": "tầng lầu", "ex": "The dining room is on the 2nd floor."}
                ],
                "questions": [
                    {
                        "id": 1,
                        "question": "Where is breakfast served in the hotel?",
                        "options": ["In the lobby", "On the 2nd floor", "On the rooftop", "In room service only"],
                        "answer": 1,
                        "explanation": "Nội dung chỉ rõ: 'Breakfast is served from 6:30 to 10:00 AM on the 2nd floor'."
                    },
                    {
                        "id": 2,
                        "question": "Is Wi-Fi free for all guests in their rooms?",
                        "options": ["Yes, it is free across all rooms", "No, it costs $10/day", "Only in the lobby", "Only for VIP guests"],
                        "answer": 0,
                        "explanation": "Nội dung: 'Free Wi-Fi is available across all rooms'."
                    }
                ]
            },
            20: {
                "genre": "Bài viết lối sống (Lifestyle Essay)",
                "est_minutes": 3,
                "vocab": [
                    {"word": "minimalism", "ipa": "/ˈmɪn.ə.məl.ɪ.zəm/", "pos": "noun", "vi": "chủ nghĩa tối giản", "ex": "Minimalism helps reduce daily stress."},
                    {"word": "matter", "ipa": "/ˈmæt̬.ɚ/", "pos": "verb", "vi": "có ý nghĩa, quan trọng", "ex": "Family is what truly matters."},
                    {"word": "skimming", "ipa": "/ˈskɪm.ɪŋ/", "pos": "noun", "vi": "kỹ năng đọc lướt", "ex": "Skimming allows you to find key ideas fast."}
                ],
                "questions": [
                    {
                        "id": 1,
                        "question": "What is the core philosophy of minimalism according to the text?",
                        "options": ["Owning absolutely nothing", "Making room for what truly matters", "Selling all possessions", "Living without technology"],
                        "answer": 1,
                        "explanation": "Bài đọc nêu rõ: 'Minimalism is not about owning nothing; it is about making room for what truly matters'."
                    }
                ]
            },
            21: {
                "genre": "Email công việc (Workplace Email)",
                "est_minutes": 4,
                "vocab": [
                    {"word": "schedule", "ipa": "/ˈskedʒ.uːl/", "pos": "noun", "vi": "tiến độ, lịch trình", "ex": "The release schedule is on track."},
                    {"word": "milestone", "ipa": "/ˈmaɪl.stoʊn/", "pos": "noun", "vi": "cột mốc dự án", "ex": "Please find the revised milestones attached."},
                    {"word": "attachment", "ipa": "/əˈtætʃ.mənt/", "pos": "noun", "vi": "tệp đính kèm", "ex": "Please review the attachment."}
                ],
                "questions": [
                    {
                        "id": 1,
                        "question": "What is the primary purpose of the email?",
                        "options": ["Requesting vacation leave", "Providing an update on the product release schedule", "Complaining about customer service", "Announcing office relocation"],
                        "answer": 1,
                        "explanation": "Câu mở đầu: 'I am writing to provide an update regarding the Q3 product release schedule'."
                    }
                ]
            },
            22: {
                "genre": "Bài báo học thuật (Academic Article)",
                "est_minutes": 5,
                "vocab": [
                    {"word": "circular economy", "ipa": "/ˌsɝː.kjə.lɚ iˈkɑː.nə.mi/", "pos": "noun", "vi": "kinh tế tuần hoàn", "ex": "The circular economy reduces industrial waste."},
                    {"word": "paradigm", "ipa": "/ˈper.ə.daɪm/", "pos": "noun", "vi": "mô hình, khuôn mẫu tư duy", "ex": "A major paradigm shift is taking place."},
                    {"word": "cross-sectoral", "ipa": "/ˌkrɑːs.sekˈtɔːr.i.əl/", "pos": "adj", "vi": "liên ngành, đa lĩnh vực", "ex": "Cross-sectoral cooperation is vital."}
                ],
                "questions": [
                    {
                        "id": 1,
                        "question": "What is required to transition towards a circular economy paradigm?",
                        "options": ["Individual effort only", "Cross-sectoral collaboration between policymakers and municipalities", "Stopping all technological development", "Increasing fossil fuel usage"],
                        "answer": 1,
                        "explanation": "Văn bản nêu: 'Transitioning towards circular economy paradigms requires cross-sectoral collaboration'."
                    }
                ]
            }
        }

        if sd.get("questions") or sd.get("reading_genre"):
            reading_info = {
                "genre": sd.get("reading_genre") or "Bài đọc",
                "est_minutes": max(1, len(reading_passage) // 250 + 1),
                "vocab": sd.get("vocab", []),
                "questions": sd.get("questions", [])
            }
        else:
            reading_info = READING_DATA.get(lesson.id, {
                "genre": "Bài đọc thực hành",
                "est_minutes": max(1, len(reading_passage) // 250 + 1),
                "vocab": [
                    {"word": "comprehension", "ipa": "/ˌkɑːm.prəˈhen.ʃən/", "pos": "noun", "vi": "sự đọc hiểu", "ex": "Reading daily improves language comprehension."},
                    {"word": "context", "ipa": "/ˈkɑːn.tekst/", "pos": "noun", "vi": "ngữ cảnh", "ex": "Always observe words in their natural context."}
                ],
                "questions": [
                    {
                        "id": 1,
                        "question": f"What is the main topic of '{lesson.title}'?",
                        "options": [lesson.title, "Grammar review", "Speaking dialogue", "Listening audio"],
                        "answer": 0,
                        "explanation": f"Nội dung bài học hướng dẫn trọng tâm về: {lesson.title}."
                    }
                ]
            })
        reading_vocab = reading_info.get("vocab", [])
        reading_questions = reading_info.get("questions", [])
        lesson.reading_genre = reading_info.get("genre", "Bài đọc")
        lesson.est_minutes = reading_info.get("est_minutes", 3)

    # Writing specific properties
    writing_prompt = ""
    writing_target_min = 40
    writing_target_max = 80
    writing_templates = []
    writing_model = ""

    if lesson.skill == "Writing":
        writing_prompt = lesson.content.strip() if lesson.content else ""
        writing_model = lesson.examples.strip() if lesson.examples else ""

        WRITING_DATA = {
            28: {
                "genre": "Ghi chú thường ngày (Routine Note)",
                "target_min": 30,
                "target_max": 60,
                "templates": [
                    {"label": "Bắt đầu ngày mới", "text": "First, I wake up at 7:00 AM and wash my face.", "vi": "Đầu tiên, tôi thức dậy lúc 7:00 sáng và rửa mặt."},
                    {"label": "Hoạt động tiếp theo", "text": "Then, I have breakfast with my family.", "vi": "Sau đó, tôi ăn sáng cùng gia đình."},
                    {"label": "Buổi chiều", "text": "After that, I study English on EnglishMate.", "vi": "Sau đó, tôi học tiếng Anh trên EnglishMate."},
                    {"label": "Kết thúc ngày", "text": "Finally, I go to bed at 10:30 PM.", "vi": "Cuối cùng, tôi đi ngủ lúc 10:30 tối."}
                ]
            },
            29: {
                "genre": "Tin nhắn mời dự tiệc (Invitation)",
                "target_min": 40,
                "target_max": 75,
                "templates": [
                    {"label": "Lời chào & Lý do", "text": "I would like to invite you to my birthday party.", "vi": "Mình muốn mời bạn đến dự tiệc sinh nhật của mình."},
                    {"label": "Thời gian & Địa điểm", "text": "The party is this Saturday at 7:00 PM at Bistro Garden.", "vi": "Bữa tiệc diễn ra vào tối thứ Bảy này lúc 7:00 tại Bistro Garden."},
                    {"label": "Xác nhận tham gia", "text": "Please let me know by Friday if you can come.", "vi": "Vui lòng báo lại cho mình trước thứ Sáu nếu bạn có thể tham gia nhé."},
                    {"label": "Lời kết thân mật", "text": "Hope to see you there! Best regards.", "vi": "Rất mong gặp bạn ở đó! Thân ái."}
                ]
            },
            30: {
                "genre": "Email du lịch thân mật (Holiday Email)",
                "target_min": 60,
                "target_max": 110,
                "templates": [
                    {"label": "Mở đầu email", "text": "I hope you are doing well! I'm writing to tell you about my trip.", "vi": "Hy vọng bạn vẫn khỏe! Mình viết thư để kể về chuyến đi của mình."},
                    {"label": "Kể lại trải nghiệm", "text": "While we were walking along the beach, we witnessed a stunning sunset.", "vi": "Khi chúng tôi đang đi dạo dọc bờ biển, chúng tôi đã ngắm một hoàng hôn tuyệt đẹp."},
                    {"label": "Cảm xúc chung", "text": "We had an amazing time exploring the local cuisine and night market.", "vi": "Chúng tôi đã có khoảng thời gian tuyệt vời khám phá ẩm thực và chợ đêm."},
                    {"label": "Hẹn gặp lại", "text": "I can't wait to catch up soon and show you all the photos!", "vi": "Mình rất nóng lòng sớm gặp bạn để khoe các bức ảnh!"}
                ]
            },
            31: {
                "genre": "Thư khiếu nại / Yêu cầu trang trọng (Business Letter)",
                "target_min": 80,
                "target_max": 150,
                "templates": [
                    {"label": "Mục đích thư", "text": "I am writing to formally request an expedited review of application reference #89412.", "vi": "Tôi viết thư này để chính thức yêu cầu đẩy nhanh tiến độ xem xét hồ sơ số #89412."},
                    {"label": "Nêu nguyên nhân", "text": "Due to urgent project deadlines, timely approval is critical for our operations.", "vi": "Do thời hạn dự án khẩn cấp, việc phê duyệt kịp thời mang tính quyết định cho hoạt động của chúng tôi."},
                    {"label": "Yêu cầu hành động", "text": "I would greatly appreciate it if you could confirm receipt of this request.", "vi": "Tôi rất cảm kích nếu quý bên có thể xác nhận đã tiếp nhận yêu cầu này."},
                    {"label": "Lời chào trang trọng", "text": "Thank you for your prompt attention to this matter. Sincerely yours.", "vi": "Cảm ơn quý bên đã nhanh chóng chú ý đến vấn đề này. Trân trọng."}
                ]
            },
            32: {
                "genre": "Bài luận học thuật (Persuasive Essay)",
                "target_min": 120,
                "target_max": 200,
                "templates": [
                    {"label": "Luận điểm chính (Thesis)", "text": "It is widely acknowledged that technological innovation reshapes modern workforce dynamics.", "vi": "Một điều được công nhận rộng rãi là sự đổi mới công nghệ đang định hình lại lực lượng lao động hiện đại."},
                    {"label": "Phản biện (Counter-argument)", "text": "Proponents argue that automation increases efficiency; however, this overlooks displacement issues.", "vi": "Những người ủng hộ cho rằng tự động hóa nâng cao hiệu quả; tuy nhiên, điều này bỏ qua vấn đề sa thải lao động."},
                    {"label": "Dẫn chứng phân tích", "text": "Recent empirical studies substantiate the necessity of proactive retraining programs.", "vi": "Các nghiên cứu thực nghiệm gần đây chứng minh tính cần thiết của các chương trình đào tạo lại chủ động."},
                    {"label": "Kết luận đúc kết", "text": "In conclusion, a nuanced policy balance is essential for long-term sustainable growth.", "vi": "Tóm lại, sự cân bằng chính sách tinh tế là điều thiết yếu cho sự tăng trưởng bền vững lâu dài."}
                ]
            }
        }

        if sd.get("writing_genre") or sd.get("min_words") or sd.get("templates"):
            writing_info = {
                "genre": sd.get("writing_genre") or "Bài viết thực hành",
                "target_min": sd.get("min_words", 40),
                "target_max": sd.get("max_words", 80),
                "templates": sd.get("templates", [])
            }
        else:
            writing_info = WRITING_DATA.get(lesson.id, {
                "genre": "Bài viết thực hành",
                "target_min": 40,
                "target_max": 80,
                "templates": [
                    {"label": "Mở đầu", "text": "First, I would like to express my thoughts on this topic.", "vi": "Đầu tiên, tôi muốn chia sẻ suy nghĩ về chủ đề này."},
                    {"label": "Phát triển ý", "text": "Furthermore, there are several key reasons to consider.", "vi": "Hơn nữa, có một số lý do quan trọng cần xem xét."},
                    {"label": "Kết bài", "text": "In conclusion, practicing writing regularly brings noticeable progress.", "vi": "Tóm lại, luyện viết thường xuyên đem lại tiến bộ rõ rệt."}
                ]
            })

        lesson.writing_genre = writing_info.get("genre", "Bài viết")
        lesson.target_min = writing_info.get("target_min", 40)
        lesson.target_max = writing_info.get("target_max", 80)
        writing_target_min = lesson.target_min
        writing_target_max = lesson.target_max
        writing_templates = writing_info.get("templates", [])

    # Speaking specific properties
    speaking_context = ""
    speaking_sentences = []
    speaking_tips = []

    if lesson.skill == "Speaking":
        speaking_context = lesson.content.strip() if lesson.content else ""

        SPEAKING_DATA = {
            23: {
                "genre": "Giới thiệu bản thân (Self-Introduction)",
                "sentences": [
                    {"idx": 1, "text": "Hi everyone, my name is Alex.", "ipa": "/haɪ ˈev.ri.wʌn maɪ neɪm ɪz ˈæl.ɪks/", "vi": "Xin chào mọi người, mình tên là Alex."},
                    {"idx": 2, "text": "I am from Da Nang and I work as a web developer.", "ipa": "/aɪ æm frɑːm đà nẵng ænd aɪ wɜːrk æz ə web dɪˈvel.ə.pɚ/", "vi": "Mình đến từ Đà Nẵng và mình làm lập trình viên web."},
                    {"idx": 3, "text": "In my free time, I love playing badminton.", "ipa": "/ɪn maɪ friː taɪm aɪ lʌv ˈpleɪ.ɪŋ ˈbæd.mɪn.tən/", "vi": "Vào thời gian rảnh, mình rất thích chơi cầu lông."},
                    {"idx": 4, "text": "I am excited to learn English with all of you.", "ipa": "/aɪ æm ɪkˈsaɪ.tɪd tuː lɜːrn ˈɪŋ.ɡlɪʃ wɪð ɔːl əv juː/", "vi": "Mình rất hào hứng được học tiếng Anh cùng các bạn."}
                ],
                "tips": [
                    "Cười nhẹ và giữ ánh mắt tự tin (Eye contact) khi bắt đầu câu chào.",
                    "Lên giọng nhẹ ở cuối tên của bạn và hạ giọng ở cuối câu khẳng định.",
                    "Chú ý phát âm rõ âm cuối: /ks/ trong 'Alex', /mz/ trong 'everyone's'."
                ]
            },
            24: {
                "genre": "Hỏi & Chỉ đường (Directions)",
                "sentences": [
                    {"idx": 1, "text": "Excuse me, could you tell me where the nearest station is?", "ipa": "/ɪkˈskjuːz miː kʊd juː tel miː wer ðə ˈnɪr.ɪst ˈsteɪ.ʃən ɪz/", "vi": "Xin lỗi, bạn có thể chỉ giúp tôi nhà ga gần nhất ở đâu không?"},
                    {"idx": 2, "text": "Go straight for two blocks, then turn left at the traffic light.", "ipa": "/ɡoʊ streɪt fɔːr tuː blɑːks ðen tɜːrn left æt ðə ˈtræf.ɪk laɪt/", "vi": "Hãy đi thẳng hai dãy nhà, sau đó rẽ trái ở cột đèn giao thông."},
                    {"idx": 3, "text": "It is right opposite the supermarket on your right.", "ipa": "/ɪt ɪz raɪt ˈɑː.pə.zɪt ðə ˈsuː.pɚˌmɑːr.kɪt ɑːn jɔːr raɪt/", "vi": "Nó nằm ngay đối diện siêu thị ở phía bên tay phải của bạn."},
                    {"idx": 4, "text": "Thank you so much for your help! Have a great day.", "ipa": "/θæŋk juː soʊ mʌtʃ fɔːr jɔːr help hæv ə ɡreɪt deɪ/", "vi": "Cảm ơn bạn rất nhiều vì sự giúp đỡ! Chúc bạn một ngày tốt lành."}
                ],
                "tips": [
                    "Dùng ngữ điệu lịch sự (Polite tone) khi mở đầu bằng 'Excuse me'.",
                    "Nhấn mạnh các động từ chỉ phương hướng: 'Go straight', 'Turn left', 'Opposite'."
                ]
            },
            25: {
                "genre": "Bày tỏ quan điểm (Opinions)",
                "sentences": [
                    {"idx": 1, "text": "In my view, remote working offers better work-life balance.", "ipa": "/ɪn maɪ vjuː rɪˈmoʊt ˈwɜːr.kɪŋ ˈɑː.fɚz ˈbet̬.ɚ wɜːrk laɪf ˈbæl.əns/", "vi": "Theo quan điểm của tôi, làm việc từ xa đem lại sự cân bằng công việc - cuộc sống tốt hơn."},
                    {"idx": 2, "text": "For instance, employees save two hours of commuting daily.", "ipa": "/fɔːr ˈɪn.stəns ɪmˈplɔɪ.iːz seɪv tuː ˈaʊ.ɚz əv kəˈmjuː.tɪŋ ˈdeɪ.li/", "vi": "Chẳng hạn, nhân viên tiết kiệm được hai tiếng đi lại mỗi ngày."},
                    {"idx": 3, "text": "However, maintaining team connection requires deliberate effort.", "ipa": "/haʊˈev.ɚ meɪnˈteɪ.nɪŋ tiːm kəˈnek.ʃən rɪˈkwaɪ.ɚz dɪˈlɪb.ɚ.ət ˈef.ɚt/", "vi": "Tuy nhiên, việc duy trì gắn kết nhóm đòi hỏi nỗ lực có chủ đích."},
                    {"idx": 4, "text": "Overall, a hybrid model seems to be the most ideal solution.", "ipa": "/ˌoʊ.vɚˈɔːl ə ˈhaɪ.brɪd ˈmɑː.dəl siːmz tuː biː ðə moʊst aɪˈdiː.əl səˈluː.ʃən/", "vi": "Nhìn chung, mô hình làm việc kết hợp dường như là giải pháp lý tưởng nhất."}
                ],
                "tips": [
                    "Tạm dừng (Pause) 0.5s sau các cụm liên từ như 'In my view', 'For instance', 'However'.",
                    "Nhấn mạnh từ khóa trọng tâm: 'better balance', 'ideal solution'."
                ]
            },
            26: {
                "genre": "Phỏng vấn xin việc (Job Interview)",
                "sentences": [
                    {"idx": 1, "text": "I have over four years of experience leading product teams.", "ipa": "/aɪ hæv ˈoʊ.vɚ fɔːr jɪrz əv ɪkˈspɪr.i.əns ˈliː.dɪŋ ˈprɑː.dʌkt tiːmz/", "vi": "Tôi có hơn bốn năm kinh nghiệm dẫn dắt các đội ngũ sản phẩm."},
                    {"idx": 2, "text": "One of my greatest strengths is solving complex technical bottlenecks.", "ipa": "/wʌn əv maɪ ˈɡreɪ.tɪst streŋθs ɪz ˈsɑːl.vɪŋ kəmˈpleks ˈtek.nɪ.kəl ˈbɑː.t̬əl.neks/", "vi": "Một trong những thế mạnh lớn nhất của tôi là giải quyết các nút thắt kỹ thuật phức tạp."},
                    {"idx": 3, "text": "In my previous project, we increased user retention by twenty-five percent.", "ipa": "/ɪn maɪ ˈpriː.vi.əs ˈprɑː.dʒekt wiː ɪnˈkriːst ˈjuː.zɚ rɪˈten.ʃən baɪ ˈtwen.ti faɪv pɚˈsent/", "vi": "Trong dự án trước, chúng tôi đã tăng tỷ lệ giữ chân người dùng thêm 25%."},
                    {"idx": 4, "text": "I am passionate about contributing to your company's mission.", "ipa": "/aɪ æm ˈpæʃ.ən.ət əˈbaʊt kənˈtrɪb.juː.tɪŋ tuː jɔːr ˈkʌm.pə.niz ˈmɪʃ.ən/", "vi": "Tôi rất nhiệt huyết được đóng góp vào sứ mệnh của công ty bạn."}
                ],
                "tips": [
                    "Sử dụng kỹ thuật STAR: Trình bày súc tích, tự tin, không ngập ngừng.",
                    "Phát âm chuẩn xác các số liệu phần trăm: 'twenty-five percent'."
                ]
            },
            27: {
                "genre": "Đàm phán thương mại (Negotiation)",
                "sentences": [
                    {"idx": 1, "text": "While we appreciate your proposal, we require greater payment flexibility.", "ipa": "/waɪl wiː əˈpriː.ʃi.eɪt jɔːr prəˈpoʊ.zəl wiː rɪˈkwaɪ.ɚ ˈɡreɪ.t̬ɚ ˈpeɪ.mənt ˌflek.səˈbɪl.ə.t̬i/", "vi": "Dù đánh giá cao đề xuất của quý bên, chúng tôi cần sự linh hoạt hơn về tiến độ thanh toán."},
                    {"idx": 2, "text": "Could you consider adjusting the delivery milestones to Q3?", "ipa": "/kʊd juː kənˈsɪd.ɚ əˈdʒʌs.tɪŋ ðə dɪˈlɪv.ɚ.i ˈmaɪl.stoʊnz tuː kjuː θriː/", "vi": "Quý bên có thể cân nhắc điều chỉnh các mốc bàn giao sang quý 3 được không?"},
                    {"idx": 3, "text": "If you can meet us on the pricing, we are ready to commit today.", "ipa": "/ɪf juː kæn miːt ʌs ɑːn ðə ˈpraɪ.sɪŋ wiː ɑːr ˈred.i tuː kəˈmɪt təˈdeɪ/", "vi": "Nếu quý bên có thể đáp ứng về mức giá, chúng tôi sẵn sàng ký cam kết ngay hôm nay."}
                ],
                "tips": [
                    "Sử dụng ngôn ngữ giảm nhẹ (Hedging language) để giữ hòa khí đàm phán.",
                    "Giữ âm điệu vững chãi, nhả chữ dứt khoát ở các cam kết quan trọng."
                ]
            }
        }

        if sd.get("speaking_genre") or sd.get("sentences"):
            speaking_info = {
                "genre": sd.get("speaking_genre") or "Giao tiếp thực hành",
                "sentences": sd.get("sentences", []),
                "tips": sd.get("tips", [])
            }
        else:
            speaking_info = SPEAKING_DATA.get(lesson.id, {
                "genre": "Giao tiếp thực hành",
                "sentences": [
                    {"idx": 1, "text": lesson.title, "ipa": "/prəˌnʌn.siˈeɪ.ʃən ˈpræk.tɪs/", "vi": f"Luyện tập phát âm chủ đề: {lesson.title}."},
                    {"idx": 2, "text": (lesson.examples or "Practice speaking clearly and naturally every day.").splitlines()[0], "ipa": "/ˈpræk.tɪs ˈspiː.kɪŋ ˈklɪr.li ænd ˈnætʃ.ɚ.əl.i/", "vi": "Luyện nói rõ ràng và tự nhiên mỗi ngày."}
                ],
                "tips": [
                    "Giữ hơi thở đều đặn và thả lỏng cơ miệng khi phát âm.",
                    "Nghe mẫu nhiều lần trước khi bấm thu âm để bắt chước ngữ điệu chuẩn."
                ]
            })

        lesson.speaking_genre = speaking_info.get("genre", "Luyện nói")
        speaking_sentences = speaking_info.get("sentences", [])
        speaking_tips = speaking_info.get("tips", [])

    completed = LessonProgress.query.filter_by(user_id=current_user.id, lesson_id=lesson.id).first()
    note_record = LessonNote.query.filter_by(user_id=current_user.id, lesson_id=lesson.id).first()
    bookmarks = [b.section_index for b in LessonBookmark.query.filter_by(user_id=current_user.id, lesson_id=lesson.id).all()]
    is_favorite = LessonFavorite.query.filter_by(user_id=current_user.id, lesson_id=lesson.id).first() is not None
    user_rating = LessonRating.query.filter_by(user_id=current_user.id, lesson_id=lesson.id).first()
    rating_distribution = lesson.get_rating_distribution()
    recent_ratings = LessonRating.query.filter_by(lesson_id=lesson.id).order_by(LessonRating.created_at.desc()).limit(10).all()
    user_annotations = []
    if current_user.is_authenticated and lesson.skill == "Reading":
        user_annotations = ReadingAnnotation.query.filter_by(
            user_id=current_user.id, lesson_id=lesson.id
        ).order_by(ReadingAnnotation.created_at.asc()).all()

    user_writing_submission = None
    if current_user.is_authenticated and lesson.skill == "Writing":
        user_writing_submission = WritingSubmission.query.filter_by(
            user_id=current_user.id, lesson_id=lesson.id
        ).order_by(WritingSubmission.updated_at.desc()).first()

    return render_template(
        "learning/lesson_detail.html",
        lesson=lesson,
        transcript_lines=transcript_lines,
        reading_passage=reading_passage,
        reading_guideline=reading_guideline,
        reading_paragraphs=reading_paragraphs,
        reading_vocab=reading_vocab,
        reading_questions=reading_questions,
        user_annotations=user_annotations,
        writing_prompt=writing_prompt,
        writing_model=writing_model,
        writing_templates=writing_templates,
        writing_target_min=writing_target_min,
        writing_target_max=writing_target_max,
        user_writing_submission=user_writing_submission,
        speaking_context=speaking_context,
        speaking_sentences=speaking_sentences,
        speaking_tips=speaking_tips,
        completed=completed,
        user_note=note_record.content if note_record else "",
        bookmarks=bookmarks,
        is_favorite=is_favorite,
        user_rating=user_rating,
        rating_distribution=rating_distribution,
        recent_ratings=recent_ratings,
        form=ActionForm()
    )


@bp.get("/listening/<int:lesson_id>")
@login_required
def listening_detail(lesson_id):
    lesson = Lesson.query.filter_by(id=lesson_id, is_active=True).first_or_404()
    return _render_lesson_page(lesson)


@bp.get("/reading/<int:lesson_id>")
@login_required
def reading_detail(lesson_id):
    lesson = Lesson.query.filter_by(id=lesson_id, is_active=True).first_or_404()
    return _render_lesson_page(lesson)


@bp.get("/speaking/<int:lesson_id>")
@login_required
def speaking_detail(lesson_id):
    lesson = Lesson.query.filter_by(id=lesson_id, is_active=True).first_or_404()
    return _render_lesson_page(lesson)


@bp.get("/writing/<int:lesson_id>")
@login_required
def writing_detail(lesson_id):
    lesson = Lesson.query.filter_by(id=lesson_id, is_active=True).first_or_404()
    return _render_lesson_page(lesson)


@bp.get("/lessons/<int:lesson_id>")
@login_required
def lesson_detail(lesson_id):
    lesson = Lesson.query.filter_by(id=lesson_id, is_active=True).first_or_404()
    skill_slug = (lesson.skill or "").lower()
    if skill_slug in ["listening", "reading", "speaking", "writing"]:
        return redirect(f"/{skill_slug}/{lesson.id}")
    return _render_lesson_page(lesson)


@bp.get("/listening")
@login_required
def listening_hub():
    return redirect(url_for("learning.lessons", skill="Listening"))


@bp.get("/reading")
@login_required
def reading_hub():
    return redirect(url_for("learning.lessons", skill="Reading"))


@bp.get("/speaking")
@login_required
def speaking_hub():
    return redirect(url_for("learning.lessons", skill="Speaking"))


@bp.get("/writing")
@login_required
def writing_hub():
    return redirect(url_for("learning.lessons", skill="Writing"))


@bp.post("/check-writing")
@bp.post("/lessons/check-writing")
@login_required
def check_writing():
    """
    Real-time writing grammar, spelling, and style correction endpoint.
    """
    data = request.get_json(silent=True) or request.form
    text = (data.get("text") or "").strip()
    result = check_grammar_and_spelling(text)
    return jsonify(result)


@bp.post("/writing/<int:lesson_id>/submit")
@bp.post("/lessons/<int:lesson_id>/writing/submit")
@login_required
def submit_writing_lesson(lesson_id):
    """
    Submits an essay written by learner, grades it with AI feedback engine,
    saves WritingSubmission, updates lesson progress, awards XP and returns detailed evaluation.
    """
    lesson = Lesson.query.filter_by(id=lesson_id, is_active=True).first_or_404()
    data = request.get_json(silent=True) or request.form
    essay_content = (data.get("content") or data.get("text") or "").strip()

    if not essay_content:
        if request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"status": "error", "message": "Nội dung bài viết không được để trống."}), 400
        flash("Vui lòng viết bài trước khi nộp!", "warning")
        return redirect(url_for("learning.lesson_detail", lesson_id=lesson.id))

    # Target limits
    skill_data = lesson.skill_data or {}
    target_min = int(skill_data.get("target_min") or skill_data.get("writing_target_min") or 40)
    target_max = int(skill_data.get("target_max") or skill_data.get("writing_target_max") or 80)
    prompt = skill_data.get("writing_prompt") or lesson.short_description or ""

    # Grade with AI essay evaluation engine
    eval_result = evaluate_writing_submission(
        text=essay_content,
        target_min=target_min,
        target_max=target_max,
        prompt=prompt
    )

    # Save or update WritingSubmission
    submission = WritingSubmission.query.filter_by(user_id=current_user.id, lesson_id=lesson.id).first()
    if not submission:
        submission = WritingSubmission(
            user_id=current_user.id,
            lesson_id=lesson.id,
            content=essay_content,
            word_count=eval_result["word_count"],
            score=eval_result["overall_score"],
            status="GRADED",
            feedback=eval_result["general_feedback"],
            evaluation_data=eval_result
        )
        db.session.add(submission)
    else:
        submission.content = essay_content
        submission.word_count = eval_result["word_count"]
        submission.score = eval_result["overall_score"]
        submission.status = "GRADED"
        submission.feedback = eval_result["general_feedback"]
        submission.evaluation_data = eval_result

    # Mark LessonProgress if not already completed
    progress = LessonProgress.query.filter_by(user_id=current_user.id, lesson_id=lesson.id).first()
    if not progress:
        progress = LessonProgress(user_id=current_user.id, lesson_id=lesson.id, completed_at=datetime.utcnow())
        db.session.add(progress)

    # Add XP & Daily Activity
    xp_earned = 30
    if eval_result["overall_score"] >= 8.5:
        xp_earned = 50
    elif eval_result["overall_score"] >= 7.0:
        xp_earned = 40
    current_user.add_xp(xp_earned, reason=f"Nộp bài viết bài học: {lesson.title}")
    record_daily_activity(current_user)

    db.session.commit()

    if request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({
            "status": "success",
            "message": f"Nộp bài viết thành công! Bạn nhận được +{xp_earned} XP.",
            "xp_earned": xp_earned,
            "submission_id": submission.id,
            "evaluation": eval_result
        })

    flash(f"Nộp bài viết thành công! Bạn nhận được +{xp_earned} XP và đạt điểm {eval_result['overall_score']}/10.", "success")
    return redirect(url_for("learning.lesson_detail", lesson_id=lesson.id))


def _calculate_word_similarity(w1, w2):
    """Calculates normalized Levenshtein similarity ratio between two words."""
    w1 = (w1 or "").lower().strip(".,!?:;\"'()")
    w2 = (w2 or "").lower().strip(".,!?:;\"'()")
    if not w1 and not w2:
        return 1.0
    if not w1 or not w2:
        return 0.0
    if w1 == w2:
        return 1.0
    m, n = len(w1), len(w2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            cost = 0 if w1[i - 1] == w2[j - 1] else 1
            dp[i][j] = min(dp[i - 1][j] + 1, dp[i][j - 1] + 1, dp[i - 1][j - 1] + cost)
    dist = dp[m][n]
    max_len = max(m, n)
    return max(0.0, 1.0 - (dist / max_len))


@bp.post("/lessons/<int:lesson_id>/speaking/evaluate")
@login_required
def evaluate_speaking_pronunciation(lesson_id):
    """
    Evaluates learner pronunciation against the target sentence with AI word-by-word feedback.
    """
    lesson = Lesson.query.filter_by(id=lesson_id, is_active=True).first_or_404()
    data = request.get_json() if request.is_json else request.form
    target_text = (data.get("target_text") or "").strip()
    spoken_text = (data.get("spoken_text") or "").strip()
    sentence_idx = int(data.get("sentence_idx") or 0)

    if not target_text:
        return jsonify({"status": "error", "message": "Câu mẫu không được để trống."}), 400

    target_tokens = [w for w in target_text.split() if w.strip()]
    spoken_tokens = [w for w in spoken_text.split() if w.strip()]

    word_analysis = []
    total_score = 0
    matched_count = 0
    spoken_remaining = list(spoken_tokens)

    for tw in target_tokens:
        clean_tw = tw.lower().strip(".,!?:;\"'()")
        best_sim = 0.0
        best_idx = -1
        for idx, sw in enumerate(spoken_remaining):
            sim = _calculate_word_similarity(clean_tw, sw)
            if sim > best_sim:
                best_sim = sim
                best_idx = idx

        if best_idx != -1 and best_sim >= 0.5:
            spoken_remaining.pop(best_idx)

        word_score = int(round(best_sim * 100))
        if best_sim >= 0.85:
            status = "correct"
            matched_count += 1
        elif best_sim >= 0.55:
            status = "close"
            matched_count += 0.5
        else:
            status = "incorrect"

        word_analysis.append({
            "word": tw,
            "status": status,
            "score": word_score,
            "similarity": round(best_sim, 2)
        })
        total_score += word_score

    word_count = len(target_tokens) or 1
    accuracy_score = int(round(total_score / word_count))
    completeness_score = int(round((len(spoken_tokens) / max(1, word_count)) * 100))
    completeness_score = min(100, completeness_score)
    fluency_score = min(100, max(20, int(round((matched_count / word_count) * 100))))
    overall_score = int(round(0.6 * accuracy_score + 0.25 * completeness_score + 0.15 * fluency_score))
    overall_score = max(10, min(100, overall_score))

    if overall_score >= 85:
        ai_feedback = "Xuất sắc! Bạn phát âm rất rõ ràng, chuẩn xác từng từ khóa và ngữ điệu tự nhiên."
        grade = "Excellent"
    elif overall_score >= 65:
        ai_feedback = "Rất tốt! Bạn đã phát âm chuẩn phần lớn các từ. Chú ý các từ chưa chuẩn để ngữ điệu mượt hơn."
        grade = "Good"
    elif overall_score >= 45:
        ai_feedback = "Khá ổn! Hãy chú ý phát âm rõ âm đuôi và các nguyên âm dài. Hãy nghe audio mẫu lại 1 lần nhé."
        grade = "Needs Practice"
    else:
        ai_feedback = "Hãy nghe mẫu thật kỹ, đọc chậm rãi từng từ và nhấn nhá trọng âm trước khi thu âm lại nhé."
        grade = "Try Again"

    return jsonify({
        "status": "success",
        "evaluation": {
            "overall_score": overall_score,
            "accuracy_score": accuracy_score,
            "completeness_score": completeness_score,
            "fluency_score": fluency_score,
            "grade": grade,
            "ai_feedback": ai_feedback,
            "target_text": target_text,
            "spoken_text": spoken_text,
            "word_analysis": word_analysis,
            "sentence_idx": sentence_idx
        }
    })


@bp.post("/lessons/<int:lesson_id>/notes")
@login_required
def save_lesson_note(lesson_id):
    lesson = Lesson.query.filter_by(id=lesson_id, is_active=True).first_or_404()
    note_text = ""
    if request.is_json and request.json:
        note_text = request.json.get("note", "").strip()
    else:
        note_text = request.form.get("note", "").strip()

    note_record = LessonNote.query.filter_by(user_id=current_user.id, lesson_id=lesson.id).first()
    if not note_record:
        note_record = LessonNote(user_id=current_user.id, lesson_id=lesson.id, content=note_text)
        db.session.add(note_record)
    else:
        note_record.content = note_text
    db.session.commit()

    if request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"success": True, "message": "Đã lưu ghi chú bài học thành công!"})

    flash("Đã lưu ghi chú bài học thành công!", "success")
    return redirect(lesson.url)


@bp.post("/lessons/<int:lesson_id>/bookmark")
@login_required
def toggle_lesson_bookmark(lesson_id):
    lesson = Lesson.query.filter_by(id=lesson_id, is_active=True).first_or_404()
    section_index = 1
    if request.is_json and request.json:
        section_index = int(request.json.get("section_index", 1))
    else:
        section_index = request.form.get("section_index", type=int) or 1

    bm = LessonBookmark.query.filter_by(user_id=current_user.id, lesson_id=lesson.id, section_index=section_index).first()
    if bm:
        db.session.delete(bm)
        db.session.commit()
        is_bm = False
        msg = f"Đã bỏ bookmark Phần {section_index}."
    else:
        db.session.add(LessonBookmark(user_id=current_user.id, lesson_id=lesson.id, section_index=section_index))
        db.session.commit()
        is_bm = True
        msg = f"Đã bookmark thành công Phần {section_index}!"

    if request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"success": True, "is_bookmarked": is_bm, "message": msg})

    flash(msg, "success" if is_bm else "info")
    return redirect(lesson.url)


@bp.post("/lessons/<int:lesson_id>/report")
@login_required
def report_lesson(lesson_id):
    lesson = Lesson.query.filter_by(id=lesson_id, is_active=True).first_or_404()
    reason = ""
    details = ""
    if request.is_json and request.json:
        reason = request.json.get("reason", "").strip()
        details = request.json.get("details", "").strip()
    else:
        reason = request.form.get("reason", "").strip()
        details = request.form.get("details", "").strip()

    if not reason:
        reason = "Khác"

    report = LessonReport(user_id=current_user.id, lesson_id=lesson.id, reason=reason, details=details)
    db.session.add(report)
    db.session.commit()

    msg = "Đã gửi báo cáo nội dung bài học thành công. Cảm ơn sự đóng góp của bạn!"
    if request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"success": True, "message": msg})

    flash(msg, "success")
    return redirect(lesson.url)


@bp.post("/lessons/<int:lesson_id>/rate")
@login_required
def rate_lesson(lesson_id):
    """
    Submits or updates a 1-5 star rating and optional review text for the lesson.
    """
    lesson = Lesson.query.filter_by(id=lesson_id, is_active=True).first_or_404()

    rating_val = None
    review_text = ""

    if request.is_json and request.json:
        rating_val = request.json.get("rating")
        review_text = (request.json.get("review_text") or "").strip()
    else:
        rating_val = request.form.get("rating")
        review_text = (request.form.get("review_text") or "").strip()

    try:
        rating_val = int(rating_val)
    except (ValueError, TypeError):
        rating_val = None

    if not rating_val or rating_val < 1 or rating_val > 5:
        if request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"success": False, "message": "Số sao đánh giá phải từ 1 đến 5 sao."}), 400
        flash("Vui lòng chọn số sao từ 1 đến 5 sao.", "warning")
        return redirect(lesson.url)

    if len(review_text) > 1000:
        review_text = review_text[:1000]

    rating_record = LessonRating.query.filter_by(user_id=current_user.id, lesson_id=lesson.id).first()
    is_update = bool(rating_record)

    if rating_record:
        rating_record.rating = rating_val
        rating_record.review_text = review_text
        rating_record.updated_at = datetime.now(timezone.utc)
    else:
        rating_record = LessonRating(
            user_id=current_user.id,
            lesson_id=lesson.id,
            rating=rating_val,
            review_text=review_text
        )
        db.session.add(rating_record)

    db.session.commit()

    msg = "Đã cập nhật đánh giá bài học của bạn!" if is_update else "Cảm ơn bạn đã gửi đánh giá bài học!"
    if request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({
            "success": True,
            "message": msg,
            "rating": {
                "id": rating_record.id,
                "rating": rating_record.rating,
                "review_text": rating_record.review_text or "",
                "user_name": current_user.full_name or current_user.username,
                "updated_at": rating_record.updated_at.strftime("%d/%m/%Y %H:%M") if rating_record.updated_at else ""
            },
            "rating_val": rating_record.rating,
            "review_text": rating_record.review_text or "",
            "average_rating": lesson.average_rating,
            "ratings_count": lesson.ratings_count,
            "distribution": lesson.get_rating_distribution(),
            "user_name": current_user.full_name or current_user.username,
            "updated_at": rating_record.updated_at.strftime("%d/%m/%Y %H:%M") if rating_record.updated_at else ""
        })

    flash(msg, "success")
    return redirect(lesson.url)


@bp.get("/lessons/<int:lesson_id>/ratings")
@login_required
def get_lesson_ratings(lesson_id):
    """
    Returns list of reviews and rating metrics for the lesson.
    """
    lesson = Lesson.query.filter_by(id=lesson_id, is_active=True).first_or_404()
    ratings = LessonRating.query.filter_by(lesson_id=lesson.id).order_by(LessonRating.updated_at.desc()).limit(20).all()

    data = []
    for r in ratings:
        data.append({
            "id": r.id,
            "user_id": r.user_id,
            "user_name": r.user.full_name or r.user.username if r.user else "Học viên",
            "avatar": r.user.avatar if r.user and r.user.avatar else "default_avatar.png",
            "rating": r.rating,
            "review_text": r.review_text or "",
            "date": r.updated_at.strftime("%d/%m/%Y") if r.updated_at else ""
        })

    return jsonify({
        "success": True,
        "average_rating": lesson.average_rating,
        "ratings_count": lesson.ratings_count,
        "distribution": lesson.get_rating_distribution(),
        "ratings": data
    })


@bp.get("/lessons/<int:lesson_id>/annotations")
@login_required
def get_reading_annotations(lesson_id):
    """
    Returns list of reading annotations made by current user for this lesson.
    """
    lesson = Lesson.query.filter_by(id=lesson_id, is_active=True).first_or_404()
    annotations = ReadingAnnotation.query.filter_by(
        lesson_id=lesson.id, user_id=current_user.id
    ).order_by(ReadingAnnotation.created_at.asc()).all()
    return jsonify({
        "status": "success",
        "success": True,
        "annotations": [a.to_dict() for a in annotations]
    })


@bp.post("/lessons/<int:lesson_id>/annotations")
@login_required
def save_reading_annotation(lesson_id):
    """
    Creates or updates an inline reading annotation for a selected text passage.
    """
    lesson = Lesson.query.filter_by(id=lesson_id, is_active=True).first_or_404()
    data = request.get_json() if request.is_json else request.form

    selected_text = (data.get("selected_text") or "").strip()
    note_content = (data.get("note_content") or "").strip()
    annotation_id = data.get("id")

    if not selected_text:
        return jsonify({"status": "error", "success": False, "message": "Đoạn văn bản được chọn không được để trống."}), 400

    paragraph_index = int(data.get("paragraph_index") or 0)
    start_offset = int(data.get("start_offset") or 0)
    end_offset = int(data.get("end_offset") or 0)
    color = (data.get("color") or "yellow").strip()

    if annotation_id:
        ann = ReadingAnnotation.query.filter_by(id=annotation_id, lesson_id=lesson.id, user_id=current_user.id).first()
        if ann:
            ann.note_content = note_content
            ann.color = color
            db.session.commit()
            return jsonify({
                "status": "success",
                "success": True,
                "message": "Đã cập nhật đánh dấu/ghi chú thành công!",
                "annotation": ann.to_dict()
            })

    ann = ReadingAnnotation(
        lesson_id=lesson.id,
        user_id=current_user.id,
        selected_text=selected_text,
        note_content=note_content,
        paragraph_index=paragraph_index,
        start_offset=start_offset,
        end_offset=end_offset,
        color=color
    )
    db.session.add(ann)
    db.session.commit()

    return jsonify({
        "status": "success",
        "success": True,
        "message": "Đã đánh dấu nổi bật bài đọc thành công!",
        "annotation": ann.to_dict()
    }), 201


@bp.delete("/lessons/<int:lesson_id>/annotations/<int:annotation_id>")
@bp.post("/lessons/<int:lesson_id>/annotations/<int:annotation_id>/delete")
@login_required
def delete_reading_annotation(lesson_id, annotation_id):
    """
    Deletes an inline reading annotation or highlight.
    """
    ann = ReadingAnnotation.query.filter_by(id=annotation_id, lesson_id=lesson_id, user_id=current_user.id).first_or_404()
    db.session.delete(ann)
    db.session.commit()
    return jsonify({
        "status": "success",
        "success": True,
        "message": "Đã xóa đánh dấu thành công!"
    })


@bp.post("/lessons/<int:lesson_id>/annotations/clear-all")
@login_required
def clear_all_reading_annotations(lesson_id):
    """
    Clears all inline reading annotations/highlights made by current user for this lesson.
    """
    lesson = Lesson.query.filter_by(id=lesson_id, is_active=True).first_or_404()
    ReadingAnnotation.query.filter_by(lesson_id=lesson.id, user_id=current_user.id).delete()
    db.session.commit()
    return jsonify({
        "status": "success",
        "success": True,
        "message": "Đã xóa toàn bộ đánh dấu và ghi chú bài đọc!"
    })


@bp.post("/lessons/<int:lesson_id>/complete")
@login_required
def complete_lesson(lesson_id):
    lesson = Lesson.query.filter_by(id=lesson_id, is_active=True).first_or_404()
    form = ActionForm()
    if not form.validate_on_submit():
        abort(400)
    duration_seconds = request.form.get("duration_seconds", type=int) or 0
    progress = LessonProgress.query.filter_by(user_id=current_user.id, lesson_id=lesson.id).first()
    if not progress:
        progress = LessonProgress(
            user_id=current_user.id,
            lesson_id=lesson.id,
            duration_seconds=duration_seconds
        )
        db.session.add(progress)
        db.session.commit()
        record_daily_activity(current_user)
        flash("Tuyệt vời! Bài học đã được đánh dấu hoàn thành.", "success")
    else:
        if duration_seconds > 0:
            progress.duration_seconds = (progress.duration_seconds or 0) + duration_seconds
            db.session.commit()
        record_daily_activity(current_user)
    return redirect(lesson.url)


@bp.get("/progress")
@login_required
def progress():
    lessons_done = LessonProgress.query.filter_by(user_id=current_user.id).order_by(LessonProgress.completed_at.desc()).all()
    words = VocabularyProgress.query.filter_by(user_id=current_user.id).filter(VocabularyProgress.learned_count > 0).all()
    attempts = QuizAttempt.query.filter_by(user_id=current_user.id).order_by(QuizAttempt.created_at.desc()).all()
    percentages = [round(a.score / a.total_questions * 100) for a in attempts]
    return render_template("learning/progress.html", lessons_done=lessons_done, words=words, attempts=attempts,
                           best=max(percentages, default=0), average=round(sum(percentages) / len(percentages)) if percentages else 0)


