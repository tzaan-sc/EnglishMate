from urllib.parse import urljoin, urlparse

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user

from ...extensions import db
from .models import User
from . import bp
from .forms import LoginForm, RegisterForm


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
            user = User(username=username, email=email)
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            flash("Tạo tài khoản thành công. Hãy đăng nhập!", "success")
            return redirect(url_for("auth.login"))
    return render_template("auth/register.html", form=form)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.strip().lower()).first()
        if user and user.check_password(form.password.data):
            if not user.is_active:
                flash("Tài khoản đã bị khóa. Vui lòng liên hệ quản trị viên.", "danger")
            else:
                login_user(user, remember=form.remember.data)
                flash(f"Chào mừng {user.username} trở lại!", "success")
                next_url = request.args.get("next")
                return redirect(next_url if next_url and is_safe_url(next_url) else url_for("main.dashboard"))
        else:
            flash("Email hoặc mật khẩu không chính xác.", "danger")
    return render_template("auth/login.html", form=form)


@bp.post("/logout")
def logout():
    logout_user()
    flash("Bạn đã đăng xuất.", "info")
    return redirect(url_for("main.index"))

