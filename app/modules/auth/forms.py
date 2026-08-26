from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length


class RegisterForm(FlaskForm):
    username = StringField("Tên đăng nhập", validators=[DataRequired(), Length(min=3, max=40)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField("Mật khẩu", validators=[DataRequired(), Length(min=6, max=128)])
    confirm_password = PasswordField("Nhập lại mật khẩu", validators=[DataRequired(), EqualTo("password")])
    submit = SubmitField("Tạo tài khoản")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Mật khẩu", validators=[DataRequired()])
    remember = BooleanField("Ghi nhớ đăng nhập")
    submit = SubmitField("Đăng nhập")

