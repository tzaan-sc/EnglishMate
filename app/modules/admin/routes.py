from functools import wraps

from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from ...extensions import db
from ..auth.models import User
from ..learning.models import Lesson, Question, QuizAttempt, Vocabulary
from . import bp
from .forms import ConfirmForm, LessonForm, VocabularyForm


def admin_required(view):
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return view(*args, **kwargs)
    return wrapped


@bp.get("")
@bp.get("/")
@admin_required
def dashboard():
    stats = {"users": User.query.count(), "lessons": Lesson.query.filter_by(is_active=True).count(),
             "words": Vocabulary.query.count(), "questions": Question.query.count(), "attempts": QuizAttempt.query.count()}
    return render_template("admin/dashboard.html", stats=stats)


@bp.get("/lessons")
@admin_required
def lessons():
    return render_template("admin/lessons.html", lessons=Lesson.query.order_by(Lesson.id.desc()).all(), form=ConfirmForm())


@bp.route("/lessons/new", methods=["GET", "POST"])
@admin_required
def lesson_create():
    form = LessonForm()
    if form.validate_on_submit():
        lesson = Lesson()
        form.populate_obj(lesson)
        db.session.add(lesson)
        db.session.commit()
        flash("Đã thêm bài học mới.", "success")
        return redirect(url_for("admin.lessons"))
    return render_template("admin/lesson_form.html", form=form, title="Thêm bài học")


@bp.route("/lessons/<int:lesson_id>/edit", methods=["GET", "POST"])
@admin_required
def lesson_edit(lesson_id):
    lesson = db.get_or_404(Lesson, lesson_id)
    form = LessonForm(obj=lesson)
    if form.validate_on_submit():
        form.populate_obj(lesson)
        db.session.commit()
        flash("Đã cập nhật bài học.", "success")
        return redirect(url_for("admin.lessons"))
    return render_template("admin/lesson_form.html", form=form, title="Sửa bài học")


@bp.post("/lessons/<int:lesson_id>/delete")
@admin_required
def lesson_delete(lesson_id):
    form = ConfirmForm()
    if not form.validate_on_submit():
        abort(400)
    lesson = db.get_or_404(Lesson, lesson_id)
    lesson.is_active = False
    db.session.commit()
    flash("Đã ẩn bài học (dữ liệu tiến độ vẫn được giữ nguyên).", "info")
    return redirect(url_for("admin.lessons"))


@bp.get("/vocabulary")
@admin_required
def vocabulary():
    search, level = request.args.get("q", "").strip(), request.args.get("level", "")
    query = Vocabulary.query
    if search:
        query = query.filter(Vocabulary.word.ilike(f"%{search}%"))
    if level:
        query = query.filter_by(level=level)
    return render_template("admin/vocabulary.html", words=query.order_by(Vocabulary.id.desc()).all(),
                           search=search, level=level, form=ConfirmForm())


@bp.route("/vocabulary/new", methods=["GET", "POST"])
@admin_required
def vocabulary_create():
    form = VocabularyForm()
    if form.validate_on_submit():
        word = Vocabulary()
        form.populate_obj(word)
        db.session.add(word)
        db.session.commit()
        flash("Đã thêm từ vựng mới.", "success")
        return redirect(url_for("admin.vocabulary"))
    return render_template("admin/vocabulary_form.html", form=form, title="Thêm từ vựng")


@bp.route("/vocabulary/<int:word_id>/edit", methods=["GET", "POST"])
@admin_required
def vocabulary_edit(word_id):
    word = db.get_or_404(Vocabulary, word_id)
    form = VocabularyForm(obj=word)
    if form.validate_on_submit():
        form.populate_obj(word)
        db.session.commit()
        flash("Đã cập nhật từ vựng.", "success")
        return redirect(url_for("admin.vocabulary"))
    return render_template("admin/vocabulary_form.html", form=form, title="Sửa từ vựng")


@bp.post("/vocabulary/<int:word_id>/delete")
@admin_required
def vocabulary_delete(word_id):
    form = ConfirmForm()
    if not form.validate_on_submit():
        abort(400)
    word = db.get_or_404(Vocabulary, word_id)
    if word.progress_records:
        flash("Không thể xóa từ đã có dữ liệu học tập.", "warning")
    else:
        db.session.delete(word)
        db.session.commit()
        flash("Đã xóa từ vựng.", "info")
    return redirect(url_for("admin.vocabulary"))


@bp.get("/users")
@admin_required
def users():
    search = request.args.get("q", "").strip()
    query = User.query
    if search:
        query = query.filter((User.username.ilike(f"%{search}%")) | (User.email.ilike(f"%{search}%")))
    return render_template("admin/users.html", users=query.order_by(User.created_at.desc()).all(), search=search, form=ConfirmForm())


@bp.post("/users/<int:user_id>/toggle")
@admin_required
def user_toggle(user_id):
    form = ConfirmForm()
    if not form.validate_on_submit():
        abort(400)
    user = db.get_or_404(User, user_id)
    if user.id == current_user.id:
        flash("Bạn không thể tự khóa tài khoản của chính mình.", "danger")
    else:
        user.is_active = not user.is_active
        db.session.commit()
        flash("Đã cập nhật trạng thái tài khoản.", "success")
    return redirect(url_for("admin.users"))


@bp.post("/users/<int:user_id>/toggle-role")
@admin_required
def user_toggle_role(user_id):
    form = ConfirmForm()
    if not form.validate_on_submit():
        abort(400)
    user = db.get_or_404(User, user_id)
    if user.id == current_user.id:
        flash("Bạn không thể tự đổi vai trò của chính mình.", "danger")
    else:
        user.role = "USER" if user.role == "ADMIN" else "ADMIN"
        db.session.commit()
        flash(f"Đã chuyển vai trò tài khoản {user.username} thành {user.role}.", "success")
    return redirect(url_for("admin.users"))


# --- EXAM UPLOAD SYSTEM (GIAI ĐOẠN 3) ---
import os
import pandas as pd
from werkzeug.utils import secure_filename
from app.modules.exams.services import import_exam_from_dataframe
from flask import jsonify

UPLOAD_FOLDER = os.path.join('app', 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@bp.route("/exams/upload", methods=["GET", "POST"])
@admin_required
def exam_upload():
    if request.method == "POST":
        file = request.files.get("file")
        category = request.form.get("category", "TOEIC")
        title = request.form.get("title", "Đề thi mới")
        duration = int(request.form.get("duration", 120))
        
        if not file or file.filename == '':
            flash("Vui lòng chọn một file.", "danger")
            return redirect(url_for("admin.exam_upload"))
            
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        try:
            if filename.endswith('.json'):
                df = pd.read_json(filepath, orient='records')
            else:
                df = pd.read_excel(filepath)
                
            exam = import_exam_from_dataframe(df, category, title, duration)
            flash(f"Đã import thành công {len(df)} câu hỏi vào đề thi '{exam.title}'.", "success")
        except Exception as e:
            flash(f"Lỗi khi xử lý file: {str(e)}", "danger")
            
        # Clean up
        if os.path.exists(filepath):
            os.remove(filepath)
            
        return redirect(url_for("admin.exam_upload"))
        
    return render_template("admin/exam_upload.html")


@bp.post("/exams/preview")
@admin_required
def exam_preview():
    file = request.files.get("file")
    if not file or file.filename == '':
        return jsonify({"success": False, "error": "Không tìm thấy file"}), 400
        
    try:
        if file.filename.endswith('.json'):
            df = pd.read_json(file, orient='records')
        else:
            df = pd.read_excel(file)
            
        # Convert first 5 rows to dict for preview
        # Handle NaN values safely
        preview_data = df.head(10).where(pd.notnull(df), None).to_dict(orient='records')
        
        return jsonify({
            "success": True,
            "total_rows": len(df),
            "preview": preview_data,
            "columns": list(df.columns)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
