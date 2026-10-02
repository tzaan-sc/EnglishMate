import uuid
import random
from datetime import date, datetime, timedelta, timezone

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import func

from ...extensions import db
from ..auth.models import record_daily_activity
from .models import (
    Badge, Challenge, FlashcardProgress, FlashcardSet, LessonProgress,
    QuizAttempt, UserBadge, UserChallenge, VocabularyProgress
)
from . import bp

# ==============================================================================

def check_user_badges(user):
    """Checks user statistics and awards any unearned badges."""
    
    existing_badge_ids = {ub.badge_id for ub in UserBadge.query.filter_by(user_id=user.id).all()}
    all_badges = Badge.query.all()
    
    lessons_cnt = LessonProgress.query.filter_by(user_id=user.id).count()
    vocab_cnt = VocabularyProgress.query.filter_by(user_id=user.id).filter(VocabularyProgress.learned_count > 0).count()
    quiz_cnt = QuizAttempt.query.filter_by(user_id=user.id).count()
    perfect_cnt = QuizAttempt.query.filter_by(user_id=user.id).filter(QuizAttempt.score == QuizAttempt.total_questions, QuizAttempt.total_questions > 0).count()
    streak_days = max(user.current_streak or 0, user.longest_streak or 0)
    flashcard_cnt = FlashcardSet.query.filter_by(user_id=user.id).count() + FlashcardProgress.query.filter_by(user_id=user.id).count()
    user_level = user.get_level()
    
    newly_unlocked = []
    for badge in all_badges:
        if badge.id in existing_badge_ids:
            continue
            
        unlocked = False
        if badge.req_type == "lessons_count" and lessons_cnt >= badge.req_value:
            unlocked = True
        elif badge.req_type == "vocab_count" and vocab_cnt >= badge.req_value:
            unlocked = True
        elif badge.req_type == "quiz_count" and quiz_cnt >= badge.req_value:
            unlocked = True
        elif badge.req_type == "perfect_score" and perfect_cnt >= badge.req_value:
            unlocked = True
        elif badge.req_type == "streak_days" and streak_days >= badge.req_value:
            unlocked = True
        elif badge.req_type == "flashcard_count" and flashcard_cnt >= badge.req_value:
            unlocked = True
        elif badge.req_type == "level_reach" and user_level >= badge.req_value:
            unlocked = True
            
        if unlocked:
            ub = UserBadge(user_id=user.id, badge_id=badge.id, unlocked_at=datetime.utcnow())
            db.session.add(ub)
            user.add_xp(badge.xp_reward)
            newly_unlocked.append(badge)
            
    if newly_unlocked:
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
    return newly_unlocked


def get_or_create_user_challenges(user):
    """Initializes and returns user's daily and weekly challenges."""
    from .models import Challenge, UserChallenge
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())
    
    all_challenges = Challenge.query.all()
    user_challenges = []
    
    for ch in all_challenges:
        p_date = today if ch.period == "DAILY" else start_of_week
        uc = UserChallenge.query.filter_by(user_id=user.id, challenge_id=ch.id, period_date=p_date).first()
        if not uc:
            uc = UserChallenge(
                user_id=user.id,
                challenge_id=ch.id,
                current_progress=0,
                is_completed=False,
                is_claimed=False,
                period_date=p_date
            )
            db.session.add(uc)
            db.session.flush()
        user_challenges.append(uc)
        
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
    return user_challenges


def update_challenge_progress(user, action_type, count=1):
    """Updates challenge progress for matching action_type."""
    from .models import Challenge, UserChallenge
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())
    
    get_or_create_user_challenges(user)
    
    user_challenges = UserChallenge.query.join(Challenge).filter(
        UserChallenge.user_id == user.id,
        Challenge.action_type == action_type,
        UserChallenge.is_completed == False,
        ((Challenge.period == "DAILY") & (UserChallenge.period_date == today)) |
        ((Challenge.period == "WEEKLY") & (UserChallenge.period_date == start_of_week))
    ).all()
    
    for uc in user_challenges:
        uc.current_progress = min(uc.challenge.target, uc.current_progress + count)
        if uc.current_progress >= uc.challenge.target:
            uc.is_completed = True
            uc.completed_at = datetime.utcnow()
            
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()


@bp.get("/gamification")
@bp.get("/leaderboard")
@login_required
def gamification_hub():
    from .models import Badge, UserBadge, Challenge, UserChallenge
    from ..auth.models import User, DailyActivity
    
    check_user_badges(current_user)
    user_challenges = get_or_create_user_challenges(current_user)
    
    level_info = current_user.get_level_info()
    
    # Badges
    all_badges = Badge.query.all()
    user_badge_map = {ub.badge_id: ub for ub in UserBadge.query.filter_by(user_id=current_user.id).all()}
    
    badges_data = []
    for b in all_badges:
        is_unlocked = b.id in user_badge_map
        unlocked_at = user_badge_map[b.id].unlocked_at if is_unlocked else None
        badges_data.append({
            "badge": b,
            "is_unlocked": is_unlocked,
            "unlocked_at": unlocked_at
        })
        
    # Leaderboards (Chỉ dành cho Học viên, loại trừ Quản trị viên Admin)
    student_filter = (User.role != "ADMIN")
    all_time_leaders = User.query.filter(student_filter).order_by(User.xp.desc()).limit(20).all()
    streak_leaders = User.query.filter(student_filter).order_by(User.current_streak.desc()).limit(20).all()
    
    # Weekly XP Leaders
    start_of_week = date.today() - timedelta(days=date.today().weekday())
    weekly_acts = db.session.query(
        DailyActivity.user_id,
        func.sum(DailyActivity.completed_lessons * 20).label("weekly_xp")
    ).join(User, User.id == DailyActivity.user_id).filter(
        DailyActivity.activity_date >= start_of_week,
        User.role != "ADMIN"
    ).group_by(DailyActivity.user_id).all()
    
    weekly_xp_map = {row.user_id: (row.weekly_xp or 0) for row in weekly_acts}
    all_students = User.query.filter(student_filter).all()
    weekly_leaders = sorted(all_students, key=lambda u: weekly_xp_map.get(u.id, 0) + min(50, (u.xp or 0)), reverse=True)[:20]
    
    # Daily goal calculation
    today = date.today()
    today_act = DailyActivity.query.filter_by(user_id=current_user.id, activity_date=today).first()
    daily_goal_target = current_user.daily_goal_xp or 50
    daily_progress_xp = min(daily_goal_target, (today_act.completed_lessons * 20) if today_act else 0)
    is_daily_goal_done = daily_progress_xp >= daily_goal_target or (today_act and today_act.goal_completed)
    is_daily_claimed = current_user.daily_reward_claimed_date == today
    
    daily_challenges = [uc for uc in user_challenges if uc.challenge.period == "DAILY"]
    weekly_challenges = [uc for uc in user_challenges if uc.challenge.period == "WEEKLY"]
    
    active_tab = request.args.get("tab", "leaderboard")
    
    return render_template(
        "learning/gamification.html",
        level_info=level_info,
        badges_data=badges_data,
        unlocked_count=len(user_badge_map),
        total_badges_count=len(all_badges),
        all_time_leaders=all_time_leaders,
        streak_leaders=streak_leaders,
        weekly_leaders=weekly_leaders,
        daily_challenges=daily_challenges,
        weekly_challenges=weekly_challenges,
        daily_progress_xp=daily_progress_xp,
        daily_goal_target=daily_goal_target,
        is_daily_goal_done=is_daily_goal_done,
        is_daily_claimed=is_daily_claimed,
        active_tab=active_tab
    )


@bp.post("/gamification/claim-challenge/<int:uc_id>")
@login_required
def claim_challenge_reward(uc_id):
    from .models import UserChallenge
    uc = UserChallenge.query.filter_by(id=uc_id, user_id=current_user.id).first_or_404()
    if not uc.is_completed:
        flash("Thử thách này chưa hoàn thành!", "warning")
        return redirect(url_for("learning.gamification_hub", tab="challenges"))
        
    if uc.is_claimed:
        flash("Bạn đã nhận thưởng cho thử thách này rồi!", "info")
        return redirect(url_for("learning.gamification_hub", tab="challenges"))
        
    uc.is_claimed = True
    reward_xp = uc.challenge.xp_reward
    current_user.add_xp(reward_xp, reason=f"Thưởng thử thách: {uc.challenge.title}")
    db.session.commit()
    
    flash(f"Chúc mừng! Bạn đã nhận được +{reward_xp} XP từ thử thách \"{uc.challenge.title}\"!", "success")
    return redirect(url_for("learning.gamification_hub", tab="challenges"))


@bp.post("/gamification/claim-daily-goal")
@login_required
def claim_daily_goal_reward():
    today = date.today()
    if current_user.daily_reward_claimed_date == today:
        flash("Bạn đã nhận phần thưởng mục tiêu ngày hôm nay rồi!", "info")
        return redirect(url_for("learning.gamification_hub", tab="challenges"))
        
    current_user.daily_reward_claimed_date = today
    reward_xp = 50
    current_user.add_xp(reward_xp, reason="Thưởng hoàn thành mục tiêu ngày")
    db.session.commit()
    
    flash(f"Tuyệt vời! Bạn đã nhận được rương thưởng ngày +{reward_xp} XP!", "success")
    return redirect(url_for("learning.gamification_hub", tab="challenges"))

