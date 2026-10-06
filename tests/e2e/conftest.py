"""Fixtures for browser-based End-to-End tests (Playwright).

E2E tests are opt-in so that the regular `pytest` run stays fast and does not
require browsers. Enable them with:  RUN_E2E=1 pytest tests/e2e
Setup:  pip install -r requirements-e2e.txt && playwright install chromium
"""
import os
import tempfile
import threading

import pytest

if os.getenv("RUN_E2E") != "1":
    collect_ignore_glob = ["test_*.py"]


@pytest.fixture(scope="session")
def live_server():
    from werkzeug.serving import make_server

    from app import create_app
    from app.backend.auth.models import User
    from app.backend.learning.models import Lesson, Vocabulary
    from app.config import TestConfig
    from app.extensions import db

    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)

    class E2EConfig(TestConfig):
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{db_path}"
        SERVER_NAME = None

    app = create_app(E2EConfig)
    with app.app_context():
        db.create_all()
        admin = User(username="admin", email="admin@test.com", role="ADMIN")
        admin.set_password("admin123")
        student = User(username="student", email="student@test.com")
        student.set_password("user123")
        db.session.add_all([admin, student])
        db.session.add(Lesson(title="E2E lesson", level="A1", skill="Grammar",
                              short_description="A useful lesson", content="Test content",
                              examples="This is an example."))
        db.session.add(Vocabulary(word="hello", pronunciation="/həˈləʊ/", part_of_speech="interjection",
                                  meaning_vi="xin chào", example_en="Hello, Mai!",
                                  example_vi="Xin chào Mai!", topic="Daily Life", level="A1"))
        db.session.commit()

    server = make_server("127.0.0.1", 0, app, threaded=True)
    port = server.server_port
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        server.shutdown()
        thread.join(timeout=5)
        with app.app_context():
            db.session.remove()
            db.engine.dispose()
        try:
            os.remove(db_path)
        except OSError:
            pass


@pytest.fixture()
def base_url(live_server):
    return live_server


def login_via_ui(page, base_url, email="student@test.com", password="user123"):
    page.goto(f"{base_url}/auth/login")
    page.fill("input[name='email']", email)
    page.fill("input[name='password']", password)
    page.locator("form button[type='submit'], form input[type='submit']").first.click()
    page.wait_for_load_state("networkidle")
