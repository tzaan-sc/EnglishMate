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
        part_stats=part_stats
    )
