"""Browser E2E tests (Playwright) covering core user journeys."""
from tests.e2e.conftest import login_via_ui


def test_login_page_renders(page, base_url):
    page.goto(f"{base_url}/auth/login")
    assert page.locator("input[name='email']").is_visible()
    assert page.locator("input[name='password']").is_visible()


def test_student_can_login(page, base_url):
    login_via_ui(page, base_url)
    assert "/auth/login" not in page.url


def test_wrong_password_stays_on_login(page, base_url):
    login_via_ui(page, base_url, password="wrong-password")
    assert "/auth/login" in page.url


def test_protected_page_redirects_anonymous(page, base_url):
    page.goto(f"{base_url}/lessons")
    assert "/auth/login" in page.url


def test_student_cannot_open_admin(page, base_url):
    login_via_ui(page, base_url)
    response = page.goto(f"{base_url}/admin")
    assert response is not None and response.status == 403


def test_admin_can_open_admin_area(page, base_url):
    login_via_ui(page, base_url, "admin@test.com", "admin123")
    response = page.goto(f"{base_url}/admin")
    assert response is not None and response.status == 200


def test_logged_in_user_sees_lessons(page, base_url):
    login_via_ui(page, base_url)
    page.goto(f"{base_url}/lessons")
    page.wait_for_load_state("networkidle")
    assert "E2E lesson" in page.content()


def test_unknown_page_shows_404(page, base_url):
    response = page.goto(f"{base_url}/this-page-does-not-exist")
    assert response is not None and response.status == 404
