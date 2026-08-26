from app import create_app
from app.extensions import db
from app.modules.exams.models import Exam, ExamQuestion, ExamSubmission, ExamAnswerDetail

def setup_exams():
    app = create_app()
    with app.app_context():
        # Create all tables (it will create the newly added Exam tables)
        db.create_all()
        print("Database tables created successfully!")

if __name__ == "__main__":
    setup_exams()
