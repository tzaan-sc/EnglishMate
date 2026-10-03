"""
Routes for IELTS Speaking Room Simulator (Feature 8.1).
3-Part Standard Simulation:
- Part 1: Introduction & Interview
- Part 2: Cue Card (1 min prep, 2 min speak)
- Part 3: Two-way Discussion
"""

from datetime import datetime
from flask import abort, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import func

from app.extensions import db
from app.backend.auth.models import record_daily_activity
from app.backend.exams.models import (
    IeltsSpeakingTest,
    IeltsSpeakingTopic,
    IeltsSpeakingSubmission,
    IeltsSpeakingAnswer
)
from app.backend.exams.speaking_evaluator import evaluate_speaking_submission_ai
from app.seeds.ielts_speaking_seeds import seed_ielts_speaking_tests
from . import bp
from .forms import ActionForm


@bp.route("/exams/speaking", methods=["GET"])
@bp.route("/ielts-speaking", methods=["GET"])
@bp.route("/speaking-simulator", methods=["GET"])
@login_required
def speaking_test_list():
    """
    IELTS Speaking Test Catalog & Overview Hub.
    """
    seed_ielts_speaking_tests()

    difficulty = request.args.get("difficulty", "").strip()
    target_band = request.args.get("target_band", "").strip()
    search = request.args.get("q", "").strip()

    query = IeltsSpeakingTest.query.filter_by(is_active=True, is_published=True)

    if difficulty and difficulty.lower() != "all":
        query = query.filter_by(difficulty=difficulty)
    if search:
        query = query.filter(
            (IeltsSpeakingTest.title.ilike(f"%{search}%")) |
            (IeltsSpeakingTest.description.ilike(f"%{search}%"))
        )

    tests = query.order_by(IeltsSpeakingTest.id.asc()).all()

    # User submission metrics
    user_submissions = IeltsSpeakingSubmission.query.filter_by(
        user_id=current_user.id
    ).order_by(IeltsSpeakingSubmission.created_at.desc()).all()

    best_bands = {}
    completed_submissions = []
    for sub in user_submissions:
        if sub.status == "COMPLETED":
            completed_submissions.append(sub)
            if sub.test_id not in best_bands or sub.overall_band > best_bands[sub.test_id]:
                best_bands[sub.test_id] = sub.overall_band

    # Check for in-progress test
    in_progress = next((s for s in user_submissions if s.status == "IN_PROGRESS"), None)

    return render_template(
        "exams/speaking_list.html",
        tests=tests,
        best_bands=best_bands,
        recent_submissions=completed_submissions[:5],
        in_progress=in_progress,
        difficulty=difficulty,
        target_band=target_band,
        search=search,
        form=ActionForm()
    )


@bp.post("/exams/speaking/<int:test_id>/start")
@login_required
def speaking_test_start(test_id):
    """
    Starts an IELTS Speaking Simulation session.
    """
    test = db.session.get(IeltsSpeakingTest, test_id)
    if not test or not test.is_active:
        flash("Không tìm thấy đề thi IELTS Speaking này.", "danger")
        return redirect(url_for("exams.speaking_test_list"))

    # Reuse or create submission
    existing_in_prog = IeltsSpeakingSubmission.query.filter_by(
        user_id=current_user.id,
        test_id=test.id,
        status="IN_PROGRESS"
    ).first()

    if existing_in_prog:
        return redirect(url_for("exams.speaking_simulation_room", submission_id=existing_in_prog.id))

    submission = IeltsSpeakingSubmission(
        user_id=current_user.id,
        test_id=test.id,
        status="IN_PROGRESS",
        overall_band=0.0
    )
    db.session.add(submission)
    db.session.commit()

    return redirect(url_for("exams.speaking_simulation_room", submission_id=submission.id))


@bp.get("/exams/speaking/room/<int:submission_id>")
@login_required
def speaking_simulation_room(submission_id):
    """
    Interactive 3-Part IELTS Speaking Simulator Room.
    """
    submission = db.session.get(IeltsSpeakingSubmission, submission_id)
    if not submission or submission.user_id != current_user.id:
        flash("Không tìm thấy phòng thi Speaking của bạn.", "danger")
        return redirect(url_for("exams.speaking_test_list"))

    if submission.status == "COMPLETED":
        return redirect(url_for("exams.speaking_test_result", submission_id=submission.id))

    test = db.session.get(IeltsSpeakingTest, submission.test_id)
    topics = IeltsSpeakingTopic.query.filter_by(test_id=test.id).order_by(IeltsSpeakingTopic.part, IeltsSpeakingTopic.order).all()

    topics_data = [
        {
            "id": t.id,
            "part": t.part,
            "topic_title": t.topic_title,
            "cue_card_prompt": t.cue_card_prompt,
            "questions": t.questions or [],
            "prep_time_seconds": t.prep_time_seconds,
            "response_time_seconds": t.response_time_seconds,
            "order": t.order
        }
        for t in topics
    ]

    # Existing saved answers for resume
    answers = IeltsSpeakingAnswer.query.filter_by(submission_id=submission.id).all()
    saved_answers_map = {
        f"{a.part}_{a.question_index}": {
            "transcript": a.candidate_transcript,
            "notes": a.candidate_notes,
            "has_audio": bool(a.audio_data_url)
        }
        for a in answers
    }

    form = ActionForm()

    return render_template(
        "exams/speaking_room.html",
        submission=submission,
        test=test,
        topics=topics,
        topics_data=topics_data,
        saved_answers_map=saved_answers_map,
        form=form
    )


@bp.post("/exams/speaking/room/<int:submission_id>/save-answer")
@login_required
def speaking_save_answer(submission_id):
    """
    Saves an answer for an individual question/part asynchronously via AJAX.
    """
    submission = db.session.get(IeltsSpeakingSubmission, submission_id)
    if not submission or submission.user_id != current_user.id:
        return jsonify({"status": "error", "message": "Unauthorized"}), 403

    data = request.get_json() if request.is_json else request.form
    part = int(data.get("part", 1))
    topic_id = data.get("topic_id")
    question_index = int(data.get("question_index", 0))
    question_text = (data.get("question_text") or "").strip()
    candidate_transcript = (data.get("candidate_transcript") or "").strip()
    candidate_notes = (data.get("candidate_notes") or "").strip()
    audio_data_url = (data.get("audio_data_url") or "").strip()

    ans = IeltsSpeakingAnswer.query.filter_by(
        submission_id=submission.id,
        part=part,
        question_index=question_index
    ).first()

    if not ans:
        ans = IeltsSpeakingAnswer(
            submission_id=submission.id,
            topic_id=topic_id,
            part=part,
            question_index=question_index
        )
        db.session.add(ans)

    ans.question_text = question_text
    ans.candidate_transcript = candidate_transcript
    ans.candidate_notes = candidate_notes
    if audio_data_url:
        ans.audio_data_url = audio_data_url

    db.session.commit()

    return jsonify({
        "status": "success",
        "message": "Answer saved successfully",
        "answer_id": ans.id
    })


@bp.post("/exams/speaking/room/<int:submission_id>/submit")
@login_required
def speaking_simulation_submit(submission_id):
    """
    Submits the IELTS Speaking test, triggers AI rubric evaluation, updates XP, and redirects to result.
    """
    submission = db.session.get(IeltsSpeakingSubmission, submission_id)
    if not submission or submission.user_id != current_user.id:
        flash("Không tìm thấy bài thi speaking.", "danger")
        return redirect(url_for("exams.speaking_test_list"))

    if submission.status == "COMPLETED":
        return redirect(url_for("exams.speaking_test_result", submission_id=submission.id))

    time_spent = int(request.form.get("time_spent") or 0)
    submission.time_spent = time_spent

    # Retrieve all answers
    answers = IeltsSpeakingAnswer.query.filter_by(submission_id=submission.id).all()

    answers_payload = [
        {
            "part": a.part,
            "question_index": a.question_index,
            "candidate_transcript": a.candidate_transcript,
            "candidate_notes": a.candidate_notes,
            "audio_data_url": a.audio_data_url
        }
        for a in answers
    ]

    # Evaluate using IELTS rubric AI scoring
    eval_result = evaluate_speaking_submission_ai(answers_payload)

    submission.overall_band = eval_result["overall_band"]
    submission.fluency_score = eval_result["fluency_score"]
    submission.lexical_score = eval_result["lexical_score"]
    submission.grammar_score = eval_result["grammar_score"]
    submission.pronunciation_score = eval_result["pronunciation_score"]
    submission.examiner_feedback = eval_result["examiner_feedback"]
    submission.detailed_analysis = eval_result["detailed_analysis"]
    submission.status = "COMPLETED"
    submission.completed_at = datetime.utcnow()

    # Gamification & Daily Activity
    xp_earned = 75 if submission.overall_band >= 7.0 else (60 if submission.overall_band >= 6.0 else 50)
    current_user.add_xp(xp_earned, reason=f"Hoàn thành phòng thi IELTS Speaking (Band {submission.overall_band})")
    record_daily_activity(current_user)

    try:
        from app.backend.learning.routes import update_challenge_progress, check_user_badges
        update_challenge_progress(current_user, "speaking", 1)
        update_challenge_progress(current_user, "exam", 1)
        check_user_badges(current_user)
    except Exception:
        pass

    db.session.commit()

    flash(f"🎉 Chúc mừng bạn đã hoàn thành bài thi IELTS Speaking! Điểm ước tính: Band {submission.overall_band}", "success")
    return redirect(url_for("exams.speaking_test_result", submission_id=submission.id))


@bp.get("/exams/speaking/result/<int:submission_id>")
@login_required
def speaking_test_result(submission_id):
    """
    Displays the IELTS Speaking Scorecard and detailed 4-criteria AI analysis.
    """
    submission = db.session.get(IeltsSpeakingSubmission, submission_id)
    if not submission or submission.user_id != current_user.id:
        flash("Không tìm thấy kết quả bài thi Speaking.", "danger")
        return redirect(url_for("exams.speaking_test_list"))

    test = db.session.get(IeltsSpeakingTest, submission.test_id)
    topics = IeltsSpeakingTopic.query.filter_by(test_id=test.id).order_by(IeltsSpeakingTopic.part, IeltsSpeakingTopic.order).all()
    answers = IeltsSpeakingAnswer.query.filter_by(submission_id=submission.id).order_by(IeltsSpeakingAnswer.part, IeltsSpeakingAnswer.question_index).all()

    answers_map = {f"{a.part}_{a.question_index}": a for a in answers}

    return render_template(
        "exams/speaking_result.html",
        submission=submission,
        test=test,
        topics=topics,
        answers=answers,
        answers_map=answers_map,
        form=ActionForm()
    )


@bp.post("/exams/speaking/submission/<int:submission_id>/delete")
@login_required
def speaking_submission_delete(submission_id):
    """
    Deletes an IELTS Speaking test attempt.
    """
    submission = db.session.get(IeltsSpeakingSubmission, submission_id)
    if submission and submission.user_id == current_user.id:
        db.session.delete(submission)
        db.session.commit()
        flash("Đã xóa bản ghi bài thi Speaking thành công.", "success")
    else:
        flash("Không tìm thấy bản ghi bài thi.", "danger")

    return redirect(url_for("exams.speaking_test_list"))
