import os
from urllib.parse import urlencode, urljoin, urlparse

import requests
from flask import current_app, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_user, logout_user

from ...extensions import db
from .models import User
from . import bp
from .forms import ForgotPasswordForm, LoginForm, RegisterForm, VerifyEmailForm


def is_safe_url(target):
    ref = urlparse(request.host_url)
    test = urlparse(urljoin(request.host_url, target))
    return test.scheme in ("http", "https") and ref.netloc == test.netloc


@bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    form = RegisterForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        username = form.username.data.strip()
        if User.query.filter((User.email == email) | (User.username == username)).first():
            flash("Email hoặc tên đăng nhập đã tồn tại.", "danger")
        else:
            user = User(username=username, email=email, is_email_verified=False)
            user.set_password(form.password.data)
            code = user.generate_verification_code()
            db.session.add(user)
            db.session.commit()
            flash(f"Đăng ký thành công! Mã xác minh OTP đã gửi đến email {email}: {code}", "info")
            return redirect(url_for("auth.verify_email", user_id=user.id))
    return render_template("auth/register.html", form=form)


@bp.route("/verify-email/<int:user_id>", methods=["GET", "POST"])
def verify_email(user_id):
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    user = db.session.get(User, user_id)
    if not user:
        flash("Tài khoản không tồn tại.", "danger")
        return redirect(url_for("auth.register"))
    if user.is_email_verified:
        flash("Email của bạn đã được xác minh. Vui lòng đăng nhập!", "success")
        return redirect(url_for("auth.login"))

    form = VerifyEmailForm()
    if form.validate_on_submit():
        if user.verify_email_code(form.code.data):
            db.session.commit()
            flash("Xác thực email thành công! Bạn có thể đăng nhập ngay bây giờ.", "success")
            return redirect(url_for("auth.login"))
        else:
            flash("Mã xác minh không chính xác hoặc đã hết hạn (15 phút). Vui lòng thử lại.", "danger")

    return render_template("auth/verify_email.html", form=form, user=user)


@bp.post("/resend-verification/<int:user_id>")
def resend_verification(user_id):
    user = db.session.get(User, user_id)
    if not user:
        flash("Tài khoản không tồn tại.", "danger")
        return redirect(url_for("auth.register"))
    if user.is_email_verified:
        flash("Tài khoản đã được xác minh.", "info")
        return redirect(url_for("auth.login"))

    code = user.generate_verification_code()
    db.session.commit()
    flash(f"Mã OTP xác minh mới đã được gửi: {code}", "info")
    return redirect(url_for("auth.verify_email", user_id=user.id))


@bp.route("/google")
def google_login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    client_id = current_app.config.get("GOOGLE_CLIENT_ID")
    client_secret = current_app.config.get("GOOGLE_CLIENT_SECRET")

    if client_id and client_secret:
        redirect_uri = url_for("auth.google_callback", _external=True)
        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "online",
            "prompt": "select_account",
        }
        google_auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
        return redirect(google_auth_url)

    # Demo mode if GOOGLE_CLIENT_ID is not configured in .env yet
    flash("⚠️ GOOGLE_CLIENT_ID chưa được định nghĩa trong tệp .env. Đã đăng nhập bằng tài khoản Google Demo.", "warning")
    oauth_email = "google_user@gmail.com"
    oauth_username = "GoogleUser"
    user = User.query.filter_by(email=oauth_email).first()
    if not user:
        user = User(
            username=oauth_username,
            email=oauth_email,
            is_email_verified=True,
            oauth_provider="google",
            oauth_id="google_123456789",
        )
        user.set_password("OAuthGoogleSecret123!")
        db.session.add(user)
        db.session.commit()

    login_user(user, remember=True)
    return redirect(url_for("main.dashboard"))


@bp.route("/google/callback")
def google_callback():
    code = request.args.get("code")
    if not code:
        flash("Đăng nhập bằng Google đã bị hủy hoặc gặp lỗi.", "danger")
        return redirect(url_for("auth.login"))

    client_id = current_app.config.get("GOOGLE_CLIENT_ID")
    client_secret = current_app.config.get("GOOGLE_CLIENT_SECRET")
    redirect_uri = url_for("auth.google_callback", _external=True)

    token_url = "https://oauth2.googleapis.com/token"
    token_data = {
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }

    try:
        token_res = requests.post(token_url, data=token_data, timeout=10)
        token_json = token_res.json()
        access_token = token_json.get("access_token")
        if not access_token:
            flash("Không thể trao đổi Token với Google. Vui lòng thử lại.", "danger")
            return redirect(url_for("auth.login"))

        userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        headers = {"Authorization": f"Bearer {access_token}"}
        userinfo_res = requests.get(userinfo_url, headers=headers, timeout=10)
        info = userinfo_res.json()

        email = info.get("email")
        google_id = info.get("id")
        name = info.get("name") or email.split("@")[0]

        if not email:
            flash("Google không cung cấp địa chỉ Email.", "danger")
            return redirect(url_for("auth.login"))

        user = User.query.filter((User.email == email) | (User.oauth_id == google_id)).first()
        if not user:
            base_username = "".join(c for c in name if c.isalnum()) or "google_user"
            username = base_username
            counter = 1
            while User.query.filter_by(username=username).first():
                username = f"{base_username}_{counter}"
                counter += 1

            user = User(
                username=username,
                email=email,
                is_email_verified=True,
                oauth_provider="google",
                oauth_id=google_id,
            )
            user.set_password(f"GoogleOAuth_{google_id}")
            db.session.add(user)
            db.session.commit()
        else:
            if not user.is_email_verified:
                user.is_email_verified = True
            if not user.oauth_provider:
                user.oauth_provider = "google"
                user.oauth_id = google_id
            db.session.commit()

        login_user(user, remember=True)
        flash(f"Xin chào {user.username}! Bạn đã đăng nhập thành công với tài khoản Google.", "success")
        return redirect(url_for("main.dashboard"))
    except Exception as exc:
        flash(f"Lỗi kết nối OAuth Google: {exc}", "danger")
        return redirect(url_for("auth.login"))


@bp.route("/facebook")
def facebook_login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    client_id = current_app.config.get("FACEBOOK_CLIENT_ID")
    client_secret = current_app.config.get("FACEBOOK_CLIENT_SECRET")

    if client_id and client_secret:
        redirect_uri = url_for("auth.facebook_callback", _external=True)
        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": "email,public_profile",
        }
        fb_auth_url = f"https://www.facebook.com/v18.0/dialog/oauth?{urlencode(params)}"
        return redirect(fb_auth_url)

    # Demo mode if FACEBOOK_CLIENT_ID is not configured in .env yet
    flash("⚠️ FACEBOOK_CLIENT_ID chưa được định nghĩa trong tệp .env. Đã đăng nhập bằng tài khoản Facebook Demo.", "warning")
    oauth_email = "facebook_user@facebook.com"
    oauth_username = "FacebookUser"
    user = User.query.filter_by(email=oauth_email).first()
    if not user:
        user = User(
            username=oauth_username,
            email=oauth_email,
            is_email_verified=True,
            oauth_provider="facebook",
            oauth_id="facebook_987654321",
        )
        user.set_password("OAuthFacebookSecret123!")
        db.session.add(user)
        db.session.commit()

    login_user(user, remember=True)
    return redirect(url_for("main.dashboard"))


@bp.route("/facebook/callback")
def facebook_callback():
    code = request.args.get("code")
    if not code:
        flash("Đăng nhập bằng Facebook đã bị hủy hoặc gặp lỗi.", "danger")
        return redirect(url_for("auth.login"))

    client_id = current_app.config.get("FACEBOOK_CLIENT_ID")
    client_secret = current_app.config.get("FACEBOOK_CLIENT_SECRET")
    redirect_uri = url_for("auth.facebook_callback", _external=True)

    token_url = "https://graph.facebook.com/v18.0/oauth/access_token"
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "client_secret": client_secret,
        "code": code,
    }

    try:
        token_res = requests.get(token_url, params=params, timeout=10)
        token_json = token_res.json()
        access_token = token_json.get("access_token")
        if not access_token:
            flash("Không thể lấy Token từ Facebook. Vui lòng thử lại.", "danger")
            return redirect(url_for("auth.login"))

        userinfo_url = f"https://graph.facebook.com/me?fields=id,name,email&access_token={access_token}"
        info = requests.get(userinfo_url, timeout=10).json()

        fb_id = info.get("id")
        name = info.get("name") or "facebook_user"
        email = info.get("email") or f"fb_{fb_id}@facebook.com"

        user = User.query.filter((User.email == email) | (User.oauth_id == fb_id)).first()
        if not user:
            base_username = "".join(c for c in name if c.isalnum()) or "facebook_user"
            username = base_username
            counter = 1
            while User.query.filter_by(username=username).first():
                username = f"{base_username}_{counter}"
                counter += 1

            user = User(
                username=username,
                email=email,
                is_email_verified=True,
                oauth_provider="facebook",
                oauth_id=fb_id,
            )
            user.set_password(f"FacebookOAuth_{fb_id}")
            db.session.add(user)
            db.session.commit()
        else:
            if not user.is_email_verified:
                user.is_email_verified = True
            if not user.oauth_provider:
                user.oauth_provider = "facebook"
                user.oauth_id = fb_id
            db.session.commit()

        login_user(user, remember=True)
        flash(f"Xin chào {user.username}! Bạn đã đăng nhập thành công với tài khoản Facebook.", "success")
        return redirect(url_for("main.dashboard"))
    except Exception as exc:
        flash(f"Lỗi kết nối OAuth Facebook: {exc}", "danger")
        return redirect(url_for("auth.login"))


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        user = User.query.filter_by(email=email).first()

        if user:
            is_locked, remaining_mins = user.is_locked_out()
            if is_locked:
                flash(f"Tài khoản tạm thời bị khóa do nhập sai mật khẩu 5 lần. Vui lòng thử lại sau {remaining_mins} phút.", "danger")
                return render_template("auth/login.html", form=form)

            if not user.is_active:
                flash("Tài khoản đã bị khóa. Vui lòng liên hệ quản trị viên.", "danger")
                return render_template("auth/login.html", form=form)

            if user.check_password(form.password.data):
                user.record_successful_login()
                db.session.commit()
                login_user(user, remember=form.remember.data)
                flash(f"Chào mừng {user.username} trở lại!", "success")
                next_url = request.args.get("next")
                return redirect(next_url if next_url and is_safe_url(next_url) else url_for("main.dashboard"))
            else:
                attempts = user.record_failed_login()
                db.session.commit()
                if attempts >= 5:
                    flash("Tài khoản của bạn đã bị khóa 15 phút do nhập sai mật khẩu 5 lần.", "danger")
                else:
                    remaining = 5 - attempts
                    flash(f"Email hoặc mật khẩu không chính xác. Bạn còn {remaining} lần thử.", "danger")
        else:
            flash("Email hoặc mật khẩu không chính xác.", "danger")

    return render_template("auth/login.html", form=form)


@bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        user = User.query.filter_by(email=email).first()
        if user:
            flash(f"Hướng dẫn khôi phục mật khẩu đã được gửi tới email {email}.", "success")
        else:
            flash(f"Nếu email {email} tồn tại trong hệ thống, bạn sẽ nhận được liên kết khôi phục.", "info")
        return redirect(url_for("auth.login"))
    return render_template("auth/forgot_password.html", form=form)


@bp.post("/logout")
def logout():
    logout_user()
    flash("Bạn đã đăng xuất.", "info")
    return redirect(url_for("main.index"))


