import time
from app.extensions import db
from app.modules.auth.models import User, UserSession


def test_session_creation_on_login(client):
    res_login = client.post("/auth/login", data={"email": "student@test.com", "password": "user123"}, follow_redirects=True)
    assert res_login.status_code == 200

    with client.application.app_context():
        user = User.query.filter_by(email="student@test.com").first()
        sessions = UserSession.query.filter_by(user_id=user.id, is_active=True).all()
        assert len(sessions) >= 1


def test_ping_session(client):
    client.post("/auth/login", data={"email": "student@test.com", "password": "user123"}, follow_redirects=True)

    res_ping = client.post("/auth/ping-session")
    assert res_ping.status_code == 200
    assert res_ping.json["status"] == "ok"


def test_revoke_specific_session(client):
    client.post("/auth/login", data={"email": "student@test.com", "password": "user123"}, follow_redirects=True)

    with client.application.app_context():
        user = User.query.filter_by(email="student@test.com").first()
        sess = UserSession(id="dummy_session_456", user_id=user.id, device_info="Firefox trên macOS", is_active=True)
        db.session.add(sess)
        db.session.commit()

    res_revoke = client.post("/sessions/revoke/dummy_session_456", follow_redirects=True)
    assert res_revoke.status_code == 200
    assert "Đã hủy phiên đăng nhập thành công".encode("utf-8") in res_revoke.data

    with client.application.app_context():
        sess_check = db.session.get(UserSession, "dummy_session_456")
        assert sess_check.is_active is False


def test_revoke_all_other_sessions(client):
    client.post("/auth/login", data={"email": "student@test.com", "password": "user123"}, follow_redirects=True)

    with client.application.app_context():
        user = User.query.filter_by(email="student@test.com").first()
        sess1 = UserSession(id="other_sess_1", user_id=user.id, device_info="Chrome trên Android", is_active=True)
        sess2 = UserSession(id="other_sess_2", user_id=user.id, device_info="Safari trên iOS", is_active=True)
        db.session.add_all([sess1, sess2])
        db.session.commit()

    res_revoke_all = client.post("/sessions/revoke-all", follow_redirects=True)
    assert res_revoke_all.status_code == 200
    assert "Đã đăng xuất khỏi".encode("utf-8") in res_revoke_all.data

    with client.application.app_context():
        s1 = db.session.get(UserSession, "other_sess_1")
        s2 = db.session.get(UserSession, "other_sess_2")
        assert s1.is_active is False
        assert s2.is_active is False


def test_session_timeout_inactivity(client):
    client.post("/auth/login", data={"email": "student@test.com", "password": "user123"}, follow_redirects=True)

    # Simulate 35 minutes of inactivity (over 1800 seconds)
    with client.session_transaction() as sess:
        sess["last_activity_ts"] = time.time() - 2100

    res_expired = client.get("/dashboard", follow_redirects=True)
    assert res_expired.status_code == 200
    assert "Phiên đăng nhập của bạn đã hết hạn do không hoạt động trong 30 phút".encode("utf-8") in res_expired.data
