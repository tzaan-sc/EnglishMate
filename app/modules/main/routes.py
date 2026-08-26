from datetime import date, timedelta
from flask import render_template
from flask_login import current_user, login_required
from sqlalchemy import func

from ...extensions import db
from ..auth.models import DailyActivity
from ..learning.models import Lesson, LessonProgress, QuizAttempt, VocabularyProgress
from . import bp


@bp.get("/")
def index():
    return render_template("main/index.html")


@bp.get("/dashboard")
@login_required
def dashboard():
    current_user.get_current_streak()

    completed = LessonProgress.query.filter_by(user_id=current_user.id).count()
    attempts = QuizAttempt.query.filter_by(user_id=current_user.id).all()
    learned = VocabularyProgress.query.filter_by(user_id=current_user.id).filter(VocabularyProgress.learned_count > 0).count()
    completed_ids = [row[0] for row in db.session.execute(db.select(LessonProgress.lesson_id).where(LessonProgress.user_id == current_user.id)).all()]
    next_lesson = Lesson.query.filter(Lesson.is_active.is_(True), ~Lesson.id.in_(completed_ids or [-1])).first()
    lessons = Lesson.query.filter_by(is_active=True).all()
    average = round(sum(a.score / a.total_questions * 100 for a in attempts) / len(attempts)) if attempts else 0

    # Calculate 7 days of current week (T2 to CN)
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())
    labels = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]
    activities = DailyActivity.query.filter(
        DailyActivity.user_id == current_user.id,
        DailyActivity.activity_date >= start_of_week,
        DailyActivity.activity_date <= start_of_week + timedelta(days=6)
    ).all()
    completed_dates = {act.activity_date for act in activities if act.goal_completed}

    week_days = []
    for i in range(7):
        day_date = start_of_week + timedelta(days=i)
        week_days.append((labels[i], day_date in completed_dates))

    return render_template("main/dashboard.html", completed=completed, attempts=len(attempts), average=average,
                           learned=learned, next_lesson=next_lesson, lessons=lessons, completed_ids=completed_ids,
                           week_days=week_days)


@bp.get("/how-to-learn")
def how_to_learn():
    return render_template("main/how_to_learn.html")


@bp.get("/faq")
def faq():
    return render_template("main/faq.html")

