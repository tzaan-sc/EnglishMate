from flask import abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import func

from app.extensions import db
from app.modules.exams.models import ToeicTest, ToeicPassage, ToeicQuestion, ToeicAttempt, ToeicAttemptAnswer
from . import bp
from .forms import ActionForm


@bp.get("/toeic")
@login_required
def toeic():
    tests = ToeicTest.query.all()
    attempts = ToeicAttempt.query.filter_by(user_id=current_user.id, is_submitted=True).order_by(ToeicAttempt.completed_at.desc()).all()
    best_scores = {}
    for att in attempts:
        if att.test_id not in best_scores or att.score > best_scores[att.test_id]:
            best_scores[att.test_id] = att.score
    return render_template("exams/toeic_list.html", tests=tests, attempts=attempts, best_scores=best_scores)


@bp.post("/toeic/<int:test_id>/start")
@login_required
def toeic_start(test_id):
    test = db.get_or_404(ToeicTest, test_id)
    attempt = ToeicAttempt(user_id=current_user.id, test_id=test.id, score=0, total_questions=100)
    db.session.add(attempt)
    db.session.commit()
    return redirect(url_for("exams.toeic_attempt", attempt_id=attempt.id))


@bp.get("/toeic/attempt/<int:attempt_id>")
@login_required
def toeic_attempt(attempt_id):
    attempt = ToeicAttempt.query.filter_by(id=attempt_id, user_id=current_user.id).first_or_404()
    if attempt.is_submitted:
        return redirect(url_for("exams.toeic_result", attempt_id=attempt.id))
    
    test = db.get_or_404(ToeicTest, attempt.test_id)
    questions = ToeicQuestion.query.filter_by(test_id=test.id).order_by(ToeicQuestion.question_number).all()
    
    part5_questions = [q for q in questions if q.part == 5]
    
    passages = ToeicPassage.query.filter_by(test_id=test.id).all()
    part6_passages = [p for p in passages if p.part == 6]
    part7_passages = [p for p in passages if p.part == 7]
    
    form = ActionForm()
    return render_template(
        "exams/toeic_attempt.html",
        attempt=attempt,
        test=test,
        part5_questions=part5_questions,
        part6_passages=part6_passages,
        part7_passages=part7_passages,
        form=form
    )


@bp.post("/toeic/attempt/<int:attempt_id>/submit")
@login_required
def toeic_submit(attempt_id):
    attempt = ToeicAttempt.query.filter_by(id=attempt_id, user_id=current_user.id).first_or_404()
    if attempt.is_submitted:
        return redirect(url_for("exams.toeic_result", attempt_id=attempt.id))
    
    form = ActionForm()
    
    test = db.get_or_404(ToeicTest, attempt.test_id)
    questions = ToeicQuestion.query.filter_by(test_id=test.id).all()
    
    score = 0
    time_spent = int(request.form.get("time_spent", 0))
    
    ToeicAttemptAnswer.query.filter_by(attempt_id=attempt.id).delete()
    
    for q in questions:
        selected = request.form.get(f"question_{q.id}")
        if selected:
            selected = selected.strip().upper()
        is_correct = (selected == q.correct_option)
        if is_correct:
            score += 1
        
        ans = ToeicAttemptAnswer(
            attempt_id=attempt.id,
            question_id=q.id,
            selected_option=selected,
            is_correct=is_correct
        )
        db.session.add(ans)
    
    attempt.score = score
    attempt.time_spent = time_spent
    attempt.completed_at = func.now()
    attempt.is_submitted = True
    db.session.commit()
    
    flash("Bài thi của bạn đã được nộp thành công!", "success")
    return redirect(url_for("exams.toeic_result", attempt_id=attempt.id))


@bp.get("/toeic/result/<int:attempt_id>")
@login_required
def toeic_result(attempt_id):
    attempt = ToeicAttempt.query.filter_by(id=attempt_id, user_id=current_user.id).first_or_404()
    if not attempt.is_submitted:
        return redirect(url_for("exams.toeic_attempt", attempt_id=attempt.id))
    
    answers = ToeicAttemptAnswer.query.filter_by(attempt_id=attempt.id).join(ToeicQuestion).order_by(ToeicQuestion.question_number).all()
    
    part_stats = {
        5: {"correct": 0, "total": 0},
        6: {"correct": 0, "total": 0},
        7: {"correct": 0, "total": 0}
    }
    for ans in answers:
        part = ans.question.part
        part_stats[part]["total"] += 1
        if ans.is_correct:
            part_stats[part]["correct"] += 1
            
    test = db.get_or_404(ToeicTest, attempt.test_id)
    
    part5_answers = [a for a in answers if a.question.part == 5]
    
    passages = ToeicPassage.query.filter_by(test_id=test.id).all()
    part6_passages = [p for p in passages if p.part == 6]
    part7_passages = [p for p in passages if p.part == 7]
    
    answer_map = {ans.question_id: ans for ans in answers}
    
    return render_template(
        "exams/toeic_result.html",
        attempt=attempt,
        test=test,
        part5_answers=part5_answers,
        part6_passages=part6_passages,
        part7_passages=part7_passages,
        answer_map=answer_map,
        part_stats=part_stats,
    )


# --- NEW GENERIC EXAM ROUTES ---
from app.modules.exams.models import Exam, ExamQuestion, ExamSubmission, ExamAnswerDetail
import json

@bp.get("/exam")
@login_required
def exam_list():
    category = request.args.get("category", "")
    skill = request.args.get("skill", "")
    
    query = Exam.query.filter_by(is_active=True)
    if category:
        query = query.filter_by(category=category)
    
    # Optional: if skill is provided, filter exams that have questions with this skill
    if skill:
        query = query.join(ExamQuestion).filter(ExamQuestion.skill == skill)
        
    exams = query.all()
    
    # Get user submissions
    submissions = ExamSubmission.query.filter_by(user_id=current_user.id).all()
    best_scores = {}
    for sub in submissions:
        if sub.status == 'COMPLETED':
            if sub.exam_id not in best_scores or sub.total_score > best_scores[sub.exam_id]:
                best_scores[sub.exam_id] = sub.total_score
                
    # Pull scores for TOEIC category exams from ToeicAttempt
    for exam in exams:
        if exam.category.upper() == "TOEIC":
            toeic_test = ToeicTest.query.filter(ToeicTest.title == exam.title).first()
            if not toeic_test:
                toeic_test = ToeicTest.query.first()
            if toeic_test:
                best_attempt = ToeicAttempt.query.filter_by(
                    user_id=current_user.id,
                    test_id=toeic_test.id,
                    is_submitted=True
                ).order_by(ToeicAttempt.score.desc()).first()
                if best_attempt:
                    best_scores[exam.id] = f"{best_attempt.score}/100"

    categories = [r[0] for r in db.session.query(Exam.category).distinct().all()]
    
    return render_template("exams/list.html", exams=exams, best_scores=best_scores, 
                           categories=categories, category=category, skill=skill, history=submissions)


@bp.route("/<int:exam_id>/start", methods=["GET", "POST"])
@login_required
def start_exam(exam_id):
    exam = db.get_or_404(Exam, exam_id)
    # Mode can be 'practice' or 'real'
    mode = request.form.get("mode", "real")
    
    if exam.category.upper() == "TOEIC":
        toeic_test = ToeicTest.query.filter(ToeicTest.title == exam.title).first()
        if not toeic_test:
            toeic_test = ToeicTest.query.first()
        if toeic_test:
            return redirect(url_for("exams.toeic_start", test_id=toeic_test.id), code=307)
            
    submission = ExamSubmission(user_id=current_user.id, exam_id=exam.id, status='IN_PROGRESS', total_score=0)
    db.session.add(submission)
    db.session.commit()
    
    return redirect(url_for("exams.attempt_exam", submission_id=submission.id, mode=mode))


@bp.get("/attempt/<int:submission_id>")
@login_required
def attempt_exam(submission_id):
    submission = ExamSubmission.query.filter_by(id=submission_id, user_id=current_user.id).first_or_404()
    if submission.status == 'COMPLETED':
        return redirect(url_for("exams.exam_result", submission_id=submission.id))
        
    exam = db.get_or_404(Exam, submission.exam_id)
    questions = ExamQuestion.query.filter_by(exam_id=exam.id).order_by(ExamQuestion.id).all()
    
    mode = request.args.get("mode", "real")
    form = ActionForm()
    
    return render_template(
        "exams/attempt.html",
        submission=submission,
        exam=exam,
        questions=questions,
        mode=mode,
        form=form
    )


@bp.post("/attempt/<int:submission_id>/submit")
@login_required
def submit_exam(submission_id):
    submission = ExamSubmission.query.filter_by(id=submission_id, user_id=current_user.id).first_or_404()
    if submission.status == 'COMPLETED':
        return redirect(url_for("exams.exam_result", submission_id=submission.id))
        
    exam = db.get_or_404(Exam, submission.exam_id)
    questions = ExamQuestion.query.filter_by(exam_id=exam.id).all()
    
    total_score = 0
    # Clear previous answers if any
    ExamAnswerDetail.query.filter_by(submission_id=submission.id).delete()
    
    for q in questions:
        selected = request.form.get(f"question_{q.id}")
        is_correct = False
        
        if q.type == 'SINGLE_CHOICE':
            if selected:
                selected = selected.strip().upper()
                is_correct = (selected == q.correct_answer)
                if is_correct:
                    total_score += 1
                    
            ans = ExamAnswerDetail(
                submission_id=submission.id,
                question_id=q.id,
                user_response={"selected": selected},
                is_correct=is_correct,
                score=1 if is_correct else 0
            )
            db.session.add(ans)
        else:
            # For ESSAY or AUDIO_RECORD, we just save the response and set is_correct=None
            ans = ExamAnswerDetail(
                submission_id=submission.id,
                question_id=q.id,
                user_response={"text": selected} if selected else {},
                is_correct=None,
                score=0
            )
            db.session.add(ans)
            
    # Check if there are questions that need AI grading
    needs_grading = any(q.type in ['ESSAY', 'AUDIO_RECORD'] for q in questions)
    
    submission.total_score = total_score
    submission.completed_at = func.now()
    submission.status = 'PENDING' if needs_grading else 'COMPLETED'
    
    db.session.commit()
    
    if needs_grading:
        from app.modules.exams.ai_grading import trigger_ai_grading
        from flask import current_app
        # current_app._get_current_object() is needed to pass the actual app instance to the thread
        trigger_ai_grading(current_app._get_current_object(), submission.id)
        
        flash("Bài thi đã được nộp. Phần tự luận đang được AI chấm điểm, vui lòng quay lại sau ít phút.", "info")
    else:
        flash("Bài thi của bạn đã được nộp thành công!", "success")
        
    return redirect(url_for("exams.exam_result", submission_id=submission.id))


@bp.get("/result/<int:submission_id>")
@login_required
def exam_result(submission_id):
    submission = ExamSubmission.query.filter_by(id=submission_id, user_id=current_user.id).first_or_404()
    
    exam = db.get_or_404(Exam, submission.exam_id)
    answers = ExamAnswerDetail.query.filter_by(submission_id=submission.id).all()
    
    # Create a map of question_id -> answer for easy rendering
    answer_map = {ans.question_id: ans for ans in answers}
    questions = ExamQuestion.query.filter_by(exam_id=exam.id).order_by(ExamQuestion.id).all()
    
    correct_count = sum(1 for ans in answers if ans.is_correct)
    
    return render_template(
        "exams/result.html",
        submission=submission,
        exam=exam,
        questions=questions,
        answer_map=answer_map,
        correct_count=correct_count,
        total_questions=len(questions)
    )


# ==========================================
# SPECIALIZED EXAMS ROUTES (Section 4.6)
# ==========================================

def ensure_specialized_exams_seeded():
    if Exam.query.filter(Exam.category.in_(["Placement", "Progress", "TOEFL", "Mock", "Custom"])).count() > 0:
        return

    special_exams = [
        Exam(
            title="Đề Thi Thử Mô Phỏng TOEIC Full 200 Câu (Listening & Reading)",
            category="TOEIC",
            duration=120,
            duration_minutes=120,
            difficulty="Medium",
            question_bank="TOEIC Bank",
            selection_type="random",
            question_count=200,
            is_published=True,
            is_active=True
        ),
        Exam(
            title="Đề Luyện Thi IELTS Academic (Listening, Reading, Writing & Speaking)",
            category="IELTS",
            duration=150,
            duration_minutes=150,
            difficulty="Hard",
            question_bank="IELTS Bank",
            selection_type="random",
            question_count=40,
            is_published=True,
            is_active=True
        ),
        Exam(
            title="Đề Chuẩn Bị TOEFL iBT Comprehensive Test",
            category="TOEFL",
            duration=120,
            duration_minutes=120,
            difficulty="Hard",
            question_bank="TOEFL Bank",
            selection_type="random",
            question_count=50,
            is_published=True,
            is_active=True
        ),
        Exam(
            title="Bài Kiểm Tra Phân Loại Trình Độ Đầu Vào (Placement Test A1-C2)",
            category="Placement",
            duration=45,
            duration_minutes=45,
            difficulty="Medium",
            question_bank="Placement Bank",
            selection_type="random",
            question_count=30,
            is_published=True,
            is_active=True
        ),
        Exam(
            title="Bài Kiểm Tra Đánh Giá Tiến Độ Học Tập Hàng Tháng (Progress Assessment)",
            category="Progress",
            duration=30,
            duration_minutes=30,
            difficulty="Medium",
            question_bank="Progress Bank",
            selection_type="random",
            question_count=25,
            is_published=True,
            is_active=True
        ),
        Exam(
            title="Đề Thi Thử Tổng Hợp Áp Lực Thời Gian Thật (Full Mock Exam)",
            category="Mock",
            duration=90,
            duration_minutes=90,
            difficulty="Hard",
            question_bank="General Bank",
            selection_type="random",
            question_count=60,
            is_published=True,
            is_active=True
        ),
        Exam(
            title="Kiểm Tra Kỹ Năng Tùy Chỉnh: Ngữ Pháp & Từ Vựng Nâng Cao",
            category="Custom",
            duration=20,
            duration_minutes=20,
            difficulty="Medium",
            question_bank="Grammar & Vocabulary",
            selection_type="random",
            question_count=20,
            is_published=True,
            is_active=True
        )
    ]
    db.session.add_all(special_exams)
    db.session.commit()


@bp.route("/specialized")
@bp.route("/exams/specialized")
@login_required
def specialized_exams_hub():
    ensure_specialized_exams_seeded()

    cat = request.args.get("category", "").strip()
    search = request.args.get("q", "").strip()

    query = Exam.query.filter_by(is_active=True, is_published=True)
    if cat:
        query = query.filter_by(category=cat)
    if search:
        query = query.filter(Exam.title.ilike(f"%{search}%"))

    exams_list_data = query.order_by(Exam.id.desc()).all()

    specialized_categories = [
        {"id": "TOEIC", "name": "Mô phỏng thi TOEIC", "icon": "🎧", "desc": "Đề thi TOEIC Listening & Reading chuẩn định dạng mới 200 câu.", "count": Exam.query.filter_by(category="TOEIC").count()},
        {"id": "IELTS", "name": "Luyện thi IELTS", "icon": "📖", "desc": "Luyện thi IELTS Academic 4 kỹ năng tích hợp chấm điểm AI.", "count": Exam.query.filter_by(category="IELTS").count()},
        {"id": "TOEFL", "name": "Chuẩn bị TOEFL", "icon": "🎓", "desc": "Đề luyện thi chuẩn bị TOEFL iBT dạng bài tổng hợp.", "count": Exam.query.filter_by(category="TOEFL").count()},
        {"id": "Custom", "name": "Kiểm tra Kỹ năng Tùy chỉnh", "icon": "⚡", "desc": "Tùy chọn luyện từng kỹ năng đơn lẻ: Ngữ pháp, Từ vựng, Đọc, Nghe.", "count": Exam.query.filter_by(category="Custom").count()},
        {"id": "Placement", "name": "Kiểm tra Xếp lớp", "icon": "🎯", "desc": "Bài test đánh giá phân loại trình độ đầu vào chuẩn CEFR A1-C2.", "count": Exam.query.filter_by(category="Placement").count()},
        {"id": "Progress", "name": "Đánh giá Tiến độ", "icon": "📈", "desc": "Bài kiểm tra đo lường sự tiến bộ và tốc độ cải thiện kiến thức.", "count": Exam.query.filter_by(category="Progress").count()},
        {"id": "Timed", "name": "Phiên Luyện tập Thời gian", "icon": "⏱️", "desc": "Tùy chỉnh phiên luyện tập giới hạn thời gian thực tế 5 - 60 phút.", "count": 10},
        {"id": "Mock", "name": "Đề Thi Thử Tổng Hợp", "icon": "🏆", "desc": "Đề thi thử tổng hợp mô phỏng áp lực phòng thi thật.", "count": Exam.query.filter_by(category="Mock").count()}
    ]

    return render_template(
        "exams/specialized_hub.html",
        categories=specialized_categories,
        exams=exams_list_data,
        active_cat=cat,
        search_query=search,
        form=ActionForm()
    )


@bp.route("/specialized/placement")
@bp.route("/exams/specialized/placement")
@login_required
def specialized_placement_start():
    ensure_specialized_exams_seeded()
    exam = Exam.query.filter_by(category="Placement", is_active=True).first()
    if not exam:
        exam = Exam.query.first()
    return redirect(url_for("exams.start_exam", exam_id=exam.id))


@bp.route("/specialized/progress")
@bp.route("/exams/specialized/progress")
@login_required
def specialized_progress_start():
    ensure_specialized_exams_seeded()
    exam = Exam.query.filter_by(category="Progress", is_active=True).first()
    if not exam:
        exam = Exam.query.first()
    return redirect(url_for("exams.start_exam", exam_id=exam.id))


@bp.route("/specialized/timed-practice", methods=["GET", "POST"])
@bp.route("/exams/specialized/timed-practice", methods=["GET", "POST"])
@login_required
def specialized_timed_practice():
    if request.method == "POST":
        duration = int(request.form.get("duration", 15))
        question_count = int(request.form.get("question_count", 15))
        difficulty = request.form.get("difficulty", "Medium")
        skill = request.form.get("skill", "General")

        title = f"Phiên Luyện Tập {duration} Phút ({skill} - {difficulty})"
        timed_exam = Exam(
            title=title,
            category="Timed",
            duration=duration,
            duration_minutes=duration,
            difficulty=difficulty,
            question_bank=skill,
            selection_type="random",
            question_count=question_count,
            is_published=True,
            is_active=True
        )
        db.session.add(timed_exam)
        db.session.commit()

        submission = ExamSubmission(user_id=current_user.id, exam_id=timed_exam.id, status='IN_PROGRESS', total_score=0)
        db.session.add(submission)
        db.session.commit()

        return redirect(url_for("exams.attempt_exam", submission_id=submission.id, mode="timed_practice"))

    return render_template("exams/timed_practice.html", form=ActionForm())


# ==========================================
# TEST HISTORY ROUTES (Section 4.7)
# ==========================================

from datetime import datetime
import io
import csv
from flask import Response
from app.modules.learning.models import QuizAttempt, GrammarExerciseAttempt

@bp.route("/history")
@bp.route("/exams/history")
@login_required
def test_history():
    test_type = request.args.get("type", "").strip()
    date_from_str = request.args.get("date_from", "").strip()
    date_to_str = request.args.get("date_to", "").strip()
    min_score_str = request.args.get("min_score", "").strip()
    max_score_str = request.args.get("max_score", "").strip()
    sort_by = request.args.get("sort", "date_desc").strip()

    records = []

    # 1. Fetch QuizAttempt records
    if not test_type or test_type in ["Quiz", "All"]:
        quiz_attempts = QuizAttempt.query.filter_by(user_id=current_user.id).all()
        for q in quiz_attempts:
            total_q = q.total_questions or 10
            score_val = q.score or 0
            acc = int((score_val / total_q) * 100) if total_q > 0 else 0
            records.append({
                "id": q.id,
                "source": "quiz",
                "type": "Quiz",
                "title": q.topic or "Bài Quiz Kiểm Tra",
                "score_display": f"{score_val}/{total_q}",
                "accuracy_pct": acc,
                "duration_sec": q.duration_seconds or 0,
                "created_at": q.created_at,
                "review_url": url_for("learning.quiz_results", attempt_id=q.id)
            })

    # 2. Fetch ToeicAttempt records
    if not test_type or test_type in ["TOEIC", "All"]:
        toeic_attempts = ToeicAttempt.query.filter_by(user_id=current_user.id, is_submitted=True).all()
        for t in toeic_attempts:
            total_q = t.total_questions or 100
            score_val = t.score or 0
            acc = int((score_val / total_q) * 100) if total_q > 0 else 0
            test_title = t.test.title if t.test else "Bài Thi Mô Phỏng TOEIC"
            records.append({
                "id": t.id,
                "source": "toeic",
                "type": "TOEIC",
                "title": test_title,
                "score_display": f"{score_val}/{total_q}",
                "accuracy_pct": acc,
                "duration_sec": t.time_spent or 0,
                "created_at": t.completed_at or t.created_at,
                "review_url": url_for("exams.toeic_result", attempt_id=t.id)
            })

    # 3. Fetch ExamSubmission records
    if not test_type or test_type in ["IELTS", "TOEFL", "Placement", "Progress", "Mock", "Custom", "All"]:
        submissions = ExamSubmission.query.filter_by(user_id=current_user.id).all()
        for s in submissions:
            ex = s.exam
            ex_cat = ex.category if ex else "Exam"
            if test_type and test_type not in ["All", ex_cat]:
                continue
            total_q = ex.question_count if ex else 10
            score_val = int(s.total_score or 0)
            acc = int((score_val / total_q) * 100) if total_q > 0 else 0
            records.append({
                "id": s.id,
                "source": "submission",
                "type": ex_cat,
                "title": ex.title if ex else "Đề Thi Chuyên Biệt",
                "score_display": f"{score_val}/{total_q}",
                "accuracy_pct": acc,
                "duration_sec": (ex.duration_minutes * 60) if ex else 0,
                "created_at": s.completed_at or s.created_at,
                "review_url": url_for("exams.exam_result", submission_id=s.id)
            })

    # 4. Fetch GrammarExerciseAttempt records
    if not test_type or test_type in ["Grammar", "All"]:
        grammar_attempts = GrammarExerciseAttempt.query.filter_by(user_id=current_user.id).all()
        for g in grammar_attempts:
            total_q = g.total_questions or 10
            score_val = g.score or 0
            acc = int((score_val / total_q) * 100) if total_q > 0 else 0
            records.append({
                "id": g.id,
                "source": "grammar",
                "type": "Grammar",
                "title": f"Bài Tập Ngữ Pháp ({g.topic})",
                "score_display": f"{score_val}/{total_q}",
                "accuracy_pct": acc,
                "duration_sec": 0,
                "created_at": g.completed_at,
                "review_url": url_for("learning.grammar_exercise_summary", attempt_id=g.id)
            })

    # Apply date filters
    if date_from_str:
        try:
            d_from = datetime.strptime(date_from_str, "%Y-%m-%d")
            records = [r for r in records if r["created_at"] and r["created_at"].replace(tzinfo=None) >= d_from]
        except ValueError:
            pass

    if date_to_str:
        try:
            d_to = datetime.strptime(date_to_str, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
            records = [r for r in records if r["created_at"] and r["created_at"].replace(tzinfo=None) <= d_to]
        except ValueError:
            pass

    # Apply score range filters
    if min_score_str.isdigit():
        min_s = int(min_score_str)
        records = [r for r in records if r["accuracy_pct"] >= min_s]

    if max_score_str.isdigit():
        max_s = int(max_score_str)
        records = [r for r in records if r["accuracy_pct"] <= max_s]

    # Apply sorting
    if sort_by == "date_asc":
        records.sort(key=lambda r: r["created_at"] or datetime.min)
    elif sort_by == "score_desc":
        records.sort(key=lambda r: r["accuracy_pct"], reverse=True)
    elif sort_by == "score_asc":
        records.sort(key=lambda r: r["accuracy_pct"])
    else: # date_desc
        records.sort(key=lambda r: r["created_at"] or datetime.min, reverse=True)

    # Summary metrics calculation
    total_tests = len(records)
    avg_score_pct = int(sum(r["accuracy_pct"] for r in records) / total_tests) if total_tests > 0 else 0
    best_score_pct = max((r["accuracy_pct"] for r in records), default=0)
    total_time_sec = sum(r["duration_sec"] for r in records)

    summary = {
        "total_tests": total_tests,
        "avg_score_pct": avg_score_pct,
        "best_score_pct": best_score_pct,
        "total_time_min": int(total_time_sec / 60)
    }

    return render_template(
        "exams/test_history.html",
        records=records,
        summary=summary,
        filter_type=test_type,
        date_from=date_from_str,
        date_to=date_to_str,
        min_score=min_score_str,
        max_score=max_score_str,
        sort_by=sort_by,
        form=ActionForm()
    )


@bp.route("/history/review/<string:source>/<int:record_id>")
@bp.route("/exams/history/review/<string:source>/<int:record_id>")
@login_required
def test_review_detail(source, record_id):
    if source == "quiz":
        return redirect(url_for("learning.quiz_results", attempt_id=record_id))
    elif source == "toeic":
        return redirect(url_for("exams.toeic_result", attempt_id=record_id))
    elif source == "submission":
        return redirect(url_for("exams.exam_result", submission_id=record_id))
    elif source == "grammar":
        return redirect(url_for("learning.grammar_exercise_summary", attempt_id=record_id))

    flash("Không tìm thấy bản ghi kiểm tra.", "danger")
    return redirect(url_for("exams.test_history"))


@bp.route("/history/compare")
@bp.route("/exams/history/compare")
@login_required
def test_compare():
    ids_str = request.args.get("ids", "").strip()
    id_list = [id.strip() for id in ids_str.split(",") if id.strip()]

    all_records = []

    for item in id_list:
        parts = item.split("_")
        if len(parts) != 2 or not parts[1].isdigit():
            continue
        src, rec_id = parts[0], int(parts[1])

        if src == "quiz":
            q = db.session.get(QuizAttempt, rec_id)
            if q and q.user_id == current_user.id:
                total_q = q.total_questions or 10
                score_v = q.score or 0
                acc = int((score_v / total_q) * 100) if total_q > 0 else 0
                all_records.append({
                    "id": item,
                    "title": q.topic or "Bài Quiz Kiểm Tra",
                    "type": "Quiz",
                    "score_display": f"{score_v}/{total_q}",
                    "accuracy_pct": acc,
                    "duration_sec": q.duration_seconds or 0,
                    "date": q.created_at.strftime('%d/%m/%Y %H:%M') if q.created_at else ""
                })
        elif src == "submission":
            s = db.session.get(ExamSubmission, rec_id)
            if s and s.user_id == current_user.id:
                ex = s.exam
                total_q = ex.question_count if ex else 10
                score_v = int(s.total_score or 0)
                acc = int((score_v / total_q) * 100) if total_q > 0 else 0
                all_records.append({
                    "id": item,
                    "title": ex.title if ex else "Đề Thi Chuyên Biệt",
                    "type": ex.category if ex else "Exam",
                    "score_display": f"{score_v}/{total_q}",
                    "accuracy_pct": acc,
                    "duration_sec": (ex.duration_minutes * 60) if ex else 0,
                    "date": s.completed_at.strftime('%d/%m/%Y %H:%M') if s.completed_at else ""
                })

    if not all_records:
        flash("Vui lòng chọn ít nhất 2 bài thi để so sánh.", "warning")
        return redirect(url_for("exams.test_history"))

    return render_template("exams/test_compare.html", records=all_records)


@bp.route("/history/export")
@bp.route("/exams/history/export")
@login_required
def test_export_csv():
    quiz_attempts = QuizAttempt.query.filter_by(user_id=current_user.id).all()
    submissions = ExamSubmission.query.filter_by(user_id=current_user.id).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Loai Bai Thi", "Tieu De", "Diem So", "Ty Le Chinh Xac (%)", "Ngay Lam Bai"])

    for q in quiz_attempts:
        total_q = q.total_questions or 10
        score_val = q.score or 0
        acc = int((score_val / total_q) * 100) if total_q > 0 else 0
        date_str = q.created_at.strftime('%d/%m/%Y %H:%M') if q.created_at else ""
        writer.writerow([f"QUIZ-{q.id}", "Quiz", q.topic, f"{score_val}/{total_q}", f"{acc}%", date_str])

    for s in submissions:
        ex = s.exam
        total_q = ex.question_count if ex else 10
        score_val = int(s.total_score or 0)
        acc = int((score_val / total_q) * 100) if total_q > 0 else 0
        date_str = s.completed_at.strftime('%d/%m/%Y %H:%M') if s.completed_at else ""
        title_str = ex.title if ex else "Exam"
        cat_str = ex.category if ex else "Exam"
        writer.writerow([f"EXAM-{s.id}", cat_str, title_str, f"{score_val}/{total_q}", f"{acc}%", date_str])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=test_history_export.csv"}
    )


@bp.route("/history/<string:source>/<int:record_id>/delete", methods=["POST"])
@bp.route("/exams/history/<string:source>/<int:record_id>/delete", methods=["POST"])
@login_required
def test_delete_record(source, record_id):
    if source == "quiz":
        rec = db.session.get(QuizAttempt, record_id)
        if rec and rec.user_id == current_user.id:
            db.session.delete(rec)
            db.session.commit()
            flash("Đã xóa bản ghi bài quiz thành công.", "success")
    elif source == "submission":
        rec = db.session.get(ExamSubmission, record_id)
        if rec and rec.user_id == current_user.id:
            db.session.delete(rec)
            db.session.commit()
            flash("Đã xóa bản ghi lượt thi thành công.", "success")
    elif source == "toeic":
        rec = db.session.get(ToeicAttempt, record_id)
        if rec and rec.user_id == current_user.id:
            db.session.delete(rec)
            db.session.commit()
            flash("Đã xóa bản ghi bài thi TOEIC thành công.", "success")
    elif source == "grammar":
        rec = db.session.get(GrammarExerciseAttempt, record_id)
        if rec and rec.user_id == current_user.id:
            db.session.delete(rec)
            db.session.commit()
            flash("Đã xóa bản ghi bài tập ngữ pháp thành công.", "success")

    return redirect(url_for("exams.test_history"))
