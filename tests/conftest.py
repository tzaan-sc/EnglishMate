import pytest

from app import create_app
from app.config import TestConfig
from app.extensions import db
from app.modules.learning.models import Lesson, Question, Vocabulary
from app.modules.auth.models import User


@pytest.fixture()
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        admin = User(username="admin", email="admin@test.com", role="ADMIN")
        admin.set_password("admin123")
        user = User(username="student", email="student@test.com")
        user.set_password("user123")
        blocked = User(username="blocked", email="blocked@test.com", is_active=False)
        blocked.set_password("user123")
        db.session.add_all([admin, user, blocked])
        lesson = Lesson(title="Test lesson", level="A1", skill="Grammar", short_description="A useful lesson",
                        content="Test content", examples="This is an example.")
        word = Vocabulary(word="hello", pronunciation="/həˈləʊ/", part_of_speech="interjection",
                          meaning_vi="xin chào", example_en="Hello, Mai!", example_vi="Xin chào Mai!",
                          topic="Daily Life", level="A1")
        db.session.add_all([lesson, word])
        for i in range(10):
            db.session.add(Question(question_text=f"Question {i}", option_a="Correct", option_b="Wrong B",
                                    option_c="Wrong C", option_d="Wrong D", correct_option="A",
                                    explanation="A is correct.", level="A1", topic="Daily Life"))
        db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def login(client, email="student@test.com", password="user123"):
    return client.post("/auth/login", data={"email": email, "password": password}, follow_redirects=True)

