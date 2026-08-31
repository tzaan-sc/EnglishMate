import os
from functools import wraps

from flask import abort, flash, redirect, render_template, request, url_for, jsonify, send_from_directory
from flask_login import current_user, login_required

from ...extensions import db
from ..auth.models import User
from ..exams.models import Exam
from ..learning.models import Lesson, Question, QuizAttempt, Vocabulary, GrammarTopic
from . import bp
from .forms import ConfirmForm, LessonForm, VocabularyForm
from .importer import parse_and_validate_excel, commit_import_records, CONTENT_SCHEMAS


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
    all_roles = Role.query.order_by(Role.id.asc()).all()
    return render_template("admin/users.html", users=query.order_by(User.created_at.desc()).all(), roles=all_roles, search=search, form=ConfirmForm())


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
        act_str = "MỞ KHÓA" if user.is_active else "KHÓA"
        log_audit_action(current_user.id, "TOGGLE_USER_STATUS", "User", user.id, f"{act_str} tài khoản {user.username}")
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
        log_audit_action(current_user.id, "TOGGLE_ROLE", "User", user.id, f"Đổi vai trò {user.username} thành {user.role}")
        flash(f"Đã chuyển vai trò tài khoản {user.username} thành {user.role}.", "success")
    return redirect(url_for("admin.users"))


# --- ROLE & PERMISSION MANAGEMENT (MỤC 1.6) ---
from datetime import datetime
from .models import AuditLog, Permission, Role, RolePermission, UserRole
from .utils import log_audit_action, permission_required, has_permission


@bp.route("/roles", methods=["GET", "POST"])
@admin_required
def roles():
    if request.method == "POST":
        role_name = request.form.get("name", "").strip().upper()
        description = request.form.get("description", "").strip()
        parent_id = request.form.get("parent_id")
        parent_id = int(parent_id) if parent_id and parent_id.isdigit() else None
        selected_perms = request.form.getlist("permissions")

        if not role_name:
            flash("Tên vai trò không được để trống.", "danger")
        elif Role.query.filter_by(name=role_name).first():
            flash(f"Vai trò '{role_name}' đã tồn tại.", "danger")
        else:
            role = Role(name=role_name, description=description, is_custom=True, parent_id=parent_id)
            db.session.add(role)
            db.session.commit()

            for perm_id in selected_perms:
                if perm_id.isdigit():
                    rp = RolePermission(role_id=role.id, permission_id=int(perm_id))
                    db.session.add(rp)
            db.session.commit()

            log_audit_action(current_user.id, "CREATE_ROLE", "Role", role.id, f"Khởi tạo vai trò tùy chỉnh '{role_name}'")
            flash(f"Đã khởi tạo vai trò tùy chỉnh '{role_name}' thành công.", "success")
            return redirect(url_for("admin.roles"))

    roles_list = Role.query.order_by(Role.is_custom.asc(), Role.id.asc()).all()
    permissions_list = Permission.query.order_by(Permission.category.asc(), Permission.id.asc()).all()

    templates = {
        "MODERATOR_TEMP": {
            "name": "Mẫu Quản trị Nội dung (Content Moderator)",
            "perm_names": ["lessons:read", "lessons:write", "vocabulary:manage", "exams:manage"]
        },
        "SECURITY_TEMP": {
            "name": "Mẫu Cảnh báo & An ninh (Security Admin)",
            "perm_names": ["users:manage", "roles:manage", "audit:read"]
        },
        "FULL_ADMIN_TEMP": {
            "name": "Mẫu Toàn quyền Quản trị (Full Admin)",
            "perm_names": [p.name for p in permissions_list]
        }
    }

    return render_template(
        "admin/roles.html",
        roles=roles_list,
        permissions=permissions_list,
        templates=templates,
        form=ConfirmForm()
    )


@bp.post("/roles/<int:role_id>/edit")
@admin_required
def role_edit(role_id):
    role = db.get_or_404(Role, role_id)
    description = request.form.get("description", "").strip()
    parent_id = request.form.get("parent_id")
    parent_id = int(parent_id) if parent_id and parent_id.isdigit() else None
    selected_perms = request.form.getlist("permissions")

    if parent_id == role.id:
        parent_id = None

    role.description = description
    role.parent_id = parent_id

    RolePermission.query.filter_by(role_id=role.id).delete()

    for perm_id in selected_perms:
        if perm_id.isdigit():
            rp = RolePermission(role_id=role.id, permission_id=int(perm_id))
            db.session.add(rp)

    db.session.commit()
    log_audit_action(current_user.id, "UPDATE_ROLE", "Role", role.id, f"Cập nhật vai trò '{role.name}'")
    flash(f"Đã cập nhật quyền hạn cho vai trò '{role.name}'.", "success")
    return redirect(url_for("admin.roles"))


@bp.post("/roles/<int:role_id>/delete")
@admin_required
def role_delete(role_id):
    form = ConfirmForm()
    if not form.validate_on_submit():
        abort(400)
    role = db.get_or_404(Role, role_id)
    if not role.is_custom:
        flash("Không thể xóa các vai trò mặc định của hệ thống.", "danger")
    else:
        role_name = role.name
        db.session.delete(role)
        db.session.commit()
        log_audit_action(current_user.id, "DELETE_ROLE", "Role", role_id, f"Xóa vai trò '{role_name}'")
        flash(f"Đã xóa vai trò '{role_name}'.", "info")
    return redirect(url_for("admin.roles"))


@bp.post("/users/<int:user_id>/assign-role")
@admin_required
def user_assign_role(user_id):
    user = db.get_or_404(User, user_id)
    role_id = request.form.get("role_id")
    expiry_date_str = request.form.get("expires_at", "").strip()

    if not role_id or not role_id.isdigit():
        flash("Vai trò không hợp lệ.", "danger")
        return redirect(url_for("admin.users"))

    role = db.get_or_404(Role, int(role_id))
    expires_at = None
    if expiry_date_str:
        try:
            expires_at = datetime.strptime(expiry_date_str, "%Y-%m-%d")
        except ValueError:
            pass

    UserRole.query.filter_by(user_id=user.id).delete()
    ur = UserRole(user_id=user.id, role_id=role.id, expires_at=expires_at)
    db.session.add(ur)

    user.role = role.name
    db.session.commit()

    expiry_msg = f" (Hết hạn: {expires_at.strftime('%d/%m/%Y')})" if expires_at else " (Vĩnh viễn)"
    log_audit_action(current_user.id, "ASSIGN_ROLE", "User", user.id, f"Gán vai trò '{role.name}' cho {user.username}{expiry_msg}")
    flash(f"Đã gán vai trò '{role.name}' cho học viên {user.username}{expiry_msg}.", "success")
    return redirect(url_for("admin.users"))


@bp.get("/audit-logs")
@admin_required
def audit_logs():
    search = request.args.get("q", "").strip()
    action_filter = request.args.get("action", "").strip()

    query = AuditLog.query
    if search:
        query = query.join(User, AuditLog.user_id == User.id, isouter=True).filter(
            (User.username.ilike(f"%{search}%")) | (AuditLog.details.ilike(f"%{search}%")) | (AuditLog.ip_address.ilike(f"%{search}%"))
        )
    if action_filter:
        query = query.filter_by(action=action_filter)

    logs = query.order_by(AuditLog.created_at.desc()).limit(100).all()
    actions = db.session.query(AuditLog.action).distinct().all()
    action_list = [a[0] for a in actions]

    return render_template("admin/audit_logs.html", logs=logs, search=search, action_filter=action_filter, actions=action_list)


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


# ==========================================
# ADMIN EXAM MANAGEMENT ROUTES (Section 4.5)
# ==========================================

def ensure_initial_admin_exams():
    if Exam.query.count() > 0:
        return

    sample_exams = [
        Exam(
            title="Đề Thi Thử TOEIC Mô Phỏng Full 200 Câu",
            category="TOEIC",
            duration_minutes=120,
            difficulty="Medium",
            question_bank="TOEIC Bank",
            selection_type="random",
            question_count=200,
            is_published=True
        ),
        Exam(
            title="Đề Luyện Thi IELTS Academic Reading & Writing",
            category="IELTS",
            duration_minutes=60,
            difficulty="Hard",
            question_bank="IELTS Bank",
            selection_type="manual",
            selected_question_ids="1,2,3,4,5",
            question_count=40,
            is_published=True
        ),
        Exam(
            title="Đề Kiểm Tra Phân Loại Đầu Vào (Placement Test)",
            category="Placement",
            duration_minutes=45,
            difficulty="Medium",
            question_bank="Grammar & Vocabulary",
            selection_type="random",
            question_count=50,
            is_published=True
        )
    ]
    db.session.add_all(sample_exams)
    db.session.commit()


@bp.route("/exams")
@admin_required
def exams_list():
    ensure_initial_admin_exams()
    exams_data = Exam.query.order_by(Exam.id.desc()).all()

    total_exams = len(exams_data)
    published_count = sum(1 for e in exams_data if e.is_published)
    total_attempts = QuizAttempt.query.count()

    stats_overview = {
        "total_exams": total_exams,
        "published_count": published_count,
        "draft_count": total_exams - published_count,
        "total_attempts": total_attempts
    }

    return render_template(
        "admin/exams.html",
        exams=exams_data,
        stats=stats_overview,
        form=ConfirmForm()
    )


@bp.route("/exams/new", methods=["GET", "POST"])
@admin_required
def exam_create():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        category = request.form.get("category", "Custom").strip()
        duration_minutes = int(request.form.get("duration_minutes", 15))
        difficulty = request.form.get("difficulty", "Medium").strip()
        question_bank = request.form.get("question_bank", "General").strip()
        selection_type = request.form.get("selection_type", "random").strip()
        selected_ids = request.form.get("selected_question_ids", "").strip()
        question_count = int(request.form.get("question_count", 10))
        is_published = bool(request.form.get("is_published"))

        if not title:
            flash("Vui lòng nhập tiêu đề đề thi.", "danger")
            return render_template("admin/exam_form.html", title="Tạo đề thi mới", form=ConfirmForm())

        exam = Exam(
            title=title,
            category=category,
            duration_minutes=duration_minutes,
            difficulty=difficulty,
            question_bank=question_bank,
            selection_type=selection_type,
            selected_question_ids=selected_ids,
            question_count=question_count,
            is_published=is_published
        )
        db.session.add(exam)
        db.session.commit()

        flash(f"Đã tạo đề thi '{exam.title}' thành công!", "success")
        return redirect(url_for("admin.exams_list"))

    return render_template("admin/exam_form.html", title="Tạo đề thi mới", exam=None, form=ConfirmForm())


@bp.route("/exams/<int:exam_id>/edit", methods=["GET", "POST"])
@admin_required
def exam_edit(exam_id):
    exam = db.get_or_404(Exam, exam_id)

    if request.method == "POST":
        exam.title = request.form.get("title", exam.title).strip()
        exam.category = request.form.get("category", exam.category).strip()
        exam.duration_minutes = int(request.form.get("duration_minutes", exam.duration_minutes))
        exam.difficulty = request.form.get("difficulty", exam.difficulty).strip()
        exam.question_bank = request.form.get("question_bank", exam.question_bank).strip()
        exam.selection_type = request.form.get("selection_type", exam.selection_type).strip()
        exam.selected_question_ids = request.form.get("selected_question_ids", "").strip()
        exam.question_count = int(request.form.get("question_count", exam.question_count))
        exam.is_published = bool(request.form.get("is_published"))

        db.session.commit()
        flash(f"Đã cập nhật đề thi '{exam.title}'.", "success")
        return redirect(url_for("admin.exams_list"))

    return render_template("admin/exam_form.html", title="Chỉnh sửa đề thi", exam=exam, form=ConfirmForm())


@bp.post("/exams/<int:exam_id>/publish")
@admin_required
def exam_toggle_publish(exam_id):
    exam = db.get_or_404(Exam, exam_id)
    exam.is_published = not exam.is_published
    db.session.commit()

    msg = f"Đã xuất bản đề thi '{exam.title}'." if exam.is_published else f"Đã chuyển đề thi '{exam.title}' về trạng thái nháp."
    flash(msg, "info")
    return redirect(url_for("admin.exams_list"))


@bp.post("/exams/<int:exam_id>/delete")
@admin_required
def exam_delete(exam_id):
    exam = db.get_or_404(Exam, exam_id)
    title = exam.title
    db.session.delete(exam)
    db.session.commit()

    flash(f"Đã xóa đề thi '{title}' thành công.", "success")
    return redirect(url_for("admin.exams_list"))


@bp.route("/exams/<int:exam_id>/preview")
@admin_required
def exam_detail_preview(exam_id):
    exam = db.get_or_404(Exam, exam_id)
    questions = Question.query.limit(exam.question_count).all()

    return render_template("admin/exam_preview.html", exam=exam, questions=questions)


@bp.route("/exams/<int:exam_id>/stats")
@admin_required
def exam_stats_analytics(exam_id):
    exam = db.get_or_404(Exam, exam_id)
    attempts = QuizAttempt.query.filter_by(topic=exam.title).order_by(QuizAttempt.created_at.desc()).all()
    if not attempts:
        attempts = QuizAttempt.query.order_by(QuizAttempt.created_at.desc()).limit(10).all()

    total_att = len(attempts)
    avg_score = round(sum(a.score for a in attempts) / total_att, 1) if total_att > 0 else 0
    total_q = sum(a.total_questions for a in attempts)
    avg_acc = int((sum(a.score for a in attempts) / total_q) * 100) if total_q > 0 else 0
    pass_count = sum(1 for a in attempts if (a.score / a.total_questions) >= 0.6) if total_q > 0 else 0
    pass_rate = int((pass_count / total_att) * 100) if total_att > 0 else 0
    avg_duration = int(sum(a.duration_seconds or 0 for a in attempts) / total_att) if total_att > 0 else 0

    analytics = {
        "total_attempts": total_att,
        "avg_score": avg_score,
        "avg_acc": avg_acc,
        "pass_count": pass_count,
        "pass_rate": pass_rate,
        "avg_duration": avg_duration
    }

    return render_template("admin/exam_stats.html", exam=exam, attempts=attempts, analytics=analytics)


# --- EXCEL CONTENT IMPORT HUB ---

@bp.get("/import")
@admin_required
def import_hub():
    stats = {
        "vocabulary_count": Vocabulary.query.count(),
        "grammar_count": GrammarTopic.query.count(),
        "lessons_count": Lesson.query.count(),
        "questions_count": Question.query.count(),
        "exams_count": Exam.query.count()
    }
    return render_template("admin/import_hub.html", schemas=CONTENT_SCHEMAS, stats=stats)


@bp.get("/import/template/<content_type>")
@admin_required
def download_import_template(content_type):
    from ...utils.template_generator import generate_all_templates, TEMPLATE_DIR, JSON_TEMPLATE_DIR
    if not os.path.exists(TEMPLATE_DIR) or len(os.listdir(TEMPLATE_DIR)) < 5:
        generate_all_templates()

    fmt = request.args.get("format", "xlsx").lower()
    base_dir = JSON_TEMPLATE_DIR if fmt == "json" else TEMPLATE_DIR
    ext = "json" if fmt == "json" else "xlsx"

    filename_map = {
        "vocabulary": f"template_vocabulary.{ext}",
        "grammar": f"template_grammar.{ext}",
        "lessons": f"template_lessons.{ext}",
        "questions": f"template_questions.{ext}",
        "exams": f"template_exams.{ext}",
    }
    filename = filename_map.get(content_type)
    if not filename or not os.path.exists(os.path.join(base_dir, filename)):
        abort(404)

    return send_from_directory(
        base_dir,
        filename,
        as_attachment=True,
        download_name=f"englishmate_{filename}"
    )


@bp.post("/import/validate")
@admin_required
def validate_import_file():
    if "file" not in request.files:
        return jsonify({"success": False, "error": "Vui lòng chọn file Excel hoặc JSON để upload."}), 400

    uploaded_file = request.files["file"]
    content_type = request.form.get("content_type", "").strip()

    if not uploaded_file or uploaded_file.filename == "":
        return jsonify({"success": False, "error": "Chưa chọn file."}), 400

    fname = uploaded_file.filename.lower()
    if not (fname.endswith(".xlsx") or fname.endswith(".json")):
        return jsonify({"success": False, "error": "Chỉ chấp nhận file định dạng Excel (.xlsx) hoặc JSON (.json)."}), 400

    from .importer import parse_and_validate_file
    result = parse_and_validate_file(uploaded_file, uploaded_file.filename, content_type)
    if not result["success"]:
        return jsonify(result), 400

    return jsonify(result)


@bp.post("/import/commit")
@admin_required
def commit_import():
    data = request.get_json() or {}
    content_type = data.get("content_type")
    valid_records = data.get("valid_records", [])
    mode = data.get("mode", "insert_or_update")

    if not content_type or not valid_records:
        return jsonify({"success": False, "error": "Không có dữ liệu hợp lệ để import."}), 400

    try:
        res = commit_import_records(
            content_type=content_type,
            valid_records=valid_records,
            user_id=current_user.id,
            mode=mode
        )
        return jsonify(res)
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": f"Lỗi khi lưu vào Database: {str(e)}"}), 500

