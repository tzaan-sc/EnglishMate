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


# ==============================================================================
# 12 MAJOR GRAMMAR CATEGORIES CATALOG
# ==============================================================================
GRAMMAR_12_CATEGORIES = [
    {
        "id": 1,
        "name": "Từ loại (Parts of Speech)",
        "name_en": "Parts of Speech",
        "icon": "ph-bold ph-text-aa",
        "badge": "TOEIC Part 5 (30% đề thi)",
        "badge_color": "warning",
        "desc": "Noun (Danh từ), Pronoun (Đại từ), Verb (Động từ), Adjective (Tính từ), Adverb (Trạng từ), Preposition, Conjunction, Determiner.",
        "keywords": ["Từ loại", "Parts of Speech", "Noun", "Pronoun", "Adjective", "Adverb"],
        "subtopics": ["Danh từ (Noun)", "Đại từ (Pronoun)", "Động từ (Verb)", "Tính từ (Adjective)", "Trạng từ (Adverb)", "Giới từ", "Liên từ", "Từ hạn định"]
    },
    {
        "id": 2,
        "name": "Cấu trúc câu (Sentence Structure)",
        "name_en": "Sentence Structure",
        "icon": "ph-bold ph-tree-structure",
        "badge": "Nền tảng câu",
        "badge_color": "info",
        "desc": "5 mẫu câu cơ bản (S+V, S+V+O, S+V+C, S+V+O+O, S+V+O+C), Câu đơn, câu ghép, câu phức & thành phần câu.",
        "keywords": ["Cấu trúc câu", "Sentence Structure", "Mẫu câu", "Thành phần câu"],
        "subtopics": ["S + V", "S + V + O", "S + V + C", "S + V + O + O", "S + V + O + C", "Câu đơn / ghép / phức"]
    },
    {
        "id": 3,
        "name": "Thì (Tenses)",
        "name_en": "12 English Tenses",
        "icon": "ph-bold ph-clock",
        "badge": "Trọng tâm TOEIC Part 5-6",
        "badge_color": "success",
        "desc": "12 thì tiếng Anh chuẩn xác: Hiện tại đơn, Tiếp diễn, Hoàn thành, Quá khứ đơn, Tương lai đơn...",
        "keywords": ["Thì", "Tenses", "Các thì", "Present Simple", "Past Simple", "Continuous", "Perfect"],
        "subtopics": ["Present Simple", "Present Continuous", "Present Perfect", "Past Simple", "Past Continuous", "Past Perfect", "Future Simple..."]
    },
    {
        "id": 4,
        "name": "Động từ (Verbs)",
        "name_en": "Verbs & Verb Patterns",
        "icon": "ph-bold ph-lightning",
        "badge": "Cốt lõi hành động",
        "badge_color": "warning",
        "desc": "Động từ thường / to be, Transitive/Intransitive, Linking verbs, Modal verbs, Phrasal verbs, Gerund, Infinitive.",
        "keywords": ["Động từ", "Verbs", "Modals", "Khuyết thiếu", "Gerund", "Infinitive", "Phrasal"],
        "subtopics": ["Động từ to be / thường", "Linking verbs", "Modal verbs", "Phrasal verbs", "Gerund (V-ing)", "To-Infinitive"]
    },
    {
        "id": 5,
        "name": "Danh từ & Mạo từ (Nouns & Articles)",
        "name_en": "Nouns & Articles",
        "icon": "ph-bold ph-books",
        "badge": "TOEIC Part 5",
        "badge_color": "primary",
        "desc": "Countable/Uncountable nouns, Singular/Plural, Possessive nouns, a/an/the, Zero article, Quantifiers (much, many, few...).",
        "keywords": ["Danh từ & Mạo từ", "Nouns & Articles", "Mạo từ", "Articles", "Quantifiers"],
        "subtopics": ["Countable / Uncountable", "Singular / Plural", "a / an / the", "Zero article", "Quantifiers: much, many, few..."]
    },
    {
        "id": 6,
        "name": "Đại từ & Từ hạn định (Pronouns & Determiners)",
        "name_en": "Pronouns & Determiners",
        "icon": "ph-bold ph-identification-card",
        "badge": "Bẫy đại từ TOEIC",
        "badge_color": "purple",
        "desc": "Personal pronouns, Possessive pronouns, Reflexive pronouns, Demonstratives, Indefinite (each, every, some, any, no).",
        "keywords": ["Đại từ & Từ hạn định", "Pronouns & Determiners", "Đại từ", "Từ hạn định"],
        "subtopics": ["Personal pronouns", "Possessive pronouns", "Reflexive pronouns", "Demonstratives", "each / every", "some / any / no"]
    },
    {
        "id": 7,
        "name": "Tính từ & Trạng từ (Adjectives & Adverbs)",
        "name_en": "Adjectives & Adverbs",
        "icon": "ph-bold ph-paint-brush",
        "badge": "Bẫy so sánh Part 5",
        "badge_color": "danger",
        "desc": "Vị trí tính từ, vị trí trạng từ, Adjective vs Adverb, Cấp so sánh (Comparative, Superlative, as...as), too/enough, so/such.",
        "keywords": ["Tính từ & Trạng từ", "Adjectives & Adverbs", "So sánh", "Comparative", "Superlative"],
        "subtopics": ["Vị trí tính từ / trạng từ", "Adjective vs Adverb", "Comparative (Hơn)", "Superlative (Nhất)", "too / enough", "so / such"]
    },
    {
        "id": 8,
        "name": "Giới từ (Prepositions)",
        "name_en": "Prepositions",
        "icon": "ph-bold ph-compass",
        "badge": "Học thuộc cụm từ",
        "badge_color": "danger",
        "desc": "Prepositions of time, place, direction, Prepositions after verbs, Prepositions after adjectives, Cụm giới từ cố định.",
        "keywords": ["Giới từ", "Prepositions"],
        "subtopics": ["Prepositions of time", "Prepositions of place", "Prepositions after verbs", "Prepositions after adjectives", "Cụm giới từ thường gặp"]
    },
    {
        "id": 9,
        "name": "Câu bị động (Passive Voice)",
        "name_en": "Passive Voice",
        "icon": "ph-bold ph-arrows-clockwise",
        "badge": "Trọng tâm TOEIC 70%",
        "badge_color": "primary",
        "desc": "Passive cơ bản, Passive theo các thì, Modal + Passive, Passive với 2 tân ngữ, Get passive, Causative have/get done.",
        "keywords": ["Câu bị động", "Passive Voice", "Passive", "Bị động"],
        "subtopics": ["Passive cơ bản", "Passive theo thì", "Modal + Passive", "Passive với 2 tân ngữ", "Get passive", "Causative (have/get done)"]
    },
    {
        "id": 10,
        "name": "Mệnh đề & Liên từ (Clauses & Conjunctions)",
        "name_en": "Clauses & Conjunctions",
        "icon": "ph-bold ph-intersect",
        "badge": "Mệnh đề quan hệ",
        "badge_color": "success",
        "desc": "Relative clauses (Mệnh đề quan hệ), Noun clauses, Adverb clauses, Defining/Non-defining, because/although/while/if/unless.",
        "keywords": ["Mệnh đề & Liên từ", "Clauses & Conjunctions", "Mệnh đề", "Liên từ", "Relative clauses"],
        "subtopics": ["Relative clauses", "Noun clauses", "Adverb clauses", "Defining / Non-defining", "because / although / while...", "if / unless..."]
    },
    {
        "id": 11,
        "name": "Cấu trúc câu nâng cao (Advanced Structures)",
        "name_en": "Advanced Structures",
        "icon": "ph-bold ph-sparkle",
        "badge": "Điểm 700+ TOEIC",
        "badge_color": "dark",
        "desc": "Conditional sentences (If 1,2,3), Wish / If only, Reported speech (Gián tiếp), Inversion (Đảo ngữ), Cleft sentences, Subjunctive.",
        "keywords": ["Cấu trúc câu nâng cao", "Advanced Structures", "Nâng cao", "Điều kiện", "Đảo ngữ", "Inversion", "Wish", "Subjunctive"],
        "subtopics": ["Conditional sentences", "Wish / If only", "Reported speech", "Inversion (Đảo ngữ)", "Cleft sentences", "Subjunctive"]
    },
    {
        "id": 12,
        "name": "Cấu trúc đặc biệt & Ngữ pháp ứng dụng",
        "name_en": "Special Structures & Applied Grammar",
        "icon": "ph-bold ph-puzzle-piece",
        "badge": "Ngữ pháp ứng dụng",
        "badge_color": "warning",
        "desc": "Question forms, Tag questions (Hỏi đuôi), Imperatives, There is/are, Used to / Be used to, Would rather, Both/Either/Neither.",
        "keywords": ["Cấu trúc đặc biệt", "Ngữ pháp ứng dụng", "Special Structures", "Question forms", "Tag questions", "Used to"],
        "subtopics": ["Question forms", "Tag questions", "There is / There are", "Used to / Be used to", "Would rather / Had better", "Both / Either / Neither"]
    }
]


@bp.route("/grammar")
@login_required
def grammar_overview():
    ensure_initial_grammar_topics()

    q = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    level = request.args.get("level", "").strip()
    difficulty = request.args.get("difficulty", "").strip()
    status = request.args.get("status", "").strip()
    exam = request.args.get("exam", "").strip()
    toeic_weight = request.args.get("toeic_weight", "").strip()
    tab = request.args.get("tab", "").strip()  # "categories" or "topics"

    all_topics = GrammarTopic.query.filter_by(is_active=True).all()
    user_progress = GrammarProgress.query.filter_by(user_id=current_user.id).all()
    completed_ids = {p.topic_id for p in user_progress if p.is_completed}
    favorite_ids = {p.topic_id for p in user_progress if p.is_favorite}

    # Find matched category if category is specified
    selected_category = None
    if category:
        selected_category = next(
            (c for c in GRAMMAR_12_CATEGORIES if c["name"].lower() == category.lower() or any(k.lower() in category.lower() for k in c["keywords"])),
            None
        )

    # Determine view mode: "categories" (12 big categories grid) or "topics" (subtopics list)
    if category or q or exam or level or difficulty or status or tab == "topics":
        view_mode = "topics"
    else:
        view_mode = "categories"

    # Compute statistics for 12 categories
    categories_catalog = []
    for c in GRAMMAR_12_CATEGORIES:
        c_copy = dict(c)
        c_topics = [
            t for t in all_topics
            if t.category == c["name"] or any(k.lower() in (t.category or "").lower() for k in c["keywords"])
        ]
        c_copy["topic_count"] = len(c_topics)
        c_copy["completed_count"] = sum(1 for t in c_topics if t.id in completed_ids)
        c_copy["progress"] = int(c_copy["completed_count"] / c_copy["topic_count"] * 100) if c_copy["topic_count"] > 0 else 0
        categories_catalog.append(c_copy)

    # Query for subtopics
    query = GrammarTopic.query.filter_by(is_active=True)
    if q:
        query = query.filter(GrammarTopic.title.ilike(f"%{q}%") | GrammarTopic.summary.ilike(f"%{q}%"))
    if category:
        if selected_category:
            cat_filters = [GrammarTopic.category == category, GrammarTopic.category == selected_category["name"]]
            cat_filters.extend([GrammarTopic.category.ilike(f"%{k}%") for k in selected_category["keywords"]])
            query = query.filter(or_(*cat_filters))
        else:
            query = query.filter_by(category=category)
    if level:
        query = query.filter_by(level=level)
    if difficulty:
        query = query.filter_by(difficulty=difficulty)
    if exam:
        if exam.upper() in ["TOEIC_HIGH", "TOEIC-HIGH"]:
            query = query.filter(GrammarTopic.exam_targets.ilike("%TOEIC%"), GrammarTopic.toeic_weight == "High")
        else:
            query = query.filter(GrammarTopic.exam_targets.ilike(f"%{exam}%"))
    if toeic_weight:
        query = query.filter_by(toeic_weight=toeic_weight)

    # Sort primarily by order_index, then level, then id
    topics_list = query.order_by(
        GrammarTopic.order_index.asc(),
        GrammarTopic.level.asc(),
        GrammarTopic.id.asc()
    ).all()

    if status == "completed":
        topics_list = [t for t in topics_list if t.id in completed_ids]
    elif status == "favorite":
        topics_list = [t for t in topics_list if t.id in favorite_ids]
    elif status == "new":
        topics_list = [t for t in topics_list if t.id not in completed_ids]

    total_topics = len(all_topics)
    completed_count = len(completed_ids)
    favorite_count = len(favorite_ids)

    # Count for Goal Badges
    toeic_high_count = sum(1 for t in all_topics if "TOEIC" in (t.exam_targets or "") and t.toeic_weight == "High")
    toeic_total_count = sum(1 for t in all_topics if "TOEIC" in (t.exam_targets or ""))

    # Distinct categories in DB for fallback
    categories = [r[0] for r in db.session.query(GrammarTopic.category).distinct().all()]

    return render_template(
        "learning/grammar.html",
        view_mode=view_mode,
        categories_catalog=categories_catalog,
        selected_category=selected_category,
        topics=topics_list,
        categories=categories,
        q=q,
        category=category,
        level=level,
        difficulty=difficulty,
        status=status,
        exam=exam,
        toeic_weight=toeic_weight,
        completed_ids=completed_ids,
        favorite_ids=favorite_ids,
        total_topics=total_topics,
        completed_count=completed_count,
        favorite_count=favorite_count,
        toeic_high_count=toeic_high_count,
        toeic_total_count=toeic_total_count,
    )


@bp.route("/grammar/toeic")
@login_required
def grammar_toeic():
    """Quick direct link to TOEIC grammar section"""
    return redirect(url_for("learning.grammar_overview", exam="TOEIC"))


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


@bp.route("/grammar/reference/<int:rule_id>/export-pdf")
@login_required
def grammar_rule_export_pdf(rule_id):
    import io
    from xhtml2pdf import pisa
    rule = db.session.get(GrammarRule, rule_id)
    if not rule:
        flash("Không tìm thấy quy tắc ngữ pháp.", "danger")
        return redirect(url_for("learning.grammar_reference_index"))

    html = render_template("learning/grammar_rule_export_pdf.html", rule=rule, now=datetime.utcnow())
    pdf_buffer = io.BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=pdf_buffer)
    if pisa_status.err:
        flash("Có lỗi khi tạo tệp PDF.", "danger")
        return redirect(url_for("learning.grammar_rule_detail", rule_id=rule.id))

    pdf_buffer.seek(0)
    filename = f"Grammar_Rule_{rule.id}.pdf"
    return send_file(
        pdf_buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename
    )


@bp.route("/grammar/reference/<int:rule_id>/export-docx")
@login_required
def grammar_rule_export_docx(rule_id):
    import io
    import docx
    from docx.shared import Pt

    rule = db.session.get(GrammarRule, rule_id)
    if not rule:
        flash("Không tìm thấy quy tắc ngữ pháp.", "danger")
        return redirect(url_for("learning.grammar_reference_index"))

    doc = docx.Document()
    doc.add_heading(rule.title, level=0)

    meta_p = doc.add_paragraph()
    meta_p.add_run(f"Danh mục: {rule.category} | Nền tảng EnglishMate\n").italic = True
    meta_p.add_run(f"Ngày xuất: {datetime.utcnow().strftime('%d/%m/%Y')}").font.size = Pt(9)

    doc.add_heading("Tóm tắt quy tắc", level=1)
    doc.add_paragraph(rule.summary or "Không có tóm tắt")

    doc.add_heading("1. Giải thích chi tiết", level=1)
    doc.add_paragraph(rule.explanation or "Không có nội dung")

    if rule.examples:
        doc.add_heading("2. Ví dụ minh họa", level=1)
        doc.add_paragraph(rule.examples)

    if rule.exceptions:
        doc.add_heading("3. Trường hợp ngoại lệ", level=1)
        doc.add_paragraph(rule.exceptions)

    if rule.common_errors:
        doc.add_heading("4. Các lỗi thường gặp", level=1)
        doc.add_paragraph(rule.common_errors)

    doc.add_paragraph("\n---\nTài liệu học tập được tạo tự động từ hệ thống EnglishMate")

    docx_buffer = io.BytesIO()
    doc.save(docx_buffer)
    docx_buffer.seek(0)

    filename = f"Grammar_Rule_{rule.id}.docx"
    return send_file(
        docx_buffer,
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        as_attachment=True,
        download_name=filename
    )


@bp.route("/grammar/reference/export-pdf")
@login_required
def grammar_handbook_export_pdf():
    import io
    from xhtml2pdf import pisa
    category = request.args.get("category", "").strip()
    query = GrammarRule.query
    if category and category != "all":
        query = query.filter_by(category=category)
    rules = query.order_by(GrammarRule.category, GrammarRule.id).all()

    html = render_template(
        "learning/grammar_handbook_export_pdf.html",
        rules=rules,
        selected_category=category if category != "all" else None,
        now=datetime.utcnow()
    )
    pdf_buffer = io.BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=pdf_buffer)
    if pisa_status.err:
        flash("Có lỗi khi tạo tệp PDF Sổ tay.", "danger")
        return redirect(url_for("learning.grammar_reference_index"))

    pdf_buffer.seek(0)
    cat_slug = f"_{category}" if category and category != "all" else ""
    filename = f"EnglishMate_So_Tay_Ngu_Phap{cat_slug}.pdf"
    return send_file(
        pdf_buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename
    )


@bp.route("/grammar/reference/export-docx")
@login_required
def grammar_handbook_export_docx():
    import io
    import docx

    category = request.args.get("category", "").strip()
    query = GrammarRule.query
    if category and category != "all":
        query = query.filter_by(category=category)
    rules = query.order_by(GrammarRule.category, GrammarRule.id).all()

    doc = docx.Document()
    doc.add_heading("SỔ TAY TRA CỨU NGỮ PHÁP TIẾNG ANH", level=0)
    sub = doc.add_paragraph(f"Tổng hợp các quy tắc chuẩn · EnglishMate Handbook\nNgày phát hành: {datetime.utcnow().strftime('%d/%m/%Y')}")
    sub.italic = True

    for idx, rule in enumerate(rules, 1):
        doc.add_heading(f"{idx}. {rule.title} ({rule.category})", level=1)
        doc.add_paragraph(f"Tóm tắt: {rule.summary}")
        doc.add_heading("Giải thích chi tiết:", level=2)
        doc.add_paragraph(rule.explanation or "")
        if rule.examples:
            doc.add_heading("Ví dụ:", level=2)
            doc.add_paragraph(rule.examples)
        if rule.exceptions:
            doc.add_heading("Ngoại lệ:", level=2)
            doc.add_paragraph(rule.exceptions)
        if rule.common_errors:
            doc.add_heading("Lỗi thường gặp:", level=2)
            doc.add_paragraph(rule.common_errors)
        doc.add_paragraph("")

    docx_buffer = io.BytesIO()
    doc.save(docx_buffer)
    docx_buffer.seek(0)

    cat_slug = f"_{category}" if category and category != "all" else ""
    filename = f"EnglishMate_So_Tay_Ngu_Phap{cat_slug}.docx"
    return send_file(
        docx_buffer,
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        as_attachment=True,
        download_name=filename
    )


# ==========================================
