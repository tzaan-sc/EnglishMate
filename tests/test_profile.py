from app.extensions import db
from app.backend.auth.models import EmailChangeHistory, User


def test_view_profile_info(client):
    # Login student user
    client.post("/auth/login", data={"email": "student@test.com", "password": "user123"}, follow_redirects=True)

    res = client.get("/profile")
    assert res.status_code == 200
    assert "Hồ sơ cá nhân".encode("utf-8") in res.data
    assert "student@test.com".encode("utf-8") in res.data
    assert "Ngày tham gia".encode("utf-8") in res.data
    assert "Đăng nhập gần nhất".encode("utf-8") in res.data
    assert "Nhật ký & Lịch sử thay đổi Email".encode("utf-8") in res.data
    assert "Chưa có nhật ký thay đổi email".encode("utf-8") in res.data


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

        # Verify EmailChangeHistory was recorded
        history = EmailChangeHistory.query.filter_by(user_id=user.id).order_by(EmailChangeHistory.changed_at.desc()).all()
        assert len(history) == 1
        record = history[0]
        assert record.old_email == "student@test.com"
        assert record.new_email == "updatedstudent@test.com"
        assert record.ip_address is not None
        assert record.changed_at is not None
        assert record.device_info is not None

    # Step 3: Check profile view shows the change history record
    res_profile = client.get("/profile")
    assert res_profile.status_code == 200
    assert "student@test.com".encode("utf-8") in res_profile.data
    assert "updatedstudent@test.com".encode("utf-8") in res_profile.data
    assert "Đã xác thực OTP".encode("utf-8") in res_profile.data
    assert "1 lần cập nhật".encode("utf-8") in res_profile.data


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


def test_admin_profile_view(client):
    # Setup admin user
    with client.application.app_context():
        admin = User.query.filter_by(email="admin_profile@test.com").first()
        if not admin:
            admin = User(username="admin_prof", email="admin_profile@test.com", role="ADMIN")
            admin.set_password("AdminPass123!")
            db.session.add(admin)
            db.session.commit()

    client.post("/auth/login", data={"email": "admin_profile@test.com", "password": "AdminPass123!"}, follow_redirects=True)
    res = client.get("/profile")
    assert res.status_code == 200
    assert "TÀI KHOẢN QUẢN TRỊ VIÊN HỆ THỐNG".encode("utf-8") in res.data
    assert "Bảng điều khiển Admin".encode("utf-8") in res.data
    assert "Quyền hạn & Vai trò".encode("utf-8") in res.data
    assert "Nhật ký của tôi".encode("utf-8") in res.data
    assert "Hành động quản trị".encode("utf-8") in res.data


def test_admin_cannot_delete_account(client):
    with client.application.app_context():
        admin = User.query.filter_by(email="admin_profile@test.com").first()
        if not admin:
            admin = User(username="admin_prof", email="admin_profile@test.com", role="ADMIN")
            admin.set_password("AdminPass123!")
            db.session.add(admin)
            db.session.commit()

    client.post("/auth/login", data={"email": "admin_profile@test.com", "password": "AdminPass123!"}, follow_redirects=True)
    res = client.post("/profile/delete", data={"confirm_password": "AdminPass123!"}, follow_redirects=True)
    assert res.status_code == 200
    assert "không thể tự xóa".encode("utf-8") in res.data

    with client.application.app_context():
        admin = User.query.filter_by(email="admin_profile@test.com").first()
        assert admin is not None


def test_email_change_history_multiple_and_cascade_delete(client):
    with client.application.app_context():
        user = User.query.filter_by(username="history_tester").first()
        if not user:
            user = User(username="history_tester", email="tester_origin@test.com", role="USER")
            user.set_password("user123")
            db.session.add(user)
            db.session.commit()

    # Login
    client.post("/auth/login", data={"email": "tester_origin@test.com", "password": "user123"}, follow_redirects=True)

    # First change: tester_origin@test.com -> tester_v2@test.com
    client.post("/profile/change-email", data={"new_email": "tester_v2@test.com"}, follow_redirects=True)
    with client.application.app_context():
        user = User.query.filter_by(username="history_tester").first()
        otp1 = user.pending_email_otp
    client.post("/profile/verify-email", data={"otp_code": otp1}, follow_redirects=True)

    # Second change: tester_v2@test.com -> tester_v3@test.com
    client.post("/profile/change-email", data={"new_email": "tester_v3@test.com"}, follow_redirects=True)
    with client.application.app_context():
        user = User.query.filter_by(username="history_tester").first()
        otp2 = user.pending_email_otp
    client.post("/profile/verify-email", data={"otp_code": otp2}, follow_redirects=True)

    with client.application.app_context():
        user = User.query.filter_by(username="history_tester").first()
        assert user.email == "tester_v3@test.com"
        records = user.email_change_history.all()
        assert len(records) == 2
        # Ordered by changed_at desc: most recent first
        assert records[0].old_email == "tester_v2@test.com"
        assert records[0].new_email == "tester_v3@test.com"
        assert records[1].old_email == "tester_origin@test.com"
        assert records[1].new_email == "tester_v2@test.com"
        uid = user.id

    # Check that profile shows 2 updates
    res_prof = client.get("/profile")
    assert "2 lần cập nhật".encode("utf-8") in res_prof.data
    assert "tester_v2@test.com".encode("utf-8") in res_prof.data
    assert "tester_v3@test.com".encode("utf-8") in res_prof.data

    # Delete account and verify cascade deletion of email change history
    client.post("/profile/delete", data={"confirm_password": "user123"}, follow_redirects=True)
    with client.application.app_context():
        remaining_history = EmailChangeHistory.query.filter_by(user_id=uid).all()
        assert len(remaining_history) == 0


