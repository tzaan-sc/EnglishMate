import random
from datetime import date, datetime, timedelta, timezone

from flask import abort, flash, jsonify, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required
from sqlalchemy import func

from ...extensions import db, csrf
from ..auth.models import record_daily_activity
from .models import (Badge, Challenge, GrammarErrorLog, GrammarExerciseAttempt, GrammarProgress, GrammarRule,
                       GrammarRuleBookmark, GrammarTopic, Lesson, LessonBookmark, LessonFavorite,
                       LessonNote, LessonProgress, LessonReport, Question, Quiz, QuizAttempt,
                       QuizAttemptAnswer, UserBadge, UserChallenge, Vocabulary, VocabularyProgress, WordReport)
from .vocab_catalog import (VOCAB_CATEGORIES, get_category_info, get_subcategory_info,
                           normalize_category_key, normalize_subcategory_key)
from . import bp
from .forms import ActionForm, QuizStartForm


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
        if sd.get("audio_url"):
            lesson.audio_url = sd.get("audio_url")

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

    return render_template(
        "learning/lesson_detail.html",
        lesson=lesson,
        transcript_lines=transcript_lines,
        reading_passage=reading_passage,
        reading_guideline=reading_guideline,
        reading_paragraphs=reading_paragraphs,
        reading_vocab=reading_vocab,
        reading_questions=reading_questions,
        writing_prompt=writing_prompt,
        writing_model=writing_model,
        writing_templates=writing_templates,
        writing_target_min=writing_target_min,
        writing_target_max=writing_target_max,
        speaking_context=speaking_context,
        speaking_sentences=speaking_sentences,
        speaking_tips=speaking_tips,
        completed=completed,
        user_note=note_record.content if note_record else "",
        bookmarks=bookmarks,
        is_favorite=is_favorite,
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


@bp.post("/lessons/<int:lesson_id>/complete")
@login_required
def complete_lesson(lesson_id):
    lesson = Lesson.query.filter_by(id=lesson_id, is_active=True).first_or_404()
    form = ActionForm()
    if not form.validate_on_submit():
        abort(400)
    if not LessonProgress.query.filter_by(user_id=current_user.id, lesson_id=lesson.id).first():
        db.session.add(LessonProgress(user_id=current_user.id, lesson_id=lesson.id))
        record_daily_activity(current_user)
        flash("Tuyệt vời! Bài học đã được đánh dấu hoàn thành.", "success")
    else:
        record_daily_activity(current_user)
    return redirect(lesson.url)


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


@bp.get("/progress")
@login_required
def progress():
    lessons_done = LessonProgress.query.filter_by(user_id=current_user.id).order_by(LessonProgress.completed_at.desc()).all()
    words = VocabularyProgress.query.filter_by(user_id=current_user.id).filter(VocabularyProgress.learned_count > 0).all()
    attempts = QuizAttempt.query.filter_by(user_id=current_user.id).order_by(QuizAttempt.created_at.desc()).all()
    percentages = [round(a.score / a.total_questions * 100) for a in attempts]
    return render_template("learning/progress.html", lessons_done=lessons_done, words=words, attempts=attempts,
                           best=max(percentages, default=0), average=round(sum(percentages) / len(percentages)) if percentages else 0)


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


# ==========================================
# GAME SYSTEM ROUTES
# ==========================================
import uuid
import json
from datetime import datetime, timedelta

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

        db.session.commit()
        flash("Đã cập nhật các cài đặt từ vựng cá nhân thành công!", "success")
        return redirect(url_for("learning.vocabulary_settings"))

    return render_template("learning/vocabulary_settings.html")


# ==========================================
# GRAMMAR LEARNING ROUTES
# ==========================================

def ensure_initial_grammar_topics():
    if GrammarTopic.query.count() > 0:
        return

    sample_topics = [
        GrammarTopic(
            title="Thì Hiện Tại Đơn (Present Simple Tense)",
            category="Các thì (Tenses)",
            level="A1",
            difficulty="Easy",
            summary="Quy tắc, công thức và cách dùng thì hiện tại đơn trong giao tiếp và văn viết tiếng Anh.",
            rule_explanation="""1. Cấu trúc với Động từ Tỏ thái độ / Thường:
- Khẳng định: S + V(s/es)
- Phủ định: S + do/does + not + V_inf
- Nghi vấn: Do/Does + S + V_inf?

2. Cách sử dụng chính:
- Diễn tả hành động lặp đi lặp lại theo thói quen (every day, always, usually).
- Diễn tả sự thật hiển nhiên, chân lý khách quan.
- Diễn tả lịch trình, thời gian biểu cố định.""",
            examples_json="""She works at a technology company in Hanoi.|Cô ấy làm việc tại một công ty công nghệ ở Hà Nội.
Do you study English every morning?|Bạn có học tiếng Anh mỗi sáng không?
The sun rises in the East.|Mặt trời mọc ở hướng Đông.""",
            common_mistakes="❌ Quên thêm 's/es' sau động từ khi chủ ngữ là ngôi thứ 3 số ít (He/She/It).\n❌ Nhầm lẫn giữa trợ động từ 'do/does' và động từ 'to be' (am/is/are).",
            tips_tricks="💡 Nhớ quy tắc thêm 'es' sau các động từ kết thúc bằng: o, s, ch, x, sh, z (VD: watch ➔ watches, wash ➔ washes).",
            related_topic_ids="2,3"
        ),
        GrammarTopic(
            title="Thì Hiện Tại Tiếp Diễn (Present Continuous Tense)",
            category="Các thì (Tenses)",
            level="A1",
            difficulty="Easy",
            summary="Cấu trúc, dấu hiệu nhận biết và cách dùng thì hiện tại tiếp diễn.",
            rule_explanation="""1. Cấu trúc:
- Khẳng định: S + am/is/are + V-ing
- Phủ định: S + am/is/are + not + V-ing
- Nghi vấn: Am/Is/Are + S + V-ing?

2. Cách sử dụng chính:
- Diễn tả hành động đang diễn ra ngay tại thời điểm nói (now, at the moment).
- Diễn tả kế hoạch đã lên lịch trong tương lai gần.""",
            examples_json="""I am writing a blog post right now.|Tôi đang viết một bài blog ngay lúc này.
They are meeting the project manager tomorrow.|Họ sẽ gặp quản lý dự án vào ngày mai.""",
            common_mistakes="❌ Không dùng thì hiện tại tiếp diễn với các động từ chỉ trạng thái/cảm xúc (stative verbs) như: know, want, like, love, believe.",
            tips_tricks="💡 Dấu hiệu nhận biết: now, right now, at the moment, Listen!, Look!",
            related_topic_ids="1,3"
        ),
        GrammarTopic(
            title="Thì Quá Khứ Đơn (Past Simple Tense)",
            category="Các thì (Tenses)",
            level="A2",
            difficulty="Medium",
            summary="Cách chia động từ quá khứ có quy tắc và bất quy tắc.",
            rule_explanation="""1. Cấu trúc:
- Khẳng định: S + V2/ed
- Phủ định: S + did not (didn't) + V_inf
- Nghi vấn: Did + S + V_inf?

2. Cách sử dụng chính:
- Diễn tả hành động đã xảy ra và chấm dứt hoàn toàn trong quá khứ tại thời điểm xác định.""",
            examples_json="""We visited the national museum last weekend.|Chúng tôi đã thăm bảo tàng quốc gia cuối tuần trước.
She didn't receive the email yesterday.|Cô ấy đã không nhận được email ngày hôm qua.""",
            common_mistakes="❌ Quên chuyển động từ về dạng nguyên thể (V_inf) sau trợ động từ 'did/didn't'.",
            tips_tricks="💡 Học thuộc 360 động từ bất quy tắc thông dụng (VD: go ➔ went, see ➔ saw, buy ➔ bought).",
            related_topic_ids="1,2"
        ),
        GrammarTopic(
            title="Câu Điều Kiện Loại 1 (First Conditional)",
            category="Cấu trúc câu (Sentence Structure)",
            level="B1",
            difficulty="Medium",
            summary="Cấu trúc diễn tả giả định có thật hoặc có thể xảy ra ở hiện tại hoặc tương lai.",
            rule_explanation="""1. Cấu trúc:
- Mệnh đề If: If + S + V(present simple)
- Mệnh đề chính: S + will / can / may + V_inf

2. Ý nghĩa:
- Diễn tả sự việc có khả năng cao sẽ xảy ra nếu điều kiện được đáp ứng.""",
            examples_json="""If it rains tomorrow, we will stay at home.|Nếu ngày mai trời mưa, chúng tôi sẽ ở nhà.
If you practice every day, you will speak English fluently.|Nếu bạn luyện tập mỗi ngày, bạn sẽ nói tiếng Anh trôi chảy.""",
            common_mistakes="❌ Dùng 'will' ở cả 2 mệnh đề (Sai: If it will rain, I will stay).",
            tips_tricks="💡 Nhớ thần chú: 'If đi với Hiện tại đơn, vế còn lại dùng Will + động từ nguyên thể'.",
            related_topic_ids="1,3"
        ),
        GrammarTopic(
            title="Động Từ Khuyết Thiếu (Modal Verbs: Can, Must, Should)",
            category="Động từ khuyết thiếu (Modals)",
            level="A2",
            difficulty="Easy",
            summary="Cách dùng các động từ khuyết thiếu chỉ khả năng, nghĩa vụ và lời khuyên.",
            rule_explanation="""1. Cấu trúc chung: S + Modal Verb + V_inf
2. Phân loại theo chức năng:
- Can / Could: Diễn tả khả năng, năng lực.
- Must / Have to: Diễn tả sự bắt buộc, nghĩa vụ.
- Should / Ought to: Diễn tả lời khuyên nên làm.""",
            examples_json="""You should drink more water every day.|Bạn nên uống nhiều nước hơn mỗi ngày.
Applicants must submit their resume before Friday.|Ứng viên phải nộp hồ sơ trước thứ Sáu.""",
            common_mistakes="❌ Thêm 'to' sau Modal Verb (Sai: You should to study). Ngoại lệ chỉ có 'ought to' và 'have to'.",
            tips_tricks="💡 Sau Modal Verbs luôn đi trực tiếp với Động từ nguyên thể không 'to' (V_inf).",
            related_topic_ids="4,6"
        )
    ]
    db.session.add_all(sample_topics)
    db.session.commit()


@bp.route("/grammar")
@login_required
def grammar_overview():
    ensure_initial_grammar_topics()

    q = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    level = request.args.get("level", "").strip()
    difficulty = request.args.get("difficulty", "").strip()
    status = request.args.get("status", "").strip()

    all_topics = GrammarTopic.query.filter_by(is_active=True).all()
    user_progress = GrammarProgress.query.filter_by(user_id=current_user.id).all()
    completed_ids = {p.topic_id for p in user_progress if p.is_completed}
    favorite_ids = {p.topic_id for p in user_progress if p.is_favorite}

    categories = [r[0] for r in db.session.query(GrammarTopic.category).distinct().all()]

    query = GrammarTopic.query.filter_by(is_active=True)
    if q:
        query = query.filter(GrammarTopic.title.ilike(f"%{q}%") | GrammarTopic.summary.ilike(f"%{q}%"))
    if category:
        query = query.filter_by(category=category)
    if level:
        query = query.filter_by(level=level)
    if difficulty:
        query = query.filter_by(difficulty=difficulty)

    topics_list = query.order_by(GrammarTopic.level, GrammarTopic.id).all()

    if status == "completed":
        topics_list = [t for t in topics_list if t.id in completed_ids]
    elif status == "favorite":
        topics_list = [t for t in topics_list if t.id in favorite_ids]
    elif status == "new":
        topics_list = [t for t in topics_list if t.id not in completed_ids]

    total_topics = len(all_topics)
    completed_count = len(completed_ids)
    favorite_count = len(favorite_ids)

    return render_template(
        "learning/grammar.html",
        topics=topics_list,
        categories=categories,
        q=q,
        category=category,
        level=level,
        difficulty=difficulty,
        status=status,
        completed_ids=completed_ids,
        favorite_ids=favorite_ids,
        total_topics=total_topics,
        completed_count=completed_count,
        favorite_count=favorite_count,
    )


@bp.route("/grammar/<int:topic_id>")
@login_required
def grammar_detail(topic_id):
    ensure_initial_grammar_topics()
    ensure_initial_grammar_questions()

    topic = GrammarTopic.query.filter_by(id=topic_id, is_active=True).first_or_404()
    prog = GrammarProgress.query.filter_by(user_id=current_user.id, topic_id=topic.id).first()

    is_completed = prog.is_completed if prog else False
    is_favorite = prog.is_favorite if prog else False

    # Related topics
    related_topics = []
    if topic.related_topic_ids:
        r_ids = [int(i.strip()) for i in topic.related_topic_ids.split(",") if i.strip().isdigit()]
        if r_ids:
            related_topics = GrammarTopic.query.filter(GrammarTopic.id.in_(r_ids), GrammarTopic.is_active.is_(True)).all()
    if not related_topics:
        related_topics = GrammarTopic.query.filter(GrammarTopic.category == topic.category, GrammarTopic.id != topic.id, GrammarTopic.is_active.is_(True)).limit(3).all()

    # Learning path topics for the current level
    level_topics = GrammarTopic.query.filter_by(level=topic.level, is_active=True).order_by(GrammarTopic.id.asc()).all()
    if not level_topics or len(level_topics) < 2:
        level_topics = GrammarTopic.query.filter_by(is_active=True).order_by(GrammarTopic.level.asc(), GrammarTopic.id.asc()).all()

    # User's completed topics IDs
    completed_topic_ids = set(
        r[0] for r in db.session.query(GrammarProgress.topic_id).filter_by(user_id=current_user.id, is_completed=True).all()
    )

    # All active topics for Previous / Next lesson navigation
    all_topics = GrammarTopic.query.filter_by(is_active=True).order_by(GrammarTopic.level.asc(), GrammarTopic.id.asc()).all()
    prev_topic = None
    next_topic = None
    for idx, t in enumerate(all_topics):
        if t.id == topic.id:
            if idx > 0:
                prev_topic = all_topics[idx - 1]
            if idx < len(all_topics) - 1:
                next_topic = all_topics[idx + 1]
            break

    # Practice questions for in-lesson quiz (up to 5 questions)
    practice_questions = Question.query.filter(
        Question.topic == "Grammar",
        Question.level == topic.level
    ).limit(5).all()
    if not practice_questions or len(practice_questions) < 3:
        practice_questions = Question.query.filter_by(topic="Grammar").limit(5).all()
    if not practice_questions:
        practice_questions = Question.query.limit(5).all()

    return render_template(
        "learning/grammar_detail.html",
        topic=topic,
        is_completed=is_completed,
        is_favorite=is_favorite,
        related_topics=related_topics,
        level_topics=level_topics,
        completed_topic_ids=completed_topic_ids,
        prev_topic=prev_topic,
        next_topic=next_topic,
        practice_questions=practice_questions,
        form=ActionForm()
    )


@bp.post("/grammar/<int:topic_id>/complete")
@login_required
def complete_grammar_topic(topic_id):
    topic = GrammarTopic.query.filter_by(id=topic_id, is_active=True).first_or_404()
    prog = GrammarProgress.query.filter_by(user_id=current_user.id, topic_id=topic.id).first()
    if not prog:
        prog = GrammarProgress(user_id=current_user.id, topic_id=topic.id, is_completed=True, completed_at=datetime.utcnow())
        db.session.add(prog)
    else:
        prog.is_completed = not prog.is_completed
        if prog.is_completed:
            prog.completed_at = datetime.utcnow()
    
    if prog.is_completed:
        record_daily_activity(current_user)

    db.session.commit()
    msg = "Đã đánh dấu hoàn thành chủ đề ngữ pháp!" if prog.is_completed else "Đã bỏ đánh dấu hoàn thành."

    if request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"success": True, "is_completed": prog.is_completed, "message": msg})

    flash(msg, "success" if prog.is_completed else "info")
    return redirect(url_for("learning.grammar_detail", topic_id=topic.id))


@bp.post("/grammar/<int:topic_id>/favorite")
@login_required
def favorite_grammar_topic(topic_id):
    topic = GrammarTopic.query.filter_by(id=topic_id, is_active=True).first_or_404()
    prog = GrammarProgress.query.filter_by(user_id=current_user.id, topic_id=topic.id).first()
    if not prog:
        prog = GrammarProgress(user_id=current_user.id, topic_id=topic.id, is_favorite=True)
        db.session.add(prog)
    else:
        prog.is_favorite = not prog.is_favorite

    db.session.commit()
    msg = "Đã thêm vào chủ đề ngữ pháp yêu thích!" if prog.is_favorite else "Đã bỏ khỏi danh sách yêu thích."

    if request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"success": True, "is_favorite": prog.is_favorite, "message": msg})

    flash(msg, "success" if prog.is_favorite else "info")
    return redirect(request.referrer or url_for("learning.grammar_overview"))


# ==========================================
# GRAMMAR EXERCISES ROUTES (Section 3.5)
# ==========================================

def ensure_initial_grammar_questions():
    if Question.query.filter_by(topic="Grammar").count() > 0:
        return

    sample_questions = [
        Question(
            question_text="She ______ at a technology company in Hanoi.",
            option_a="work",
            option_b="works",
            option_c="working",
            option_d="worked",
            correct_option="B",
            explanation="Chủ ngữ là 'She' (ngôi thứ 3 số ít) ở thì hiện tại đơn ➔ Động từ thêm 's/es' (works).",
            level="A1",
            topic="Grammar"
        ),
        Question(
            question_text="Look! The train ______ into the station.",
            option_a="comes",
            option_b="is coming",
            option_c="came",
            option_d="has come",
            correct_option="B",
            explanation="Dấu hiệu 'Look!' chỉ hành động đang diễn ra ngay tại thời điểm nói ➔ Dùng thì Hiện tại tiếp diễn (is coming).",
            level="A1",
            topic="Grammar"
        ),
        Question(
            question_text="We ______ the ancient citadel last weekend.",
            option_a="visit",
            option_b="are visiting",
            option_c="visited",
            option_d="will visit",
            correct_option="C",
            explanation="Dấu hiệu 'last weekend' chỉ thời điểm xác định trong quá khứ ➔ Dùng thì Quá khứ đơn (visited).",
            level="A2",
            topic="Grammar"
        ),
        Question(
            question_text="If it ______ tomorrow, we will stay at home.",
            option_a="rains",
            option_b="will rain",
            option_c="rained",
            option_d="is raining",
            correct_option="A",
            explanation="Câu điều kiện loại 1: Mệnh đề If dùng thì Hiện tại đơn (rains), mệnh đề chính dùng Will + V_inf.",
            level="B1",
            topic="Grammar"
        ),
        Question(
            question_text="You ______ drink more water every day for better health.",
            option_a="should",
            option_b="must to",
            option_c="ought",
            option_d="had better to",
            correct_option="A",
            explanation="Sau động từ khuyết thiếu 'should' dùng V_inf trực tiếp để đưa ra lời khuyên.",
            level="A2",
            topic="Grammar"
        ),
        Question(
            question_text="They ______ an important business proposal right now.",
            option_a="discuss",
            option_b="are discussing",
            option_c="discussed",
            option_d="have discussed",
            correct_option="B",
            explanation="Dấu hiệu 'right now' ➔ Thì Hiện tại tiếp diễn (are discussing).",
            level="B1",
            topic="Grammar"
        )
    ]
    db.session.add_all(sample_questions)
    db.session.commit()


@bp.route("/grammar/exercises")
@login_required
def grammar_exercises_setup():
    ensure_initial_grammar_topics()
    ensure_initial_grammar_questions()

    topics = GrammarTopic.query.filter_by(is_active=True).all()
    recent_attempts = GrammarExerciseAttempt.query.filter_by(user_id=current_user.id).order_by(GrammarExerciseAttempt.completed_at.desc()).limit(5).all()

    return render_template(
        "learning/grammar_exercises_setup.html",
        topics=topics,
        recent_attempts=recent_attempts,
        form=ActionForm()
    )


@bp.post("/grammar/exercises/start")
@login_required
def start_grammar_exercise():
    ensure_initial_grammar_questions()

    topic_id = request.form.get("topic_id", type=int)
    difficulty = request.form.get("difficulty", "Easy").strip()
    question_count = request.form.get("question_count", type=int, default=10)

    query = Question.query
    if difficulty in ("Easy", "Medium", "Hard"):
        level_map = {"Easy": ["A1", "A2"], "Medium": ["B1", "B2"], "Hard": ["C1", "C2"]}
        query = query.filter(Question.level.in_(level_map.get(difficulty, ["A1", "A2"])))

    questions = query.limit(question_count).all()
    if not questions:
        questions = Question.query.limit(question_count).all()

    q_ids = [q.id for q in questions]

    session["grammar_exercise"] = {
        "topic_id": topic_id,
        "difficulty": difficulty,
        "question_ids": q_ids,
        "answers": {},
        "marked_reviews": [],
        "start_time": datetime.utcnow().isoformat()
    }

    return redirect(url_for("learning.do_grammar_exercise"))


@bp.route("/grammar/exercises/do")
@login_required
def do_grammar_exercise():
    sess_data = session.get("grammar_exercise")
    if not sess_data or not sess_data.get("question_ids"):
        flash("Vui lòng thiết lập bài tập trước khi bắt đầu.", "warning")
        return redirect(url_for("learning.grammar_exercises_setup"))

    q_ids = sess_data.get("question_ids", [])
    questions = Question.query.filter(Question.id.in_(q_ids)).all()

    q_map = {q.id: q for q in questions}
    ordered_questions = [q_map[qid] for qid in q_ids if qid in q_map]

    topic = None
    if sess_data.get("topic_id"):
        topic = db.session.get(GrammarTopic, sess_data.get("topic_id"))

    return render_template(
        "learning/grammar_exercises_do.html",
        questions=ordered_questions,
        topic=topic,
        sess_data=sess_data,
        form=ActionForm()
    )


@bp.post("/grammar/exercises/submit")
@login_required
def submit_grammar_exercise():
    sess_data = session.get("grammar_exercise")
    if not sess_data:
        flash("Phiên bài tập không hợp lệ.", "danger")
        return redirect(url_for("learning.grammar_exercises_setup"))

    q_ids = sess_data.get("question_ids", [])
    questions = Question.query.filter(Question.id.in_(q_ids)).all()

    user_answers = {}
    score = 0
    incorrect_questions = []

    for q in questions:
        ans = request.form.get(f"q_{q.id}", "").strip().upper()
        user_answers[str(q.id)] = ans
        if ans == q.correct_option:
            score += 1
        else:
            incorrect_questions.append((q, ans))

    start_time_str = sess_data.get("start_time")
    duration = 0
    if start_time_str:
        try:
            start_dt = datetime.fromisoformat(start_time_str)
            duration = int((datetime.utcnow() - start_dt).total_seconds())
        except Exception:
            duration = 60

    attempt = GrammarExerciseAttempt(
        user_id=current_user.id,
        topic_id=sess_data.get("topic_id"),
        difficulty=sess_data.get("difficulty", "Easy"),
        question_count=len(questions),
        score=score,
        total_questions=len(questions),
        duration_seconds=max(duration, 5)
    )
    db.session.add(attempt)
    db.session.commit()

    for q, ans in incorrect_questions:
        err = GrammarErrorLog(
            user_id=current_user.id,
            question_id=q.id,
            attempt_id=attempt.id,
            user_answer=ans if ans else "N/A",
            correct_answer=q.correct_option,
            is_resolved=False
        )
        db.session.add(err)

    if score > 0:
        record_daily_activity(current_user)

    db.session.commit()
    session.pop("grammar_exercise", None)

    flash("Đã nộp bài tập ngữ pháp thành công!", "success")
    return redirect(url_for("learning.grammar_exercise_summary", attempt_id=attempt.id))


@bp.route("/grammar/exercises/summary/<int:attempt_id>")
@login_required
def grammar_exercise_summary(attempt_id):
    attempt = db.session.get(GrammarExerciseAttempt, attempt_id)
    if not attempt or attempt.user_id != current_user.id:
        flash("Không tìm thấy kết quả bài tập.", "danger")
        return redirect(url_for("learning.grammar_exercises_setup"))

    error_logs = GrammarErrorLog.query.filter_by(attempt_id=attempt.id).all()
    incorrect_q_ids = [e.question_id for e in error_logs]
    incorrect_questions = Question.query.filter(Question.id.in_(incorrect_q_ids)).all() if incorrect_q_ids else []

    error_detail_map = {e.question_id: e for e in error_logs}

    pct = int((attempt.score / attempt.total_questions) * 100) if attempt.total_questions > 0 else 0

    return render_template(
        "learning/grammar_exercises_summary.html",
        attempt=attempt,
        error_logs=error_logs,
        incorrect_questions=incorrect_questions,
        error_detail_map=error_detail_map,
        pct=pct,
        form=ActionForm()
    )


@bp.post("/grammar/exercises/retry/<int:attempt_id>")
@login_required
def retry_grammar_exercise(attempt_id):
    attempt = db.session.get(GrammarExerciseAttempt, attempt_id)
    if not attempt or attempt.user_id != current_user.id:
        flash("Không tìm thấy thông tin lượt tập.", "danger")
        return redirect(url_for("learning.grammar_exercises_setup"))

    error_logs = GrammarErrorLog.query.filter_by(attempt_id=attempt.id).all()
    q_ids = [e.question_id for e in error_logs]

    if not q_ids:
        flash("Bạn không có câu sai nào trong lượt tập này! Rất xuất sắc!", "info")
        return redirect(url_for("learning.grammar_exercises_setup"))

    session["grammar_exercise"] = {
        "topic_id": attempt.topic_id,
        "difficulty": attempt.difficulty,
        "question_ids": q_ids,
        "answers": {},
        "marked_reviews": [],
        "start_time": datetime.utcnow().isoformat()
    }

    flash("Đã mở chế độ Thử lại các câu sai!", "info")
    return redirect(url_for("learning.do_grammar_exercise"))


# ==========================================
# GRAMMAR REFERENCE ROUTES (Section 3.6)
# ==========================================

def ensure_initial_grammar_rules():
    if GrammarRule.query.count() > 0:
        return

    sample_rules = [
        GrammarRule(
            title="Quy tắc Thêm S/ES vào Động Từ & Danh Từ",
            category="Verbs & Nouns",
            summary="Các quy tắc phát âm và chính tả khi thêm s/es vào đuôi động từ hoặc danh từ số nhiều.",
            explanation="""1. Quy tắc thêm 'es':
- Khi động từ hoặc danh từ kết thúc bằng các chữ cái: -s, -ss, -sh, -ch, -x, -z, -o ➔ Thêm 'es'.
  Ví dụ: watch ➔ watches, wash ➔ washes, box ➔ boxes, potato ➔ potatoes.

2. Quy tắc với đuôi '-y':
- Nguyên âm (a, e, i, o, u) + y ➔ Giữ nguyên, thêm 's' (play ➔ plays, boy ➔ boys).
- Phụ âm + y ➔ Đổi 'y' thành 'i' rồi thêm 'es' (study ➔ studies, city ➔ cities).""",
            examples="""watch ➔ watches (xem)
box ➔ boxes (hộp)
fly ➔ flies (bay)
toy ➔ toys (đồ chơi)""",
            exceptions="""- Một số từ mượn gốc Ý/Đức tận cùng là '-o' chỉ thêm 's': photo ➔ photos, piano ➔ pianos, radio ➔ radios, kilo ➔ kilos.""",
            common_errors="❌ Thêm 'es' cho các từ tận cùng '-y' đứng sau nguyên âm (Sai: playes ➔ Đúng: plays).\n❌ Quên phát âm đuôi /iz/ khi từ kết thúc bằng âm xuýt.",
            quick_table_html="""<table class="table table-bordered table-sm mb-0">
  <thead class="table-light"><tr><th>Đuôi tận cùng</th><th>Quy tắc</th><th>Ví dụ</th></tr></thead>
  <tbody>
    <tr><td>-s, -sh, -ch, -x, -z, -o</td><td>+ es</td><td>watches, washes, tomatoes</td></tr>
    <tr><td>Phụ âm + y</td><td>y ➔ i + es</td><td>study ➔ studies</td></tr>
    <tr><td>Nguyên âm + y</td><td>+ s</td><td>play ➔ plays</td></tr>
  </tbody>
</table>"""
        ),
        GrammarRule(
            title="Quy tắc Trật Tự Tính Từ (OSASCOMP)",
            category="Adjectives",
            summary="Thứ tự sắp xếp các tính từ khi bổ nghĩa cho một danh từ trong tiếng Anh.",
            explanation="""Khi có nhiều tính từ cùng đứng trước một danh từ, thứ tự được sắp xếp theo quy tắc OSASCOMP:
1. Opinion (Ý kiến, cảm nhận): beautiful, lovely, delicious
2. Size (Kích cỡ): big, small, huge, tall
3. Age (Độ tuổi, cũ mới): new, old, young, ancient
4. Shape (Hình dáng): round, square, oval
5. Color (Màu sắc): red, blue, dark, pale
6. Origin (Nguồn gốc, xuất xứ): Vietnamese, American, Japanese
7. Material (Chất liệu): wooden, silk, leather, plastic
8. Purpose (Mục đích sử dụng): sleeping (bag), racing (car)""",
            examples="""A beautiful small old round black Vietnamese wooden table.
(Một chiếc bàn gỗ Việt Nam màu đen hình tròn cũ nhỏ xinh xắn).""",
            exceptions="""- Tính từ chỉ kích thước và chiều dài thường đứng trước tính từ chỉ hình dạng (short round hair).""",
            common_errors="❌ Đặt Nguồn gốc hoặc Chất liệu lên trước Ý kiến (Sai: a wooden beautiful table ➔ Đúng: a beautiful wooden table).",
            quick_table_html="""<table class="table table-bordered table-sm mb-0">
  <thead class="table-light"><tr><th>Ký tự</th><th>Yếu tố (Meaning)</th><th>Ví dụ</th></tr></thead>
  <tbody>
    <tr><td>O</td><td>Opinion (Ý kiến)</td><td>lovely, ugly</td></tr>
    <tr><td>S</td><td>Size (Kích thước)</td><td>huge, tiny</td></tr>
    <tr><td>A</td><td>Age (Tuổi tác)</td><td>ancient, modern</td></tr>
    <tr><td>S</td><td>Shape (Hình dáng)</td><td>round, square</td></tr>
    <tr><td>C</td><td>Color (Màu sắc)</td><td>yellow, green</td></tr>
    <tr><td>O</td><td>Origin (Xuất xứ)</td><td>Italian, French</td></tr>
    <tr><td>M</td><td>Material (Chất liệu)</td><td>gold, plastic</td></tr>
    <tr><td>P</td><td>Purpose (Mục đích)</td><td>swimming (pool)</td></tr>
  </tbody>
</table>"""
        ),
        GrammarRule(
            title="Quy tắc Động Từ Bất Quy Tắc Phổ Biến (Irregular Verbs)",
            category="Verbs",
            summary="Bảng tổng hợp và quy tắc biến đổi các động từ bất quy tắc trong quá khứ đơn và quá khứ phân từ.",
            explanation="""Động từ bất quy tắc là các động từ khi chuyển sang Quá khứ đơn (V2) và Quá khứ phân từ (V3) không thêm đuôi '-ed' mà biến đổi theo dạng riêng hoặc giữ nguyên.""",
            examples="""go ➔ went ➔ gone (đi)
see ➔ saw ➔ seen (nhìn thấy)
take ➔ took ➔ taken (lấy)
cut ➔ cut ➔ cut (cắt)""",
            exceptions="""- Một số động từ có 2 cách chia cả có quy tắc và bất quy tắc (VD: burn ➔ burned/burnt, learn ➔ learned/learnt).""",
            common_errors="❌ Thêm '-ed' vào động từ bất quy tắc (Sai: goed ➔ Đúng: went).",
            quick_table_html="""<table class="table table-bordered table-sm mb-0">
  <thead class="table-light"><tr><th>V1 (Nguyên thể)</th><th>V2 (Quá khứ)</th><th>V3 (Phân từ)</th><th>Nghĩa</th></tr></thead>
  <tbody>
    <tr><td>go</td><td>went</td><td>gone</td><td>đi</td></tr>
    <tr><td>do</td><td>did</td><td>done</td><td>làm</td></tr>
    <tr><td>have</td><td>had</td><td>had</td><td>có</td></tr>
    <tr><td>make</td><td>made</td><td>made</td><td>tạo ra</td></tr>
  </tbody>
</table>"""
        )
    ]
    db.session.add_all(sample_rules)
    db.session.commit()


@bp.route("/grammar/reference")
@login_required
def grammar_reference_index():
    ensure_initial_grammar_rules()

    q = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    bookmarked_only = request.args.get("bookmarked_only", "").strip()

    user_bms = GrammarRuleBookmark.query.filter_by(user_id=current_user.id).all()
    bm_rule_ids = {b.rule_id for b in user_bms}

    categories = [r[0] for r in db.session.query(GrammarRule.category).distinct().all()]

    query = GrammarRule.query
    if q:
        query = query.filter(GrammarRule.title.ilike(f"%{q}%") | GrammarRule.summary.ilike(f"%{q}%"))
    if category:
        query = query.filter_by(category=category)

    rules = query.order_by(GrammarRule.id).all()

    if bookmarked_only == "1":
        rules = [r for r in rules if r.id in bm_rule_ids]

    return render_template(
        "learning/grammar_reference.html",
        rules=rules,
        categories=categories,
        q=q,
        category=category,
        bookmarked_only=bookmarked_only,
        bm_rule_ids=bm_rule_ids
    )


@bp.route("/grammar/reference/<int:rule_id>")
@login_required
def grammar_rule_detail(rule_id):
    rule = db.session.get(GrammarRule, rule_id)
    if not rule:
        flash("Không tìm thấy quy tắc ngữ pháp.", "danger")
        return redirect(url_for("learning.grammar_reference_index"))

    bm = GrammarRuleBookmark.query.filter_by(user_id=current_user.id, rule_id=rule.id).first()
    is_bookmarked = (bm is not None)

    return render_template(
        "learning/grammar_rule_detail.html",
        rule=rule,
        is_bookmarked=is_bookmarked,
        form=ActionForm()
    )


@bp.post("/grammar/reference/<int:rule_id>/bookmark")
@login_required
def bookmark_grammar_rule(rule_id):
    rule = db.session.get(GrammarRule, rule_id)
    if not rule:
        return jsonify({"success": False, "message": "Không tìm thấy quy tắc."}), 404

    bm = GrammarRuleBookmark.query.filter_by(user_id=current_user.id, rule_id=rule.id).first()
    if bm:
        db.session.delete(bm)
        db.session.commit()
        is_bm = False
        msg = "Đã bỏ bookmark quy tắc ngữ pháp."
    else:
        db.session.add(GrammarRuleBookmark(user_id=current_user.id, rule_id=rule.id))
        db.session.commit()
        is_bm = True
        msg = "Đã bookmark quy tắc ngữ pháp thành công!"

    if request.is_json or request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"success": True, "is_bookmarked": is_bm, "message": msg})

    flash(msg, "success" if is_bm else "info")
    return redirect(url_for("learning.grammar_rule_detail", rule_id=rule.id))


@bp.route("/grammar/reference/<int:rule_id>/print")
@login_required
def grammar_rule_print_view(rule_id):
    rule = db.session.get(GrammarRule, rule_id)
    if not rule:
        flash("Không tìm thấy quy tắc ngữ pháp.", "danger")
        return redirect(url_for("learning.grammar_reference_index"))

    return render_template("learning/grammar_rule_print.html", rule=rule)


# ==========================================
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
# ==============================================================================

def check_user_badges(user):
    """Checks user statistics and awards any unearned badges."""
    from .models import Badge, UserBadge, FlashcardSet, FlashcardProgress
    
    existing_badge_ids = {ub.badge_id for ub in UserBadge.query.filter_by(user_id=user.id).all()}
    all_badges = Badge.query.all()
    
    lessons_cnt = LessonProgress.query.filter_by(user_id=user.id).count()
    vocab_cnt = VocabularyProgress.query.filter_by(user_id=user.id).filter(VocabularyProgress.learned_count > 0).count()
    quiz_cnt = QuizAttempt.query.filter_by(user_id=user.id).count()
    perfect_cnt = QuizAttempt.query.filter_by(user_id=user.id).filter(QuizAttempt.score == QuizAttempt.total_questions, QuizAttempt.total_questions > 0).count()
    streak_days = max(user.current_streak or 0, user.longest_streak or 0)
    flashcard_cnt = FlashcardSet.query.filter_by(user_id=user.id).count() + FlashcardProgress.query.filter_by(user_id=user.id).count()
    user_level = user.get_level()
    
    newly_unlocked = []
    for badge in all_badges:
        if badge.id in existing_badge_ids:
            continue
            
        unlocked = False
        if badge.req_type == "lessons_count" and lessons_cnt >= badge.req_value:
            unlocked = True
        elif badge.req_type == "vocab_count" and vocab_cnt >= badge.req_value:
            unlocked = True
        elif badge.req_type == "quiz_count" and quiz_cnt >= badge.req_value:
            unlocked = True
        elif badge.req_type == "perfect_score" and perfect_cnt >= badge.req_value:
            unlocked = True
        elif badge.req_type == "streak_days" and streak_days >= badge.req_value:
            unlocked = True
        elif badge.req_type == "flashcard_count" and flashcard_cnt >= badge.req_value:
            unlocked = True
        elif badge.req_type == "level_reach" and user_level >= badge.req_value:
            unlocked = True
            
        if unlocked:
            ub = UserBadge(user_id=user.id, badge_id=badge.id, unlocked_at=datetime.utcnow())
            db.session.add(ub)
            user.add_xp(badge.xp_reward)
            newly_unlocked.append(badge)
            
    if newly_unlocked:
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
    return newly_unlocked


def get_or_create_user_challenges(user):
    """Initializes and returns user's daily and weekly challenges."""
    from .models import Challenge, UserChallenge
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())
    
    all_challenges = Challenge.query.all()
    user_challenges = []
    
    for ch in all_challenges:
        p_date = today if ch.period == "DAILY" else start_of_week
        uc = UserChallenge.query.filter_by(user_id=user.id, challenge_id=ch.id, period_date=p_date).first()
        if not uc:
            uc = UserChallenge(
                user_id=user.id,
                challenge_id=ch.id,
                current_progress=0,
                is_completed=False,
                is_claimed=False,
                period_date=p_date
            )
            db.session.add(uc)
            db.session.flush()
        user_challenges.append(uc)
        
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
    return user_challenges


def update_challenge_progress(user, action_type, count=1):
    """Updates challenge progress for matching action_type."""
    from .models import Challenge, UserChallenge
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())
    
    get_or_create_user_challenges(user)
    
    user_challenges = UserChallenge.query.join(Challenge).filter(
        UserChallenge.user_id == user.id,
        Challenge.action_type == action_type,
        UserChallenge.is_completed == False,
        ((Challenge.period == "DAILY") & (UserChallenge.period_date == today)) |
        ((Challenge.period == "WEEKLY") & (UserChallenge.period_date == start_of_week))
    ).all()
    
    for uc in user_challenges:
        uc.current_progress = min(uc.challenge.target, uc.current_progress + count)
        if uc.current_progress >= uc.challenge.target:
            uc.is_completed = True
            uc.completed_at = datetime.utcnow()
            
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()


@bp.get("/gamification")
@bp.get("/leaderboard")
@login_required
def gamification_hub():
    from .models import Badge, UserBadge, Challenge, UserChallenge
    from ..auth.models import User, DailyActivity
    
    check_user_badges(current_user)
    user_challenges = get_or_create_user_challenges(current_user)
    
    level_info = current_user.get_level_info()
    
    # Badges
    all_badges = Badge.query.all()
    user_badge_map = {ub.badge_id: ub for ub in UserBadge.query.filter_by(user_id=current_user.id).all()}
    
    badges_data = []
    for b in all_badges:
        is_unlocked = b.id in user_badge_map
        unlocked_at = user_badge_map[b.id].unlocked_at if is_unlocked else None
        badges_data.append({
            "badge": b,
            "is_unlocked": is_unlocked,
            "unlocked_at": unlocked_at
        })
        
    # Leaderboards (Chỉ dành cho Học viên, loại trừ Quản trị viên Admin)
    student_filter = (User.role != "ADMIN")
    all_time_leaders = User.query.filter(student_filter).order_by(User.xp.desc()).limit(20).all()
    streak_leaders = User.query.filter(student_filter).order_by(User.current_streak.desc()).limit(20).all()
    
    # Weekly XP Leaders
    start_of_week = date.today() - timedelta(days=date.today().weekday())
    weekly_acts = db.session.query(
        DailyActivity.user_id,
        func.sum(DailyActivity.completed_lessons * 20).label("weekly_xp")
    ).join(User, User.id == DailyActivity.user_id).filter(
        DailyActivity.activity_date >= start_of_week,
        User.role != "ADMIN"
    ).group_by(DailyActivity.user_id).all()
    
    weekly_xp_map = {row.user_id: (row.weekly_xp or 0) for row in weekly_acts}
    all_students = User.query.filter(student_filter).all()
    weekly_leaders = sorted(all_students, key=lambda u: weekly_xp_map.get(u.id, 0) + min(50, (u.xp or 0)), reverse=True)[:20]
    
    # Daily goal calculation
    today = date.today()
    today_act = DailyActivity.query.filter_by(user_id=current_user.id, activity_date=today).first()
    daily_goal_target = current_user.daily_goal_xp or 50
    daily_progress_xp = min(daily_goal_target, (today_act.completed_lessons * 20) if today_act else 0)
    is_daily_goal_done = daily_progress_xp >= daily_goal_target or (today_act and today_act.goal_completed)
    is_daily_claimed = current_user.daily_reward_claimed_date == today
    
    daily_challenges = [uc for uc in user_challenges if uc.challenge.period == "DAILY"]
    weekly_challenges = [uc for uc in user_challenges if uc.challenge.period == "WEEKLY"]
    
    active_tab = request.args.get("tab", "leaderboard")
    
    return render_template(
        "learning/gamification.html",
        level_info=level_info,
        badges_data=badges_data,
        unlocked_count=len(user_badge_map),
        total_badges_count=len(all_badges),
        all_time_leaders=all_time_leaders,
        streak_leaders=streak_leaders,
        weekly_leaders=weekly_leaders,
        daily_challenges=daily_challenges,
        weekly_challenges=weekly_challenges,
        daily_progress_xp=daily_progress_xp,
        daily_goal_target=daily_goal_target,
        is_daily_goal_done=is_daily_goal_done,
        is_daily_claimed=is_daily_claimed,
        active_tab=active_tab
    )


@bp.post("/gamification/claim-challenge/<int:uc_id>")
@login_required
def claim_challenge_reward(uc_id):
    from .models import UserChallenge
    uc = UserChallenge.query.filter_by(id=uc_id, user_id=current_user.id).first_or_404()
    if not uc.is_completed:
        flash("Thử thách này chưa hoàn thành!", "warning")
        return redirect(url_for("learning.gamification_hub", tab="challenges"))
        
    if uc.is_claimed:
        flash("Bạn đã nhận thưởng cho thử thách này rồi!", "info")
        return redirect(url_for("learning.gamification_hub", tab="challenges"))
        
    uc.is_claimed = True
    reward_xp = uc.challenge.xp_reward
    current_user.add_xp(reward_xp, reason=f"Thưởng thử thách: {uc.challenge.title}")
    db.session.commit()
    
    flash(f"Chúc mừng! Bạn đã nhận được +{reward_xp} XP từ thử thách \"{uc.challenge.title}\"!", "success")
    return redirect(url_for("learning.gamification_hub", tab="challenges"))


@bp.post("/gamification/claim-daily-goal")
@login_required
def claim_daily_goal_reward():
    today = date.today()
    if current_user.daily_reward_claimed_date == today:
        flash("Bạn đã nhận phần thưởng mục tiêu ngày hôm nay rồi!", "info")
        return redirect(url_for("learning.gamification_hub", tab="challenges"))
        
    current_user.daily_reward_claimed_date = today
    reward_xp = 50
    current_user.add_xp(reward_xp, reason="Thưởng hoàn thành mục tiêu ngày")
    db.session.commit()
    
    flash(f"Tuyệt vời! Bạn đã nhận được rương thưởng ngày +{reward_xp} XP!", "success")
    return redirect(url_for("learning.gamification_hub", tab="challenges"))

