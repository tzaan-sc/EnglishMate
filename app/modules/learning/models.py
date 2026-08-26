from app.extensions import db
from app.modules.auth.models import now


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


class FlashcardSet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_public = db.Column(db.Boolean, default=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    created_at = db.Column(db.DateTime(timezone=True), default=now, nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=now, onupdate=now, nullable=False)
    
    user = db.relationship("User", backref=db.backref("flashcard_sets", cascade="all, delete-orphan"))


class FlashcardItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    set_id = db.Column(db.Integer, db.ForeignKey("flashcard_set.id"), nullable=False, index=True)
    term = db.Column(db.String(500), nullable=False)
    definition = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(500), nullable=True)
    order = db.Column(db.Integer, nullable=False, default=0)
    
    flashcard_set = db.relationship("FlashcardSet", backref=db.backref("items", cascade="all, delete-orphan", order_by="FlashcardItem.order"))

