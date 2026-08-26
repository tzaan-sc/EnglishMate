from app.modules.auth.models import User


def test_register_login_logout(client):
    response = client.post("/auth/register", data={"username": "newstudent", "email": "new@test.com",
                           "password": "secret12", "confirm_password": "secret12"}, follow_redirects=True)
    assert response.status_code == 200
    assert b"new@test.com" not in response.data
    response = client.post("/auth/login", data={"email": "new@test.com", "password": "secret12"}, follow_redirects=True)
    assert response.status_code == 200
    assert b"newstudent" in response.data
    response = client.post("/auth/logout", follow_redirects=True)
    assert response.status_code == 200
    assert b"EnglishMate" in response.data


def test_blocked_user_cannot_login(client):
    response = client.post("/auth/login", data={"email": "blocked@test.com", "password": "user123"}, follow_redirects=True)
    assert response.status_code == 200
    assert "Tài khoản đã bị khóa".encode() in response.data
    assert client.get("/dashboard").status_code == 302

