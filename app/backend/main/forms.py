from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length


class EditProfileForm(FlaskForm):
    full_name = StringField("Họ và tên", validators=[Length(max=100, message="Họ và tên không vượt quá 100 ký tự.")])
    avatar = FileField("Ảnh đại diện", validators=[FileAllowed(["jpg", "jpeg", "png", "webp", "gif"], "Chỉ hỗ trợ file ảnh JPG, PNG, WEBP, GIF.")])
    submit = SubmitField("Cập nhật thông tin")


class ChangeEmailForm(FlaskForm):
    new_email = StringField("Email mới", validators=[DataRequired(message="Vui lòng nhập email mới."), Email(message="Email không hợp lệ."), Length(max=120)])
    submit = SubmitField("Gửi mã xác nhận OTP")


class VerifyNewEmailForm(FlaskForm):
    otp_code = StringField("Mã OTP xác minh", validators=[DataRequired(message="Vui lòng nhập mã OTP 6 chữ số."), Length(min=6, max=6, message="Mã OTP gồm 6 chữ số.")])
    submit = SubmitField("Xác nhận đổi email")


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField("Mật khẩu hiện tại", validators=[DataRequired(message="Vui lòng nhập mật khẩu hiện tại.")])
    new_password = PasswordField("Mật khẩu mới", validators=[DataRequired(message="Vui lòng nhập mật khẩu mới."), Length(min=6, max=128, message="Mật khẩu mới từ 6 đến 128 ký tự.")])
    confirm_password = PasswordField("Nhập lại mật khẩu mới", validators=[DataRequired(message="Vui lòng xác nhận mật khẩu mới."), EqualTo("new_password", message="Mật khẩu mới nhập lại không khớp.")])
    submit = SubmitField("Đổi mật khẩu")


class DeleteAccountForm(FlaskForm):
    confirm_password = PasswordField("Nhập mật khẩu để xác nhận xóa", validators=[DataRequired(message="Vui lòng nhập mật khẩu xác nhận.")])
    submit = SubmitField("Xóa tài khoản vĩnh viễn")
