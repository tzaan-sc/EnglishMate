import random

from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import func

from ...extensions import db
from ..auth.models import record_daily_activity
from .models import (Lesson, LessonProgress, Question, QuizAttempt, QuizAttemptAnswer,
                       Vocabulary, VocabularyProgress)
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
    learned = {p.vocabulary_id for p in VocabularyProgress.query.filter_by(user_id=current_user.id)
               .filter(VocabularyProgress.learned_count > 0).all()}
    topics = [r[0] for r in db.session.query(Vocabulary.topic).distinct().order_by(Vocabulary.topic).all()]
    return render_template("learning/vocabulary.html", words=query.order_by(Vocabulary.word).all(),
                           learned=learned, topics=topics, search=search, level=level, topic=topic, form=ActionForm())


@bp.post("/vocabulary/<int:word_id>/learn")
@login_required
def learn_word(word_id):
    word = db.get_or_404(Vocabulary, word_id)
    form = ActionForm()
    if not form.validate_on_submit():
        abort(400)
    progress = VocabularyProgress.query.filter_by(user_id=current_user.id, vocabulary_id=word.id).first()
    if not progress:
        progress = VocabularyProgress(user_id=current_user.id, vocabulary_id=word.id)
        db.session.add(progress)
    progress.learned_count += 1
    progress.last_reviewed_at = func.now()
    db.session.commit()
    flash(f"Đã thêm “{word.word}” vào từ đã học.", "success")
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
        progress = VocabularyProgress(user_id=current_user.id, vocabulary_id=word.id)
        db.session.add(progress)
    if action == "known":
        progress.learned_count += 1
    else:
        progress.review_count += 1
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
        
    return render_template("learning/flashcard_create.html")


@bp.get("/flashcard-sets/<int:set_id>")
@login_required
def flashcard_set_view(set_id):
    from .models import FlashcardSet
    fset = FlashcardSet.query.get_or_404(set_id)
    # Check permissions
    if not fset.is_public and fset.user_id != current_user.id:
        abort(403)
    return render_template("learning/flashcard_view.html", fset=fset)
