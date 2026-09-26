import logging
from datetime import date, datetime, timedelta, timezone
from flask import current_app, render_template_string, url_for

from app.backend.auth.models import DailyActivity, User
from app.extensions import db
from app.utils.email import send_email

logger = logging.getLogger(__name__)


def get_vietnam_time():
    """Returns current datetime in UTC+7 (Vietnam Time)."""
    return datetime.now(timezone.utc) + timedelta(hours=7)


def get_user_daily_goal_status(user, target_date=None):
    """
    Computes real-time daily goal completion status, progress XP and remaining XP for given user.
    """
    if not user or getattr(user, "is_admin", False):
        return None

    today = target_date or get_vietnam_time().date()
    activity = DailyActivity.query.filter_by(user_id=user.id, activity_date=today).first()
    target_xp = getattr(user, "daily_goal_xp", 50) or 50
    completed_lessons = activity.completed_lessons if activity else 0
    progress_xp = min(target_xp, completed_lessons * 20)
    is_completed = bool((activity and activity.goal_completed) or (progress_xp >= target_xp))
    remaining_xp = max(0, target_xp - progress_xp)
    is_claimed = bool(getattr(user, "daily_reward_claimed_date", None) == today)
    streak = user.get_current_streak() if hasattr(user, "get_current_streak") else getattr(user, "current_streak", 0) or 0

    return {
        "user_id": user.id,
        "username": user.username,
        "target_xp": target_xp,
        "progress_xp": progress_xp,
        "remaining_xp": remaining_xp,
        "completed_lessons": completed_lessons,
        "is_completed": is_completed,
        "is_claimed": is_claimed,
        "streak": streak,
        "longest_streak": getattr(user, "longest_streak", 0) or 0,
        "reminder_enabled": getattr(user, "daily_goal_reminder_enabled", True),
        "reminder_time": getattr(user, "daily_goal_reminder_time", "20:00") or "20:00",
        "reminder_email": getattr(user, "daily_goal_reminder_email", True),
        "reminder_popup": getattr(user, "daily_goal_reminder_popup", True),
        "last_reminder_date": getattr(user, "last_daily_goal_reminder_date", None),
    }


def check_user_goal_reminder_alert(user, target_date=None, force_hour=None):
    """
    Checks if a popup / notification should be presented to user right now.
    Triggers when:
    1. User is not admin and is active
    2. Goal reminder is enabled
    3. Today's daily goal is not completed
    4. Current time is >= reminder_time or within evening window before midnight
    """
    status = get_user_daily_goal_status(user, target_date=target_date)
    if not status:
        return {"should_remind": False, "reason": "admin_or_no_user"}

    if not status["reminder_enabled"]:
        return {"should_remind": False, "reason": "reminder_disabled", "status": status}

    if status["is_completed"]:
        return {"should_remind": False, "reason": "already_completed", "status": status}

    vn_now = get_vietnam_time()
    current_hour = force_hour if force_hour is not None else vn_now.hour

    # Parse user reminder hour (e.g. "20:00" -> 20)
    reminder_str = status.get("reminder_time", "20:00") or "20:00"
    try:
        reminder_hour = int(reminder_str.split(":")[0])
    except (ValueError, IndexError):
        reminder_hour = 20

    is_evening_near_deadline = current_hour >= reminder_hour or current_hour >= 20

    remaining_xp = status["remaining_xp"]
    streak = status["streak"]

    title = "⏰ Sắp hết ngày! Nhắc nhở Mục tiêu học tập"
    message = (
        f"Bạn còn thiếu {remaining_xp} XP để hoàn thành mục tiêu ngày hôm nay. "
        f"Đừng để chuỗi {streak} ngày streak bị gián đoạn, hãy học một bài ngắn ngay nhé!"
    )

    try:
        learn_url = url_for("learning.lessons")
        review_url = url_for("learning.review_vocabulary")
        reward_url = url_for("learning.gamification_hub", tab="challenges")
    except RuntimeError:
        learn_url = "/lessons"
        review_url = "/vocabulary/review"
        reward_url = "/gamification?tab=challenges"

    return {
        "should_remind": True,
        "should_popup": bool(is_evening_near_deadline and status["reminder_popup"]),
        "is_evening_near_deadline": is_evening_near_deadline,
        "title": title,
        "message": message,
        "status": status,
        "learn_url": learn_url,
        "review_url": review_url,
        "reward_url": reward_url,
    }


EMAIL_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Nhắc nhở Mục tiêu học tập - EnglishMate</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #1e293b;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color: #f8fafc; padding: 32px 16px;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width: 580px; background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06); border: 1px solid #e2e8f0;">
          
          <!-- HEADER -->
          <tr>
            <td style="background: linear-gradient(135deg, #ea580c 0%, #f97316 50%, #f59e0b 100%); padding: 32px 28px; text-align: center;">
              <div style="font-size: 42px; margin-bottom: 8px;">⏰🔥</div>
              <h1 style="color: #ffffff; font-size: 24px; font-weight: 800; margin: 0 0 6px; letter-spacing: -0.02em;">
                Sắp hết ngày rồi! Đừng quên Mục Tiêu Ngày
              </h1>
              <p style="color: rgba(255, 255, 255, 0.9); font-size: 14px; margin: 0;">
                EnglishMate · Giữ vững chuỗi streak & nhận rương quà +50 XP
              </p>
            </td>
          </tr>

          <!-- BODY CONTENT -->
          <tr>
            <td style="padding: 28px 28px 20px;">
              <p style="font-size: 15px; line-height: 1.6; margin: 0 0 16px; color: #334155;">
                Xin chào <strong>{{ user_name }}</strong>,
              </p>
              <p style="font-size: 15px; line-height: 1.6; margin: 0 0 20px; color: #334155;">
                Đồng hồ đang điểm dần về mốc 24:00 đêm! Hệ thống nhận thấy bạn chỉ còn một chút nữa là hoàn thành chỉ tiêu học tập hôm nay. Đừng để lỡ nhé:
              </p>

              <!-- PROGRESS CARD -->
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color: #fff7ed; border: 1.5px solid #fdba74; border-radius: 12px; margin-bottom: 24px;">
                <tr>
                  <td style="padding: 18px 20px;">
                    <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
                      <tr>
                        <td style="font-size: 13px; font-weight: 700; color: #c2410c; text-transform: uppercase; letter-spacing: 0.05em; padding-bottom: 8px;">
                          Tiến độ Mục tiêu ngày hôm nay
                        </td>
                        <td align="right" style="font-size: 14px; font-weight: 800; color: #ea580c; padding-bottom: 8px;">
                          {{ progress_xp }} / {{ target_xp }} XP
                        </td>
                      </tr>
                      <tr>
                        <td colspan="2" style="padding-bottom: 12px;">
                          <div style="background-color: #fed7aa; height: 10px; border-radius: 999px; overflow: hidden;">
                            <div style="background-color: #ea580c; width: {{ progress_pct }}%; height: 10px; border-radius: 999px;"></div>
                          </div>
                        </td>
                      </tr>
                      <tr>
                        <td colspan="2" style="font-size: 13px; color: #7c2d12; line-height: 1.5;">
                          ⚡ Bạn chỉ còn thiếu <strong>{{ remaining_xp }} XP</strong> nữa (tương đương 1 bài học ngắn hoặc ôn tập từ vựng).
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
              </table>

              <!-- HIGHLIGHT PERKS -->
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin-bottom: 24px;">
                <tr>
                  <td width="36" valign="top" style="font-size: 20px; padding-right: 12px;">🔥</td>
                  <td style="font-size: 14px; line-height: 1.5; color: #475569; padding-bottom: 12px;">
                    <strong>Bảo toàn chuỗi học tập:</strong> Bạn đang có chuỗi <strong>{{ streak }} ngày liên tiếp</strong>. Hoàn thành bài học để giữ vững ngọn lửa streak sáng rực!
                  </td>
                </tr>
                <tr>
                  <td width="36" valign="top" style="font-size: 20px; padding-right: 12px;">🎁</td>
                  <td style="font-size: 14px; line-height: 1.5; color: #475569;">
                    <strong>Mở rương thưởng Daily Goal Chest:</strong> Nhận ngay phần thưởng độc quyền <strong>+50 XP</strong> sau khi đạt chỉ tiêu!
                  </td>
                </tr>
              </table>

              <!-- CTA BUTTON -->
              <div style="text-align: center; margin: 28px 0 20px;">
                <a href="{{ cta_url }}" target="_blank" style="display: inline-block; background: linear-gradient(135deg, #f97316 0%, #ea580c 100%); color: #ffffff; text-decoration: none; padding: 14px 32px; border-radius: 999px; font-weight: 700; font-size: 15px; box-shadow: 0 4px 14px rgba(234, 88, 12, 0.35);">
                  🚀 Bắt đầu học ngay để giữ Streak
                </a>
              </div>

              <p style="font-size: 12px; color: #94a3b8; text-align: center; margin: 0;">
                Mẹo nhỏ: Chỉ mất 3 - 5 phút để hoàn thành một bài đọc hoặc ôn tập 10 từ vựng SRS!
              </p>
            </td>
          </tr>

          <!-- FOOTER -->
          <tr>
            <td style="background-color: #f1f5f9; padding: 18px 24px; text-align: center; border-top: 1px solid #e2e8f0; font-size: 12px; color: #64748b;">
              <p style="margin: 0 0 4px;">EnglishMate · Nền tảng luyện thi & học tiếng Anh toàn diện</p>
              <p style="margin: 0;">Bạn nhận được email này vì đã bật tính năng Nhắc nhở Mục tiêu hàng ngày trong tài khoản.</p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""


def send_daily_goal_reminders(force=False, target_user_id=None):
    """
    Finds all active student users who haven't completed their daily goal today,
    and sends them an automated email reminder.

    :param force: If True, sends even if user was already sent a reminder today.
    :param target_user_id: If specified, only checks and sends for this specific user.
    :return: dict with summary stats
    """
    today = get_vietnam_time().date()

    query = User.query.filter(
        User.role != "ADMIN",
        User.is_active.is_(True),
        User.email.isnot(None),
    )

    if target_user_id:
        query = query.filter(User.id == target_user_id)
    else:
        query = query.filter(User.daily_goal_reminder_enabled.is_(True))
        query = query.filter(User.daily_goal_reminder_email.is_(True))

    users = query.all()

    total_checked = len(users)
    sent_count = 0
    already_done_count = 0
    skipped_count = 0

    try:
        base_cta_url = url_for("learning.lessons", _external=True)
    except Exception:
        base_cta_url = "http://localhost:5000/lessons"

    for user in users:
        # Check if already sent today
        if not force and getattr(user, "last_daily_goal_reminder_date", None) == today:
            skipped_count += 1
            continue

        goal_status = get_user_daily_goal_status(user, target_date=today)
        if not goal_status:
            continue

        if goal_status["is_completed"]:
            already_done_count += 1
            continue

        target_xp = goal_status["target_xp"]
        progress_xp = goal_status["progress_xp"]
        remaining_xp = goal_status["remaining_xp"]
        progress_pct = min(100, int((progress_xp / target_xp * 100))) if target_xp > 0 else 0
        streak = goal_status["streak"]

        html_body = render_template_string(
            EMAIL_HTML_TEMPLATE,
            user_name=user.full_name or user.username,
            progress_xp=progress_xp,
            target_xp=target_xp,
            remaining_xp=remaining_xp,
            progress_pct=progress_pct,
            streak=streak,
            cta_url=base_cta_url,
        )

        subject = "⏰ [EnglishMate] Sắp hết ngày! Đừng quên hoàn thành Mục tiêu ngày & giữ vững chuỗi Streak 🔥"
        send_email(user.email, subject, html_body)

        user.last_daily_goal_reminder_date = today
        sent_count += 1

    try:
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        logger.error(f"Error committing daily goal reminders update: {exc}")

    return {
        "success": True,
        "total_checked": total_checked,
        "sent_count": sent_count,
        "already_done_count": already_done_count,
        "skipped_count": skipped_count,
        "date": str(today),
    }
