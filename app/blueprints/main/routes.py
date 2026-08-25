from flask import render_template
from flask_login import current_user, login_required
from sqlalchemy import func

from ...extensions import db
from ...models import Lesson, LessonProgress, QuizAttempt, VocabularyProgress
from . import bp


@bp.get("/")
def index():
    return render_template("main/index.html")


@bp.get("/dashboard")
@login_required
def dashboard():
    completed = LessonProgress.query.filter_by(user_id=current_user.id).count()
    attempts = QuizAttempt.query.filter_by(user_id=current_user.id).all()
    learned = VocabularyProgress.query.filter_by(user_id=current_user.id).filter(VocabularyProgress.learned_count > 0).count()
    completed_ids = db.select(LessonProgress.lesson_id).where(LessonProgress.user_id == current_user.id)
    next_lesson = Lesson.query.filter(Lesson.is_active.is_(True), ~Lesson.id.in_(completed_ids)).first()
    average = round(sum(a.score / a.total_questions * 100 for a in attempts) / len(attempts)) if attempts else 0
    return render_template("main/dashboard.html", completed=completed, attempts=len(attempts), average=average,
                           learned=learned, next_lesson=next_lesson)


@bp.get("/how-to-learn")
def how_to_learn():
    return render_template("main/how_to_learn.html")


@bp.get("/faq")
def faq():
    return render_template("main/faq.html")

