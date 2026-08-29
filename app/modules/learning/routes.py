import random
from datetime import date, datetime, timedelta

from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import func

from ...extensions import db
from ..auth.models import record_daily_activity
from .models import (Lesson, LessonProgress, Question, QuizAttempt, QuizAttemptAnswer,
                       Vocabulary, VocabularyProgress, WordReport)
from . import bp
from .forms import ActionForm, QuizStartForm


@bp.get("/lessons")
@login_required
def lessons():
    level, skill = request.args.get("level", ""), request.args.get("skill", "")
    query = Lesson.query.filter_by(is_active=True)
    if level:
        query = query.filter_by(level=level)
    if skill:
        query = query.filter_by(skill=skill)
    done = {p.lesson_id for p in LessonProgress.query.filter_by(user_id=current_user.id).all()}
    return render_template("learning/lessons.html", lessons=query.order_by(Lesson.level, Lesson.id).all(),
                           level=level, skill=skill, done=done)


@bp.get("/lessons/<int:lesson_id>")
@login_required
def lesson_detail(lesson_id):
    lesson = Lesson.query.filter_by(id=lesson_id, is_active=True).first_or_404()
    completed = LessonProgress.query.filter_by(user_id=current_user.id, lesson_id=lesson.id).first()
    return render_template("learning/lesson_detail.html", lesson=lesson, completed=completed, form=ActionForm())


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
    return redirect(url_for("learning.lesson_detail", lesson_id=lesson.id))


@bp.get("/vocabulary")
@login_required
def vocabulary():
    search = request.args.get("q", "").strip()
    level, topic = request.args.get("level", ""), request.args.get("topic", "")
    query = Vocabulary.query
    if search:
        query = query.filter(Vocabulary.word.ilike(f"%{search}%"))
    if level:
        query = query.filter_by(level=level)
    if topic:
        query = query.filter_by(topic=topic)

    all_progress = VocabularyProgress.query.filter_by(user_id=current_user.id).all()
    progress_map = {p.vocabulary_id: p for p in all_progress}
    learned = {p.vocabulary_id for p in all_progress if p.learned_count > 0}

    total_vocab_count = Vocabulary.query.count()
    mastered_count = sum(1 for p in all_progress if p.learned_count >= 3 or p.review_count >= 3)
    learning_count = sum(1 for p in all_progress if (0 < p.learned_count < 3) or (0 < p.review_count < 3))
    new_vocab_count = max(0, total_vocab_count - (mastered_count + learning_count))
    review_vocab_count = sum(1 for p in all_progress if p.review_count > 0 or p.learned_count > 0)

    overall_progress_pct = round(((mastered_count + learning_count) / total_vocab_count * 100)) if total_vocab_count > 0 else 0

    levels = ["A1", "A2", "B1", "B2", "C1", "C2"]
    level_stats = []
    for lvl in levels:
        lvl_total = Vocabulary.query.filter_by(level=lvl).count()
        if lvl_total > 0:
            lvl_words = [v.id for v in Vocabulary.query.filter_by(level=lvl).all()]
            lvl_learned = sum(1 for wid in lvl_words if wid in progress_map and (progress_map[wid].learned_count > 0 or progress_map[wid].review_count > 0))
            lvl_pct = round((lvl_learned / lvl_total) * 100)
            level_stats.append({
                "level": lvl,
                "total": lvl_total,
                "learned": lvl_learned,
                "pct": lvl_pct
            })

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

    topics = [r[0] for r in db.session.query(Vocabulary.topic).distinct().order_by(Vocabulary.topic).all()]
    words_list = query.order_by(Vocabulary.word).all()

    return render_template(
        "learning/vocabulary.html",
        words=words_list,
        learned=learned,
        topics=topics,
        search=search,
        level=level,
        topic=topic,
        form=ActionForm(),
        total_vocab_count=total_vocab_count,
        mastered_count=mastered_count,
        learning_count=learning_count,
        new_vocab_count=new_vocab_count,
        review_vocab_count=review_vocab_count,
        due_words_count=due_words_count,
        overall_progress_pct=overall_progress_pct,
        level_stats=level_stats,
        today_learned_count=today_learned_count,
        today_reviewed_count=today_reviewed_count,
        daily_goal=daily_goal,
        daily_goal_pct=daily_goal_pct,
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


@bp.get("/vocabulary/study")
@login_required
def study_vocabulary():
    level = request.args.get("level", "")
    topic = request.args.get("topic", "")
    try:
        index = int(request.args.get("index", 0))
    except ValueError:
        index = 0

    autoplay = request.args.get("autoplay", "0") == "1"
    show_meaning = request.args.get("show_meaning", "1") == "1"
    mode = request.args.get("mode", "study")

    query = Vocabulary.query
    if level:
        query = query.filter_by(level=level)
    if topic:
        query = query.filter_by(topic=topic)

    words = query.order_by(Vocabulary.id).all()
    if not words:
        flash("Chưa có từ vựng nào thuộc cấp độ hoặc chủ đề này.", "info")
        return redirect(url_for("learning.vocabulary"))

    if index < 0 or index >= len(words):
        index = 0

    current_word = words[index]

    progress = VocabularyProgress.query.filter_by(user_id=current_user.id, vocabulary_id=current_word.id).first()
    is_favorite = progress.is_favorite if progress else False
    is_learned = (progress.learned_count > 0 or progress.review_count > 0) if progress else False

    topics = [r[0] for r in db.session.query(Vocabulary.topic).distinct().order_by(Vocabulary.topic).all()]
    levels = ["A1", "A2", "B1", "B2", "C1", "C2"]

    return render_template(
        "learning/study_vocabulary.html",
        word=current_word,
        index=index,
        total_words=len(words),
        level=level,
        topic=topic,
        autoplay=autoplay,
        show_meaning=show_meaning,
        mode=mode,
        is_favorite=is_favorite,
        is_learned=is_learned,
        topics=topics,
        levels=levels,
        form=ActionForm(),
    )


@bp.post("/vocabulary/<int:word_id>/favorite")
@login_required
def favorite_word(word_id):
    word = db.get_or_404(Vocabulary, word_id)
    progress = VocabularyProgress.query.filter_by(user_id=current_user.id, vocabulary_id=word.id).first()
    if not progress:
        progress = VocabularyProgress(user_id=current_user.id, vocabulary_id=word.id, learned_count=0, review_count=0)
        db.session.add(progress)

    progress.is_favorite = not progress.is_favorite
    db.session.commit()
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


@bp.get("/flashcards")
@login_required
def flashcards():
    level, topic = request.args.get("level", ""), request.args.get("topic", "")
    query = Vocabulary.query
    if level:
        query = query.filter_by(level=level)
    if topic:
        query = query.filter_by(topic=topic)
    words = query.order_by(Vocabulary.id).all()
    topics = [r[0] for r in db.session.query(Vocabulary.topic).distinct().order_by(Vocabulary.topic).all()]
    return render_template("learning/flashcards.html", words=words, topics=topics, level=level,
                           topic=topic, form=ActionForm())


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
        db.session.commit()
        return redirect(url_for("learning.quiz_result", attempt_id=attempt.id))

    form = QuizStartForm()
    topics = [r[0] for r in db.session.query(Question.topic).distinct().order_by(Question.topic).all()]
    form.topic.choices = [("", "Tất cả chủ đề")] + [(t, t) for t in topics]
    level, topic = request.args.get("level", ""), request.args.get("topic", "")
    questions = []
    if request.args.get("start") == "1":
        query = Question.query
        if level:
            query = query.filter_by(level=level)
        if topic:
            query = query.filter_by(topic=topic)
        pool = query.all()
        random.shuffle(pool)
        questions = pool[:10]
        if not questions:
            flash("Chưa có câu hỏi phù hợp với bộ lọc này.", "warning")
    return render_template("learning/quiz.html", form=form, questions=questions, level=level, topic=topic)


@bp.get("/quiz/result/<int:attempt_id>")
@login_required
def quiz_result(attempt_id):
    attempt = QuizAttempt.query.filter_by(id=attempt_id, user_id=current_user.id).first_or_404()
    return render_template("learning/quiz_result.html", attempt=attempt)


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
    from .models import FlashcardSet
    # Lấy các học phần do user tạo hoặc công khai
    sets = FlashcardSet.query.filter(
        (FlashcardSet.user_id == current_user.id) | (FlashcardSet.is_public == True)
    ).order_by(FlashcardSet.created_at.desc()).all()
    return render_template("learning/flashcard_sets.html", sets=sets)


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
        return redirect(url_for("learning.flashcard_sets"))
        
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
            p = FlashcardProgress(user_id=current_user.id, item_id=item_id)
            db.session.add(p)
        p.is_known = is_known
        p.review_count += 1
        p.last_reviewed_at = func.now()

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
    return redirect(url_for("learning.flashcard_sets"))


# ==========================================
# GAME SYSTEM ROUTES
# ==========================================
import uuid
import json
from datetime import datetime, timedelta

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
        FlashcardProgress.last_reviewed_at < now_time - timedelta(hours=24)
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
    
    for item in items:
        p = progress_records.get(item.id)
        is_known = p.is_known if p else False
        if is_known:
            learned_count += 1
            
        if status == "learning" and is_known:
            continue
        if status == "known" and not is_known:
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
    for item in items:
        p = progress_records.get(item.id)
        is_known = p.is_known if p else False
        if status == "learning" and is_known: continue
        if status == "known" and not is_known: continue
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
        
    return {"status": "ok", "game_type": game_data["game_type"], "items": data}

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
