import os
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path

from flask import current_app, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, logout_user
from sqlalchemy import func

from ...extensions import db
from ..auth.models import DailyActivity, User, UserSession
from ..auth.routes import log_dev_otp_code
from ..learning.models import (FlashcardProgress, GrammarProgress, GrammarTopic, Lesson,
                               LessonProgress, QuizAttempt, Vocabulary, VocabularyProgress)
from . import bp
from .forms import ChangeEmailForm, ChangePasswordForm, DeleteAccountForm, EditProfileForm, VerifyNewEmailForm


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

    # 1. Skill-specific progress
    total_vocab = Vocabulary.query.count() or 1
    vocab_pct = min(100, int((learned / total_vocab) * 100))
    
    total_grammar_topics = GrammarTopic.query.count() or 1
    user_grammar_completed = GrammarProgress.query.filter_by(user_id=current_user.id, is_completed=True).count()
    grammar_pct = min(100, int((user_grammar_completed / total_grammar_topics) * 100))
    
    reading_lessons_total = Lesson.query.filter_by(is_active=True, skill="Reading").count() or 1
    reading_completed = LessonProgress.query.join(Lesson).filter(LessonProgress.user_id == current_user.id, Lesson.skill == "Reading").count()
    reading_pct = min(100, int((reading_completed / reading_lessons_total) * 100))
    
    listening_lessons_total = Lesson.query.filter_by(is_active=True, skill="Listening").count() or 1
    listening_completed = LessonProgress.query.join(Lesson).filter(LessonProgress.user_id == current_user.id, Lesson.skill == "Listening").count()
    listening_pct = min(100, int((listening_completed / listening_lessons_total) * 100))
    
    skills_progress = [
        {"name": "Từ vựng", "icon": "ph-book-open", "color": "success", "pct": vocab_pct, "stat": f"{learned}/{total_vocab} từ"},
        {"name": "Ngữ pháp", "icon": "ph-books", "color": "purple", "pct": grammar_pct, "stat": f"{user_grammar_completed}/{total_grammar_topics} chủ đề"},
        {"name": "Đọc hiểu", "icon": "ph-article", "color": "primary", "pct": reading_pct, "stat": f"{reading_completed}/{reading_lessons_total} bài"},
        {"name": "Nghe hiểu", "icon": "ph-headphones", "color": "warning", "pct": listening_pct, "stat": f"{listening_completed}/{listening_lessons_total} bài"},
    ]

    # Skill balance (percentages)
    skill_balance = {
        "từ vựng": vocab_pct,
        "ngữ pháp": grammar_pct,
        "đọc hiểu": reading_pct,
        "nghe hiểu": listening_pct,
    }

    # Level info
    level_info = current_user.get_level_info()
    level_start_date = current_user.level_start_date
    level_progress_pct = level_info.get('progress_pct', 0)
    needed_xp = level_info.get('needed_xp', 0)

    # Estimate completion date based on average daily XP
    all_acts = DailyActivity.query.filter_by(user_id=current_user.id).all()
    total_xp_from_acts = sum(
        (a.completed_lessons * 20) + (50 if current_user.daily_reward_claimed_date == a.activity_date else 0)
        for a in all_acts
    )
    active_days = len({a.activity_date for a in all_acts}) or 1
    daily_xp_avg = total_xp_from_acts / active_days if active_days else 0
    if daily_xp_avg > 0:
        days_needed = int((needed_xp + daily_xp_avg - 1) // daily_xp_avg)  # ceil
        estimated_completion_date = (date.today() + timedelta(days=days_needed)).strftime('%d/%m/%Y')
    else:
        estimated_completion_date = "-"

    # 2. Time spent learning
    today_act = DailyActivity.query.filter_by(user_id=current_user.id, activity_date=today).first()
    today_lessons = today_act.completed_lessons if today_act else 0
    today_time_spent_minutes = today_lessons * 15 + (10 if today_act else 0)
    
    weekly_acts = DailyActivity.query.filter(
        DailyActivity.user_id == current_user.id,
        DailyActivity.activity_date >= start_of_week
    ).all()
    weekly_time_spent_minutes = sum((a.completed_lessons * 15 + 10) for a in weekly_acts)
    
    all_acts = DailyActivity.query.filter_by(user_id=current_user.id).all()
    total_time_spent_minutes = sum((a.completed_lessons * 15 + 10) for a in all_acts) or (completed * 15)
    total_time_hours = round(total_time_spent_minutes / 60, 1)

    # 3. Activity Heatmap (Calendar Year like GitHub, e.g. 2026)
    selected_year = request.args.get("year", type=int) or today.year
    available_years = [today.year, today.year - 1, today.year - 2]

    # Calendar Year Start and End (Jan 1 to Dec 31)
    year_start = date(selected_year, 1, 1)
    year_end = date(selected_year, 12, 31)

    # Align start to Monday of that week and end to Sunday
    cal_start = year_start - timedelta(days=year_start.weekday())
    cal_end = year_end + timedelta(days=(6 - year_end.weekday()))
    total_days = (cal_end - cal_start).days + 1

    heatmap_acts = {
        act.activity_date: act.completed_lessons
        for act in DailyActivity.query.filter(
            DailyActivity.user_id == current_user.id,
            DailyActivity.activity_date >= cal_start,
            DailyActivity.activity_date <= cal_end
        ).all()
    }
    total_yearly_lessons = sum(heatmap_acts.values())

    activity_heatmap = []
    month_labels = []
    last_month = None

    for i in range(total_days):
        d = cal_start + timedelta(days=i)
        is_in_year = (d.year == selected_year)
        cnt = heatmap_acts.get(d, 0)
        lvl = 0
        if cnt >= 5: lvl = 4
        elif cnt >= 3: lvl = 3
        elif cnt >= 2: lvl = 2
        elif cnt >= 1: lvl = 1

        col_index = i // 7
        if is_in_year and d.day <= 7 and d.month != last_month:
            last_month = d.month
            month_names = ["", "Thg 1", "Thg 2", "Thg 3", "Thg 4", "Thg 5", "Thg 6", "Thg 7", "Thg 8", "Thg 9", "Thg 10", "Thg 11", "Thg 12"]
            month_labels.append({
                "name": month_names[d.month],
                "col": col_index
            })

        activity_heatmap.append({
            "date": d.strftime("%d/%m/%Y"),
            "iso_date": d.isoformat(),
            "count": cnt,
            "level": lvl,
            "day_name": d.strftime("%a"),
            "in_year": is_in_year
        })

    # 4. Performance trends (Last 7 attempts)
    recent_attempts = QuizAttempt.query.filter_by(user_id=current_user.id).order_by(QuizAttempt.created_at.desc()).limit(7).all()
    performance_trends = []
    for att in reversed(recent_attempts):
        score_pct = int((att.score / att.total_questions) * 100) if att.total_questions > 0 else 0
        performance_trends.append({
            "topic": att.topic or "Quiz",
            "score_pct": score_pct,
            "date": att.created_at.strftime("%d/%m") if att.created_at else ""
        })

    # 5. Today's Schedule
    srs_due_count = FlashcardProgress.query.filter(
        FlashcardProgress.user_id == current_user.id,
        FlashcardProgress.next_review_at <= func.now()
    ).count() if hasattr(FlashcardProgress, 'next_review_at') else 0
    
    today_schedule = [
        {
            "title": f"Bài học kế tiếp: {next_lesson.title if next_lesson else 'Ôn tập tổng hợp'}",
            "type": "lesson",
            "icon": "ph-graduation-cap",
            "status": "Hoàn thành" if (today_act and today_act.completed_lessons > 0) else "Cần học",
            "is_done": bool(today_act and today_act.completed_lessons > 0),
            "url": url_for("learning.lesson_detail", lesson_id=next_lesson.id) if next_lesson else url_for("learning.lessons")
        },
        {
            "title": f"Ôn tập từ vựng ({srs_due_count} thẻ đến hạn)",
            "type": "vocab",
            "icon": "ph-cards",
            "status": "Đã ôn" if srs_due_count == 0 else "Cần ôn tập",
            "is_done": srs_due_count == 0,
            "url": url_for("learning.game_lobby")
        },
        {
            "title": "Hoàn thành 1 bài Quiz kiểm tra",
            "type": "quiz",
            "icon": "ph-check-square-offset",
            "status": "Đã làm" if len(attempts) > 0 else "Chưa làm",
            "is_done": len(attempts) > 0,
            "url": url_for("learning.quiz")
        }
    ]

    # 6. Today's Achievements
    today_achievements = {
        "xp_today": (today_act.completed_lessons * 20 if today_act else 0) + (50 if current_user.daily_reward_claimed_date == today else 0),
        "streak": current_user.get_current_streak(),
        "longest_streak": current_user.longest_streak or 0,
        "is_daily_goal_done": bool(today_act and today_act.goal_completed),
        "daily_reward_claimed": current_user.daily_reward_claimed_date == today
    }

    # 7. Daily Motivation Quote
    MOTIVATION_QUOTES = [
        {"en": "The secret of getting ahead is getting started.", "vi": "Bí quyết để tiến lên phía trước là hãy bắt đầu ngay hôm nay.", "author": "Mark Twain"},
        {"en": "Live as if you were to die tomorrow. Learn as if you were to live forever.", "vi": "Hãy sống như thể ngày mai bạn sẽ chết. Hãy học như thể bạn sẽ sống mãi mãi.", "author": "Mahatma Gandhi"},
        {"en": "Small daily improvements over time lead to stunning results.", "vi": "Những cải thiện nhỏ mỗi ngày theo thời gian sẽ mang lại kết quả đáng kinh ngạc.", "author": "Robin Sharma"},
        {"en": "A journey of a thousand miles begins with a single step.", "vi": "Hành trình vạn dặm luôn luôn bắt đầu từ một bước chân nhỏ.", "author": "Lao Tzu"},
        {"en": "Don't watch the clock; do what it does. Keep going.", "vi": "Đừng nhìn đồng hồ; hãy làm như nó. Cứ tiếp tục tiến bước.", "author": "Sam Levenson"},
        {"en": "It always seems impossible until it is done.", "vi": "Mọi việc dường như luôn bất khả thi cho đến khi nó được hoàn thành.", "author": "Nelson Mandela"},
    ]
    daily_quote = MOTIVATION_QUOTES[today.timetuple().tm_yday % len(MOTIVATION_QUOTES)]

    return render_template(
        "main/dashboard.html",
        completed=completed,
        attempts=len(attempts),
        average=average,
        learned=learned,
        next_lesson=next_lesson,
        lessons=lessons,
        completed_ids=completed_ids,
        week_days=week_days,
        skills_progress=skills_progress,
        today_time_spent_minutes=today_time_spent_minutes,
        weekly_time_spent_minutes=weekly_time_spent_minutes,
        total_time_hours=total_time_hours,
        activity_heatmap=activity_heatmap,
        month_labels=month_labels,
        total_yearly_lessons=total_yearly_lessons,
        performance_trends=performance_trends,
        today_schedule=today_schedule,
        today_achievements=today_achievements,
        daily_quote=daily_quote,
        srs_due_count=srs_due_count,
        skill_balance=skill_balance,
        level_start_date=level_start_date,
        level_progress_pct=level_progress_pct,
        estimated_completion_date=estimated_completion_date,
        selected_year=selected_year,
        available_years=available_years
    )


@bp.get("/how-to-learn")
def how_to_learn():
    return render_template("main/how_to_learn.html")


@bp.get("/faq")
def faq():
    return render_template("main/faq.html")


@bp.route("/profile", methods=["GET"])
@login_required
def profile():
    profile_form = EditProfileForm(full_name=current_user.full_name or "")
    email_form = ChangeEmailForm()
    verify_email_form = VerifyNewEmailForm()
    password_form = ChangePasswordForm()
    delete_form = DeleteAccountForm()
    show_verify_modal = request.args.get("verify_email") == "1"

    current_session_id = session.get("session_key")
    active_sessions = UserSession.query.filter_by(user_id=current_user.id, is_active=True).order_by(UserSession.last_activity.desc()).all()

    return render_template(
        "main/profile.html",
        profile_form=profile_form,
        email_form=email_form,
        verify_email_form=verify_email_form,
        password_form=password_form,
        delete_form=delete_form,
        show_verify_modal=show_verify_modal,
        active_sessions=active_sessions,
        current_session_id=current_session_id,
    )


@bp.post("/profile/edit-info")
@login_required
def edit_profile_info():
    form = EditProfileForm()
    if form.validate_on_submit():
        if form.full_name.data is not None:
            current_user.full_name = form.full_name.data.strip()

        if form.avatar.data:
            file = form.avatar.data
            ext = os.path.splitext(file.filename)[1].lower()
            filename = f"avatar_{current_user.id}_{uuid.uuid4().hex[:8]}{ext}"
            upload_folder = Path(current_app.root_path) / "static" / "uploads" / "avatars"
            upload_folder.mkdir(parents=True, exist_ok=True)
            file_path = upload_folder / filename
            file.save(file_path)
            current_user.avatar = filename

        db.session.commit()
        flash("Cập nhật thông tin cá nhân thành công!", "success")
    else:
        for error in form.errors.values():
            flash(f"Lỗi: {error[0]}", "danger")

    return redirect(url_for("main.profile"))


@bp.post("/profile/change-email")
@login_required
def change_email_request():
    form = ChangeEmailForm()
    if form.validate_on_submit():
        new_email = form.new_email.data.strip().lower()
        if new_email == current_user.email:
            flash("Email mới trùng với email hiện tại.", "warning")
        elif User.query.filter(User.email == new_email, User.id != current_user.id).first():
            flash("Email này đã được sử dụng bởi tài khoản khác.", "danger")
        else:
            code = current_user.generate_pending_email_otp(new_email)
            db.session.commit()
            log_dev_otp_code(new_email, code)
            flash(f"Mã OTP xác nhận đã được gửi tới email mới <strong>{new_email}</strong>. Vui lòng nhập mã OTP để xác nhận.", "info")
            return redirect(url_for("main.profile", verify_email="1"))
    else:
        for error in form.errors.values():
            flash(f"Lỗi: {error[0]}", "danger")

    return redirect(url_for("main.profile"))


@bp.post("/profile/verify-email")
@login_required
def verify_new_email():
    form = VerifyNewEmailForm()
    if form.validate_on_submit():
        if current_user.verify_pending_email_otp(form.otp_code.data):
            db.session.commit()
            flash("Cập nhật địa chỉ email mới thành công!", "success")
        else:
            flash("Mã OTP không chính xác hoặc đã hết hạn (15 phút). Vui lòng thử lại.", "danger")
            return redirect(url_for("main.profile", verify_email="1"))
    else:
        for error in form.errors.values():
            flash(f"Lỗi: {error[0]}", "danger")

    return redirect(url_for("main.profile"))


@bp.post("/profile/change-password")
@login_required
def profile_change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash("Mật khẩu hiện tại không chính xác.", "danger")
        else:
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash("Đổi mật khẩu thành công!", "success")
    else:
        for error in form.errors.values():
            flash(f"Lỗi: {error[0]}", "danger")

    return redirect(url_for("main.profile"))


@bp.post("/profile/deactivate")
@login_required
def profile_deactivate():
    current_user.is_active = False
    db.session.commit()
    logout_user()
    flash("Tài khoản của bạn đã được vô hiệu hóa tạm thời.", "warning")
    return redirect(url_for("main.index"))


@bp.post("/profile/delete")
@login_required
def profile_delete_account():
    form = DeleteAccountForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.confirm_password.data):
            flash("Mật khẩu xác nhận không chính xác. Xóa tài khoản thất bại.", "danger")
        else:
            user = db.session.get(User, current_user.id)
            logout_user()
            db.session.delete(user)
            db.session.commit()
            flash("Tài khoản của bạn đã được xóa vĩnh viễn khỏi hệ thống.", "info")
            return redirect(url_for("main.index"))
    else:
        for error in form.errors.values():
            flash(f"Lỗi: {error[0]}", "danger")

    return redirect(url_for("main.profile"))


@bp.post("/sessions/revoke/<session_id>")
@login_required
def revoke_session_route(session_id):
    user_sess = UserSession.query.filter_by(id=session_id, user_id=current_user.id).first()
    if user_sess:
        user_sess.is_active = False
        db.session.commit()
        flash("Đã hủy phiên đăng nhập thành công.", "success")
    else:
        flash("Không tìm thấy phiên đăng nhập.", "danger")
    return redirect(url_for("main.profile"))


@bp.post("/sessions/revoke-all")
@login_required
def revoke_all_sessions_route():
    current_key = session.get("session_key")
    sessions = UserSession.query.filter(UserSession.user_id == current_user.id, UserSession.is_active.is_(True)).all()
    count = 0
    for sess in sessions:
        if sess.id != current_key:
            sess.is_active = False
            count += 1
    db.session.commit()
    flash(f"Đã đăng xuất khỏi {count} thiết bị khác.", "success")
    return redirect(url_for("main.profile"))

