from tests.conftest import login


def test_user_cannot_access_admin(client):
    login(client)
    assert client.get("/admin").status_code == 403


def test_admin_can_access_admin(client):
    login(client, "admin@test.com", "admin123")
    response = client.get("/admin")
    assert response.status_code == 200
    assert "Tổng quan hệ thống".encode() in response.data


def test_all_admin_pages_render(client):
    login(client, "admin@test.com", "admin123")
    for path in ["/admin", "/admin/lessons", "/admin/lessons/new", "/admin/vocabulary",
                 "/admin/vocabulary/new", "/admin/users"]:
        response = client.get(path)
        assert response.status_code == 200, path
