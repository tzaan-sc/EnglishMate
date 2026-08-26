from app import create_app
from app.extensions import db
from app.modules.exams.services import import_exam_from_json
from app.modules.exams.models import Exam, ExamQuestion

def run_import():
    app = create_app()
    with app.app_context():
        # Clean up old sample exam if it exists
        old_exam = Exam.query.filter_by(title="Sample Test 1").first()
        if old_exam:
            db.session.delete(old_exam)
            db.session.commit()
            print("Deleted old sample exam.")
            
        print("Importing JSON...")
        exam = import_exam_from_json(
            "sample_exam.json", 
            category="TOEIC", 
            title="Sample Test 1", 
            duration=60
        )
        print(f"Imported exam: ID={exam.id}, Title={exam.title}")
        
        # Verify
        questions = ExamQuestion.query.filter_by(exam_id=exam.id).all()
        print(f"Total questions imported: {len(questions)}")
        for q in questions:
            print(f"- {q.part} [{q.skill}] {q.type}: {q.question_text}")
            print(f"  Media: {q.media_info}")
            print(f"  Correct: {q.correct_answer}")

if __name__ == "__main__":
    run_import()
