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
    search = request.args.get("search", request.args.get("q", "")).strip()
    skill = request.args.get("skill", "").strip()
    level = request.args.get("level", "").strip()
    status = request.args.get("status", "").strip()

    query = Lesson.query
    if search:
        query = query.filter(Lesson.title.ilike(f"%{search}%") | Lesson.short_description.ilike(f"%{search}%"))
    if skill and skill != "All":
        query = query.filter(Lesson.skill.ilike(skill))
    if level and level != "All":
        query = query.filter_by(level=level)
    if status == "active":
        query = query.filter_by(is_active=True)
    elif status == "hidden":
        query = query.filter_by(is_active=False)

    total_count = Lesson.query.count()
    active_count = Lesson.query.filter_by(is_active=True).count()
    hidden_count = total_count - active_count

    lessons_list = query.order_by(Lesson.id.desc()).all()
    return render_template(
        "admin/lessons.html",
        lessons=lessons_list,
        form=ConfirmForm(),
        search=search,
        skill=skill,
        level=level,
        status=status,
        total_count=total_count,
        active_count=active_count,
        hidden_count=hidden_count,
    )


def _extract_skill_data(skill, form_data):
    import json
    data = {}
    if skill == "Listening":
        data["audio_url"] = form_data.get("audio_url", "").strip()
        data["accent"] = form_data.get("accent", "US").strip()
        data["audio_duration"] = form_data.get("audio_duration", "").strip()
        data["transcript"] = form_data.get("listening_transcript", "").strip()
    elif skill == "Reading":
        data["reading_genre"] = form_data.get("reading_genre", "").strip()
        data["passage"] = form_data.get("reading_passage", "").strip()
        q_raw = form_data.get("reading_questions_json", "").strip()
        if q_raw:
            try:
                data["questions"] = json.loads(q_raw)
            except Exception:
                pass
    elif skill == "Speaking":
        data["speaking_genre"] = form_data.get("speaking_genre", "").strip()
        sent_raw = form_data.get("speaking_sentences_json", "").strip()
        if sent_raw:
            try:
                if sent_raw.startswith("["):
                    data["sentences"] = json.loads(sent_raw)
                else:
                    parsed = []
                    for idx, line in enumerate(sent_raw.splitlines()):
                        line = line.strip()
                        if not line:
                            continue
                        parts = [p.strip() for p in line.split("|")]
                        parsed.append({
                            "idx": idx + 1,
                            "text": parts[0],
                            "ipa": parts[1] if len(parts) > 1 else "",
                            "vi": parts[2] if len(parts) > 2 else ""
                        })
                    data["sentences"] = parsed
            except Exception:
                pass
        data["tips"] = [t.strip() for t in form_data.get("speaking_tips", "").splitlines() if t.strip()]
    elif skill == "Writing":
        data["writing_genre"] = form_data.get("writing_genre", "").strip()
        try:
            data["min_words"] = int(form_data.get("min_words", 40))
        except (ValueError, TypeError):
            data["min_words"] = 40
        try:
            data["max_words"] = int(form_data.get("max_words", 80))
        except (ValueError, TypeError):
            data["max_words"] = 80
        tpl_raw = form_data.get("writing_templates_json", "").strip()
        if tpl_raw:
            try:
                if tpl_raw.startswith("["):
                    data["templates"] = json.loads(tpl_raw)
                else:
                    parsed = []
                    for line in tpl_raw.splitlines():
                        line = line.strip()
                        if not line:
                            continue
                        parts = [p.strip() for p in line.split("|")]
                        parsed.append({
                            "label": parts[0],
                            "text": parts[1] if len(parts) > 1 else "",
                            "vi": parts[2] if len(parts) > 2 else ""
                        })
                    data["templates"] = parsed
            except Exception:
                pass
    return data


@bp.route("/lessons/new", methods=["GET", "POST"])
@admin_required
def lesson_create():
    form = LessonForm()
    if form.validate_on_submit():
        lesson = Lesson()
        form.populate_obj(lesson)
        lesson.skill_data = _extract_skill_data(lesson.skill, request.form)
        db.session.add(lesson)
        db.session.commit()
        flash("Đã thêm bài học mới.", "success")
        return redirect(url_for("admin.lessons"))
    return render_template("admin/lesson_form.html", form=form, title="Thêm bài học", skill_data={})


@bp.route("/lessons/<int:lesson_id>/edit", methods=["GET", "POST"])
@admin_required
def lesson_edit(lesson_id):
    lesson = db.get_or_404(Lesson, lesson_id)
    form = LessonForm(obj=lesson)
    if form.validate_on_submit():
        form.populate_obj(lesson)
        lesson.skill_data = _extract_skill_data(lesson.skill, request.form)
        db.session.commit()
        flash("Đã cập nhật bài học.", "success")
        return redirect(url_for("admin.lessons"))
    return render_template(
        "admin/lesson_form.html",
        form=form,
        title="Sửa bài học",
        lesson=lesson,
        skill_data=lesson.skill_data or {}
    )


@bp.get("/lessons/<int:lesson_id>/quick-preview")
@admin_required
def lesson_quick_preview(lesson_id):
    from flask import jsonify
    lesson = db.get_or_404(Lesson, lesson_id)
    return jsonify({
        "id": lesson.id,
        "title": lesson.title,
        "skill": lesson.skill,
        "level": lesson.level,
        "short_description": lesson.short_description or "",
        "content_preview": lesson.content or "",
        "examples": lesson.examples or "",
        "url": lesson.url,
        "edit_url": url_for("admin.lesson_edit", lesson_id=lesson.id),
    })


@bp.post("/lessons/<int:lesson_id>/toggle-status")
@bp.post("/lessons/<int:lesson_id>/delete")
@admin_required
def lesson_delete(lesson_id):
    form = ConfirmForm()
    if not form.validate_on_submit():
        abort(400)
    lesson = db.get_or_404(Lesson, lesson_id)
    lesson.is_active = not lesson.is_active
    db.session.commit()
    msg = f"Đã kích hoạt mở lại bài học '{lesson.title}'." if lesson.is_active else f"Đã ẩn bài học '{lesson.title}' (dữ liệu tiến độ vẫn được giữ nguyên)."
    flash(msg, "success" if lesson.is_active else "info")
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


def _get_exam_questions(exam):
    """Lấy danh sách câu hỏi chuẩn xác cho đề thi."""
    # 1. Kiểm tra câu hỏi trực tiếp liên kết qua ExamQuestion
    direct_questions = exam.questions.all()
    if direct_questions:
        return direct_questions

    # 2. Kiểm tra danh sách ID được cấu hình trong selected_question_ids
    if exam.selected_question_ids:
        try:
            ids = [int(x.strip()) for x in exam.selected_question_ids.split(",") if x.strip().isdigit()]
            if ids:
                matched = Question.query.filter(Question.id.in_(ids)).all()
                if matched:
                    return matched
        except Exception:
            pass

    # 3. Lọc câu hỏi theo Question Bank hoặc Category
    bank_name = exam.question_bank or exam.category
    if bank_name and bank_name != "General":
        matched_by_bank = Question.query.filter(Question.topic.ilike(f"%{bank_name}%")).limit(exam.question_count).all()
        if matched_by_bank:
            return matched_by_bank

    # 4. Fallback theo độ khó
    matched_by_diff = Question.query.filter(Question.level == exam.difficulty).limit(exam.question_count).all()
    if matched_by_diff:
        return matched_by_diff

    return Question.query.limit(exam.question_count).all()


@bp.route("/exams")
@admin_required
def exams_list():
    ensure_initial_admin_exams()
    search = request.args.get("search", request.args.get("q", "")).strip()
    category = request.args.get("category", "").strip()
    difficulty = request.args.get("difficulty", "").strip()
    status = request.args.get("status", "").strip()

    query = Exam.query.filter_by(is_active=True)
    if search:
        query = query.filter(Exam.title.ilike(f"%{search}%") | Exam.question_bank.ilike(f"%{search}%"))
    if category and category != "All":
        query = query.filter_by(category=category)
    if difficulty and difficulty != "All":
        query = query.filter_by(difficulty=difficulty)
    if status == "published":
        query = query.filter_by(is_published=True)
    elif status == "draft":
        query = query.filter_by(is_published=False)

    total_exams = Exam.query.filter_by(is_active=True).count()
    published_count = Exam.query.filter_by(is_active=True, is_published=True).count()
    draft_count = total_exams - published_count
    total_attempts = QuizAttempt.query.count()

    stats_overview = {
        "total_exams": total_exams,
        "published_count": published_count,
        "draft_count": draft_count,
        "total_attempts": total_attempts
    }

    exams_data = query.order_by(Exam.id.desc()).all()

    # Danh mục phong phú theo chuẩn hệ thống
    default_categories = ["TOEIC", "IELTS", "TOEFL", "Placement", "Progress", "Timed", "Mock", "Custom"]
    existing_cats = [c[0] for c in db.session.query(Exam.category).filter(Exam.is_active==True).distinct().all() if c[0]]
    all_categories = sorted(list(set(default_categories + existing_cats)))

    return render_template(
        "admin/exams.html",
        exams=exams_data,
        stats=stats_overview,
        search=search,
        category=category,
        difficulty=difficulty,
        status=status,
        all_categories=all_categories,
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

        # Cấu hình ma trận Part cho đề thi TOEIC
        part_dist = None
        if category == "TOEIC":
            try:
                p5 = int(request.form.get("part5_count", 30))
                p6 = int(request.form.get("part6_count", 16))
                p7 = int(request.form.get("part7_count", 54))
                part_dist = {"part5": p5, "part6": p6, "part7": p7}
                question_count = p5 + p6 + p7
                if duration_minutes <= 15:
                    duration_minutes = 75  # Chuẩn TOEIC Reading
            except (ValueError, TypeError):
                part_dist = {"part5": 30, "part6": 16, "part7": 54}
                question_count = 100

        if not title:
            flash("Vui lòng nhập tiêu đề đề thi.", "danger")
            return render_template("admin/exam_form.html", title="Tạo đề thi mới", exam=None, form=ConfirmForm())

        exam = Exam(
            title=title,
            category=category,
            duration_minutes=duration_minutes,
            difficulty=difficulty,
            question_bank=question_bank,
            selection_type=selection_type,
            selected_question_ids=selected_ids,
            part_distribution=part_dist,
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
        exam.is_published = bool(request.form.get("is_published"))

        if exam.category == "TOEIC":
            try:
                p5 = int(request.form.get("part5_count", 30))
                p6 = int(request.form.get("part6_count", 16))
                p7 = int(request.form.get("part7_count", 54))
                exam.part_distribution = {"part5": p5, "part6": p6, "part7": p7}
                exam.question_count = p5 + p6 + p7
            except (ValueError, TypeError):
                pass
        else:
            exam.question_count = int(request.form.get("question_count", exam.question_count))

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


@bp.post("/exams/<int:exam_id>/toggle-publish-ajax")
@admin_required
def exam_toggle_publish_ajax(exam_id):
    from flask import jsonify
    exam = db.get_or_404(Exam, exam_id)
    exam.is_published = not exam.is_published
    db.session.commit()

    total_exams = Exam.query.filter_by(is_active=True).count()
    published_count = Exam.query.filter_by(is_active=True, is_published=True).count()
    draft_count = total_exams - published_count

    return jsonify({
        "success": True,
        "is_published": exam.is_published,
        "status_label": "Đã xuất bản" if exam.is_published else "Bản nháp",
        "total_exams": total_exams,
        "published_count": published_count,
        "draft_count": draft_count,
        "msg": f"Đã xuất bản '{exam.title}'." if exam.is_published else f"Đã chuyển '{exam.title}' về trạng thái nháp."
    })


@bp.get("/exams/<int:exam_id>/quick-preview")
@admin_required
def exam_quick_preview(exam_id):
    from flask import jsonify
    exam = db.get_or_404(Exam, exam_id)
    questions = _get_exam_questions(exam)

    samples = []
    for idx, q in enumerate(questions[:4]):
        q_text = getattr(q, "question_text", None) or getattr(q, "question", "")
        opt_a = getattr(q, "option_a", "")
        opt_b = getattr(q, "option_b", "")
        opt_c = getattr(q, "option_c", "")
        opt_d = getattr(q, "option_d", "")
        ans = getattr(q, "correct_answer", None) or getattr(q, "correct_option", "")
        samples.append({
            "idx": idx + 1,
            "text": q_text,
            "options": [opt_a, opt_b, opt_c, opt_d],
            "correct": ans
        })

    return jsonify({
        "success": True,
        "id": exam.id,
        "title": exam.title,
        "category": exam.category,
        "duration_minutes": exam.duration_minutes,
        "difficulty": exam.difficulty,
        "question_count": exam.question_count,
        "is_published": exam.is_published,
        "part_distribution": exam.part_distribution or {},
        "total_fetched": len(questions),
        "samples": samples,
        "edit_url": url_for("admin.exam_edit", exam_id=exam.id),
        "stats_url": url_for("admin.exam_stats_analytics", exam_id=exam.id),
        "full_preview_url": url_for("admin.exam_detail_preview", exam_id=exam.id),
    })


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
    questions = _get_exam_questions(exam)

    return render_template("admin/exam_preview.html", exam=exam, questions=questions)


@bp.route("/exams/<int:exam_id>/stats")
@admin_required
def exam_stats_analytics(exam_id):
    exam = db.get_or_404(Exam, exam_id)
    # Lấy chính xác các lượt làm bài cho đề thi này (không mượn bài khác)
    attempts = QuizAttempt.query.filter_by(topic=exam.title).order_by(QuizAttempt.created_at.desc()).all()

    total_att = len(attempts)
    if total_att == 0:
        # Zero State sạch sẽ: Không fake data!
        analytics = {
            "total_attempts": 0,
            "avg_score": 0,
            "avg_acc": 0,
            "pass_count": 0,
            "pass_rate": 0,
            "avg_duration": 0
        }
    else:
        avg_score = round(sum(a.score for a in attempts) / total_att, 1)
        total_q = sum(a.total_questions for a in attempts)
        avg_acc = int((sum(a.score for a in attempts) / total_q) * 100) if total_q > 0 else 0
        pass_count = sum(1 for a in attempts if (a.score / a.total_questions) >= 0.6) if total_q > 0 else 0
        pass_rate = int((pass_count / total_att) * 100)
        avg_duration = int(sum(a.duration_seconds or 0 for a in attempts) / total_att)

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
    from ...utils.template_generator import generate_all_templates, TEMPLATE_DIR, JSON_TEMPLATE_DIR, CSV_TEMPLATE_DIR
    if not os.path.exists(TEMPLATE_DIR) or len(os.listdir(TEMPLATE_DIR)) < 5 or not os.path.exists(CSV_TEMPLATE_DIR):
        generate_all_templates()

    fmt = request.args.get("format", "xlsx").lower()
    if fmt == "json":
        base_dir = JSON_TEMPLATE_DIR
        ext = "json"
    elif fmt == "csv":
        base_dir = CSV_TEMPLATE_DIR
        ext = "csv"
    else:
        base_dir = TEMPLATE_DIR
        ext = "xlsx"

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

    extra_kwargs = {}
    if ext == "csv":
        extra_kwargs["mimetype"] = "text/csv; charset=utf-8"

    return send_from_directory(
        base_dir,
        filename,
        as_attachment=True,
        download_name=f"englishmate_{filename}",
        **extra_kwargs
    )


@bp.post("/import/validate")
@admin_required
def validate_import_file():
    if "file" not in request.files:
        return jsonify({"success": False, "error": "Vui lòng chọn file Excel, CSV hoặc JSON để upload."}), 400

    uploaded_file = request.files["file"]
    content_type = request.form.get("content_type", "").strip()

    if not uploaded_file or uploaded_file.filename == "":
        return jsonify({"success": False, "error": "Chưa chọn file."}), 400

    fname = uploaded_file.filename.lower()
    if not (fname.endswith(".xlsx") or fname.endswith(".json") or fname.endswith(".csv")):
        return jsonify({"success": False, "error": "Chỉ chấp nhận file định dạng Excel (.xlsx), CSV (.csv) hoặc JSON (.json)."}), 400

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

