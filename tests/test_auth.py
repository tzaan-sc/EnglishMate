from app.extensions import db
from app.modules.auth.models import User


def test_register_flow_with_otp(client):
    # Test registration fails without checking terms & privacy
    res_fail = client.post(
        "/auth/register",
        data={
            "username": "newstudent",
            "email": "new@test.com",
            "password": "Secret123!",
            "confirm_password": "Secret123!",
        },
        follow_redirects=True,
    )
    assert res_fail.status_code == 200
    assert "Bạn phải đồng ý với Điều khoản sử dụng".encode("utf-8") in res_fail.data

    # Test registration succeeds when terms & privacy are checked
    res_reg = client.post(
        "/auth/register",
        data={
            "username": "newstudent",
            "email": "new@test.com",
            "password": "Secret123!",
            "confirm_password": "Secret123!",
            "terms_agree": "y",
            "privacy_agree": "y",
        },
        follow_redirects=True,
    )
    assert res_reg.status_code == 200
    assert "Xác thực Email".encode("utf-8") in res_reg.data

    # Check user in DB has verification code
    with client.application.app_context():
        user = User.query.filter_by(email="new@test.com").first()
        assert user is not None
        assert user.is_email_verified is False
        otp_code = user.email_verification_code
        user_id = user.id

    # Test wrong OTP submission
    res_wrong_otp = client.post(
        f"/auth/verify-email/{user_id}",
        data={"code": "000000"},
        follow_redirects=True,
    )
    assert "Mã xác minh không chính xác".encode("utf-8") in res_wrong_otp.data

    # Test correct OTP submission
    res_correct_otp = client.post(
        f"/auth/verify-email/{user_id}",
        data={"code": otp_code},
        follow_redirects=True,
    )
    assert "Xác thực email thành công".encode("utf-8") in res_correct_otp.data

    # Login with newly verified user
    res_login = client.post(
        "/auth/login",
        data={"email": "new@test.com", "password": "Secret123!"},
        follow_redirects=True,
    )
    assert res_login.status_code == 200
    assert "newstudent".encode("utf-8") in res_login.data


def test_google_oauth_login(client):
    response = client.get("/auth/google", follow_redirects=False)
    assert response.status_code in (200, 302)


def test_facebook_oauth_login(client):
    response = client.get("/auth/facebook", follow_redirects=False)
    assert response.status_code in (200, 302)


def test_blocked_user_cannot_login(client):
    response = client.post("/auth/login", data={"email": "blocked@test.com", "password": "user123"}, follow_redirects=True)
    assert response.status_code == 200
    assert "Tài khoản đã bị khóa".encode("utf-8") in response.data
    assert client.get("/dashboard").status_code == 302


def test_login_attempts_and_lockout(client):
    # Failed attempts 1 to 4
    for i in range(1, 5):
        res = client.post("/auth/login", data={"email": "student@test.com", "password": "wrong_password"}, follow_redirects=True)
        assert res.status_code == 200
        assert f"Bạn còn {5 - i} lần thử".encode("utf-8") in res.data

    # 5th failed attempt -> Lockout
    res_lockout = client.post("/auth/login", data={"email": "student@test.com", "password": "wrong_password"}, follow_redirects=True)
    assert res_lockout.status_code == 200
    assert "Tài khoản của bạn đã bị khóa 15 phút".encode("utf-8") in res_lockout.data

    # Subsequent attempt during lockout -> Blocked
    res_blocked = client.post("/auth/login", data={"email": "student@test.com", "password": "user123"}, follow_redirects=True)
    assert "Tài khoản tạm thời bị khóa".encode("utf-8") in res_blocked.data


def test_forgot_password_page(client):
    res_get = client.get("/auth/forgot-password")
    assert res_get.status_code == 200
    assert "Khôi phục mật khẩu".encode("utf-8") in res_get.data

    res_post = client.post("/auth/forgot-password", data={"email": "student@test.com"}, follow_redirects=True)
    assert res_post.status_code == 200
    assert "Hướng dẫn khôi phục mật khẩu đã được gửi đến email".encode("utf-8") in res_post.data


def test_full_password_reset_flow(client):
    # Request password reset
    res = client.post("/auth/forgot-password", data={"email": "student@test.com"}, follow_redirects=True)
    assert res.status_code == 200

    with client.application.app_context():
        user = User.query.filter_by(email="student@test.com").first()
        assert user.reset_token is not None
        token = user.reset_token

    # Invalid token test
    res_invalid = client.get("/auth/reset-password/invalid_token_123", follow_redirects=True)
    assert "Đường dẫn khôi phục mật khẩu không hợp lệ".encode("utf-8") in res_invalid.data

    # Valid token test GET
    res_reset_get = client.get(f"/auth/reset-password/{token}")
    assert res_reset_get.status_code == 200
    assert "Đặt lại mật khẩu".encode("utf-8") in res_reset_get.data

    # Valid token test POST (Mismatch passwords)
    res_mismatch = client.post(
        f"/auth/reset-password/{token}",
        data={"password": "NewSecret123!", "confirm_password": "Different123!"},
        follow_redirects=True,
    )
    assert "Mật khẩu nhập lại không khớp".encode("utf-8") in res_mismatch.data

    # Valid token test POST (Matching passwords)
    res_reset_post = client.post(
        f"/auth/reset-password/{token}",
        data={"password": "NewSecret123!", "confirm_password": "NewSecret123!"},
        follow_redirects=True,
    )
    assert "Đặt lại mật khẩu thành công".encode("utf-8") in res_reset_post.data

    # Verify user token cleared and login works with new password
    with client.application.app_context():
        user = User.query.filter_by(email="student@test.com").first()
        assert user.reset_token is None

    res_new_login = client.post("/auth/login", data={"email": "student@test.com", "password": "NewSecret123!"}, follow_redirects=True)
    assert res_new_login.status_code == 200
    assert "student".encode("utf-8") in res_new_login.data


