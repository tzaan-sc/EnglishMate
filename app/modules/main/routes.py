import os
import uuid
from datetime import date, timedelta
from pathlib import Path

from flask import current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, logout_user
from sqlalchemy import func

from ...extensions import db
from ..auth.models import DailyActivity, User
from ..auth.routes import log_dev_otp_code
from ..learning.models import Lesson, LessonProgress, QuizAttempt, VocabularyProgress
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

    return render_template("main/dashboard.html", completed=completed, attempts=len(attempts), average=average,
                           learned=learned, next_lesson=next_lesson, lessons=lessons, completed_ids=completed_ids,
                           week_days=week_days)


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

    return render_template(
        "main/profile.html",
        profile_form=profile_form,
        email_form=email_form,
        verify_email_form=verify_email_form,
        password_form=password_form,
        delete_form=delete_form,
        show_verify_modal=show_verify_modal,
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

