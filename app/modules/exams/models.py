from app.extensions import db
from app.modules.auth.models import now


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
