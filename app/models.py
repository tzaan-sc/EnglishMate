from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db


def now():
    return datetime.now(timezone.utc)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(40), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(10), nullable=False, default="USER")
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime(timezone=True), default=now, nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=now, onupdate=now, nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role == "ADMIN"


class Lesson(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(160), nullable=False)
    level = db.Column(db.String(2), nullable=False, index=True)
    skill = db.Column(db.String(30), nullable=False, index=True)
    short_description = db.Column(db.String(280), nullable=False)
    content = db.Column(db.Text, nullable=False)
    examples = db.Column(db.Text, nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime(timezone=True), default=now, nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=now, onupdate=now, nullable=False)


class Vocabulary(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(100), nullable=False, index=True)
    pronunciation = db.Column(db.String(100), nullable=False)
    part_of_speech = db.Column(db.String(30), nullable=False)
    meaning_vi = db.Column(db.String(200), nullable=False)
    example_en = db.Column(db.String(300), nullable=False)
    example_vi = db.Column(db.String(300), nullable=False)
    topic = db.Column(db.String(80), nullable=False, index=True)
    level = db.Column(db.String(2), nullable=False, index=True)
    created_at = db.Column(db.DateTime(timezone=True), default=now, nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=now, onupdate=now, nullable=False)


class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_text = db.Column(db.String(500), nullable=False)
    option_a = db.Column(db.String(200), nullable=False)
    option_b = db.Column(db.String(200), nullable=False)
    option_c = db.Column(db.String(200), nullable=False)
    option_d = db.Column(db.String(200), nullable=False)
    correct_option = db.Column(db.String(1), nullable=False)
    explanation = db.Column(db.String(500), nullable=False)
    level = db.Column(db.String(2), nullable=False, index=True)
    topic = db.Column(db.String(80), nullable=False, index=True)
    created_at = db.Column(db.DateTime(timezone=True), default=now, nullable=False)

    @property
    def options(self):
        return {"A": self.option_a, "B": self.option_b, "C": self.option_c, "D": self.option_d}


class LessonProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    lesson_id = db.Column(db.Integer, db.ForeignKey("lesson.id"), nullable=False, index=True)
    completed_at = db.Column(db.DateTime(timezone=True), default=now, nullable=False)
    user = db.relationship("User", backref="lesson_progress")
    lesson = db.relationship("Lesson", backref="progress_records")
    __table_args__ = (db.UniqueConstraint("user_id", "lesson_id"),)


class VocabularyProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    vocabulary_id = db.Column(db.Integer, db.ForeignKey("vocabulary.id"), nullable=False, index=True)
    learned_count = db.Column(db.Integer, nullable=False, default=0)
    review_count = db.Column(db.Integer, nullable=False, default=0)
    last_reviewed_at = db.Column(db.DateTime(timezone=True), default=now, nullable=False)
    user = db.relationship("User", backref="vocabulary_progress")
    vocabulary = db.relationship("Vocabulary", backref="progress_records")
    __table_args__ = (db.UniqueConstraint("user_id", "vocabulary_id"),)


class QuizAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    level = db.Column(db.String(2), nullable=False)
    topic = db.Column(db.String(80), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    total_questions = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=now, nullable=False)
    user = db.relationship("User", backref="quiz_attempts")


class QuizAttemptAnswer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    attempt_id = db.Column(db.Integer, db.ForeignKey("quiz_attempt.id"), nullable=False, index=True)
    question_id = db.Column(db.Integer, db.ForeignKey("question.id"), nullable=False)
    selected_option = db.Column(db.String(1), nullable=True)
    is_correct = db.Column(db.Boolean, nullable=False, default=False)
    attempt = db.relationship("QuizAttempt", backref=db.backref("answers", cascade="all, delete-orphan"))
    question = db.relationship("Question")


class ToeicTest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(160), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=now, nullable=False)


class ToeicPassage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    test_id = db.Column(db.Integer, db.ForeignKey("toeic_test.id"), nullable=False, index=True)
    part = db.Column(db.Integer, nullable=False)  # 6 or 7
    passage_text = db.Column(db.Text, nullable=False)
    test = db.relationship("ToeicTest", backref=db.backref("passages", cascade="all, delete-orphan"))


class ToeicQuestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    test_id = db.Column(db.Integer, db.ForeignKey("toeic_test.id"), nullable=False, index=True)
    passage_id = db.Column(db.Integer, db.ForeignKey("toeic_passage.id"), nullable=True, index=True)
    part = db.Column(db.Integer, nullable=False)  # 5, 6, 7
    question_number = db.Column(db.Integer, nullable=False)  # 101 to 200
    question_text = db.Column(db.String(500), nullable=True)
    option_a = db.Column(db.String(200), nullable=False)
    option_b = db.Column(db.String(200), nullable=False)
    option_c = db.Column(db.String(200), nullable=False)
    option_d = db.Column(db.String(200), nullable=False)
    correct_option = db.Column(db.String(1), nullable=False)  # A, B, C, D
    explanation = db.Column(db.Text, nullable=False)
    test = db.relationship("ToeicTest", backref=db.backref("questions", cascade="all, delete-orphan"))
    passage = db.relationship("ToeicPassage", backref=db.backref("questions", order_by="ToeicQuestion.question_number", cascade="all, delete-orphan"))


class ToeicAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    test_id = db.Column(db.Integer, db.ForeignKey("toeic_test.id"), nullable=False, index=True)
    score = db.Column(db.Integer, nullable=False, default=0)
    total_questions = db.Column(db.Integer, nullable=False, default=100)
    time_spent = db.Column(db.Integer, nullable=False, default=0)  # in seconds
    created_at = db.Column(db.DateTime(timezone=True), default=now, nullable=False)
    completed_at = db.Column(db.DateTime(timezone=True), nullable=True)
    is_submitted = db.Column(db.Boolean, nullable=False, default=False)
    user = db.relationship("User", backref="toeic_attempts")
    test = db.relationship("ToeicTest", backref="attempts")


class ToeicAttemptAnswer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    attempt_id = db.Column(db.Integer, db.ForeignKey("toeic_attempt.id"), nullable=False, index=True)
    question_id = db.Column(db.Integer, db.ForeignKey("toeic_question.id"), nullable=False, index=True)
    selected_option = db.Column(db.String(1), nullable=True)
    is_correct = db.Column(db.Boolean, nullable=False, default=False)
    attempt = db.relationship("ToeicAttempt", backref=db.backref("answers", cascade="all, delete-orphan"))
    question = db.relationship("ToeicQuestion")


