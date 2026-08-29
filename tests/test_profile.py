from app.extensions import db
from app.modules.auth.models import User


def test_view_profile_info(client):
    # Login student user
    client.post("/auth/login", data={"email": "student@test.com", "password": "user123"}, follow_redirects=True)

    res = client.get("/profile")
    assert res.status_code == 200
    assert "Hồ sơ cá nhân".encode("utf-8") in res.data
    assert "student@test.com".encode("utf-8") in res.data
    assert "Ngày tham gia".encode("utf-8") in res.data
    assert "Đăng nhập gần nhất".encode("utf-8") in res.data


def test_edit_full_name(client):
    client.post("/auth/login", data={"email": "student@test.com", "password": "user123"}, follow_redirects=True)

    res = client.post("/profile/edit-info", data={"full_name": "Nguyễn Văn Học Viên"}, follow_redirects=True)
    assert res.status_code == 200
    assert "Cập nhật thông tin cá nhân thành công".encode("utf-8") in res.data

    with client.application.app_context():
        user = User.query.filter_by(email="student@test.com").first()
        assert user.full_name == "Nguyễn Văn Học Viên"


def test_change_email_with_otp_verification(client):
    client.post("/auth/login", data={"email": "student@test.com", "password": "user123"}, follow_redirects=True)

    # Step 1: Request email change
    res_req = client.post("/profile/change-email", data={"new_email": "updatedstudent@test.com"}, follow_redirects=True)
    assert res_req.status_code == 200
    assert "Mã OTP xác nhận đã được gửi".encode("utf-8") in res_req.data

    with client.application.app_context():
        user = User.query.filter_by(username="student").first()
        assert user.pending_email == "updatedstudent@test.com"
        otp_code = user.pending_email_otp
        assert otp_code is not None

    # Step 2: Submit OTP verification code
    res_verify = client.post("/profile/verify-email", data={"otp_code": otp_code}, follow_redirects=True)
    assert res_verify.status_code == 200
    assert "Cập nhật địa chỉ email mới thành công".encode("utf-8") in res_verify.data

    with client.application.app_context():
        user = User.query.filter_by(username="student").first()
        assert user.email == "updatedstudent@test.com"
        assert user.pending_email is None


def test_change_password_profile(client):
    client.post("/auth/login", data={"email": "student@test.com", "password": "user123"}, follow_redirects=True)

    # Wrong current password
    res_wrong = client.post(
        "/profile/change-password",
        data={"current_password": "wrongpassword", "new_password": "NewUserPassword123!", "confirm_password": "NewUserPassword123!"},
        follow_redirects=True,
    )
    assert "Mật khẩu hiện tại không chính xác".encode("utf-8") in res_wrong.data

    # Correct current password
    res_correct = client.post(
        "/profile/change-password",
        data={"current_password": "user123", "new_password": "NewUserPassword123!", "confirm_password": "NewUserPassword123!"},
        follow_redirects=True,
    )
    assert "Đổi mật khẩu thành công".encode("utf-8") in res_correct.data

    # Verify login works with new password
    client.post("/auth/logout", follow_redirects=True)
    res_login = client.post("/auth/login", data={"email": "student@test.com", "password": "NewUserPassword123!"}, follow_redirects=True)
    assert res_login.status_code == 200
    assert "student".encode("utf-8") in res_login.data


def test_deactivate_account(client):
    client.post("/auth/login", data={"email": "student@test.com", "password": "user123"}, follow_redirects=True)

    res_deactivate = client.post("/profile/deactivate", follow_redirects=True)
    assert res_deactivate.status_code == 200
    assert "Tài khoản của bạn đã được vô hiệu hóa tạm thời".encode("utf-8") in res_deactivate.data

    # Try logging in with deactivated user
    res_login = client.post("/auth/login", data={"email": "student@test.com", "password": "user123"}, follow_redirects=True)
    assert "Tài khoản đã bị khóa".encode("utf-8") in res_login.data


def test_delete_account_profile(client):
    client.post("/auth/login", data={"email": "student@test.com", "password": "user123"}, follow_redirects=True)

    res_delete = client.post("/profile/delete", data={"confirm_password": "user123"}, follow_redirects=True)
    assert res_delete.status_code == 200
    assert "Tài khoản của bạn đã được xóa vĩnh viễn".encode("utf-8") in res_delete.data

    with client.application.app_context():
        user = User.query.filter_by(email="student@test.com").first()
        assert user is None
