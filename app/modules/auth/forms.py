from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length


class RegisterForm(FlaskForm):
    username = StringField("Tên đăng nhập", validators=[DataRequired(message="Vui lòng nhập tên đăng nhập."), Length(min=3, max=40)])
    email = StringField("Email", validators=[DataRequired(message="Vui lòng nhập email."), Email(message="Email không hợp lệ."), Length(max=120)])
    password = PasswordField("Mật khẩu", validators=[DataRequired(message="Vui lòng nhập mật khẩu."), Length(min=6, max=128)])
    confirm_password = PasswordField("Nhập lại mật khẩu", validators=[DataRequired(message="Vui lòng xác nhận mật khẩu."), EqualTo("password", message="Mật khẩu nhập lại không khớp.")])
    terms_agree = BooleanField("Tôi đồng ý với Điều khoản sử dụng", validators=[DataRequired(message="Bạn phải đồng ý với Điều khoản sử dụng.")])
    privacy_agree = BooleanField("Tôi đồng ý với Chính sách bảo mật", validators=[DataRequired(message="Bạn phải đồng ý với Chính sách bảo mật.")])
    submit = SubmitField("Tạo tài khoản")


class VerifyEmailForm(FlaskForm):
    code = StringField("Mã xác minh (OTP)", validators=[DataRequired(message="Vui lòng nhập mã xác minh 6 chữ số."), Length(min=6, max=6, message="Mã OTP phải gồm 6 chữ số.")])
    submit = SubmitField("Xác nhận email")


class ForgotPasswordForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(message="Vui lòng nhập email."), Email(message="Email không hợp lệ.")])
    submit = SubmitField("Gửi đường dẫn khôi phục")


class ResetPasswordForm(FlaskForm):
    password = PasswordField("Mật khẩu mới", validators=[DataRequired(message="Vui lòng nhập mật khẩu mới."), Length(min=6, max=128)])
    confirm_password = PasswordField("Nhập lại mật khẩu mới", validators=[DataRequired(message="Vui lòng xác nhận mật khẩu mới."), EqualTo("password", message="Mật khẩu nhập lại không khớp.")])
    submit = SubmitField("Đặt lại mật khẩu")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Mật khẩu", validators=[DataRequired()])
    remember = BooleanField("Ghi nhớ đăng nhập")
    submit = SubmitField("Đăng nhập")

