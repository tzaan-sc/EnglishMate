import time
from threading import Thread
from app.extensions import db
from app.modules.exams.models import ExamSubmission, ExamAnswerDetail, ExamQuestion

def async_grade_submission(app, submission_id):
    """
    Background task để giả lập AI chấm điểm.
    Cần truyền Flask app instance để tạo app_context.
    """
    with app.app_context():
        # Giả lập thời gian gọi API AI (VD: OpenAI/Whisper) mất 5-10 giây
        print(f"[AI Queue] Đang bắt đầu chấm bài cho Submission ID: {submission_id}...")
        time.sleep(5)
        
        submission = ExamSubmission.query.get(submission_id)
        if not submission or submission.status == 'COMPLETED':
            return
            
        details = ExamAnswerDetail.query.filter_by(submission_id=submission.id).all()
        
        total_score = submission.total_score or 0
        
        for ans in details:
            # Chấm điểm những câu tự luận/ghi âm (is_correct đang là None)
            if ans.is_correct is None:
                q = ExamQuestion.query.get(ans.question_id)
                if q and q.type in ['ESSAY', 'AUDIO_RECORD']:
                    user_text = ans.user_response.get('text', '')
                    
                    # --- MOCK AI GRADING LOGIC ---
                    # TODO: Sau này user sẽ thay thế đoạn này bằng code gọi API thật
                    # response = openai.ChatCompletion.create(...)
                    
                    # Logic chấm điểm tạm thời:
                    if user_text and len(user_text) > 15:
                        ans.is_correct = True
                        ans.score = 1.0
                        # Cập nhật thêm feedback của AI vào file JSON
                        # Gán mảng dict mới để SQLAlchemy nhận diện sự thay đổi (JSON Mutation)
                        resp = dict(ans.user_response)
                        resp['ai_feedback'] = "Tuyệt vời! Bạn sử dụng từ vựng phong phú và cấu trúc câu tốt."
                        ans.user_response = resp
                        total_score += 1.0
                    else:
                        ans.is_correct = False
                        ans.score = 0.0
                        resp = dict(ans.user_response)
                        resp['ai_feedback'] = "Câu trả lời quá ngắn hoặc thiếu ý. Hãy cố gắng triển khai ý chi tiết hơn."
                        ans.user_response = resp
                        
        submission.total_score = total_score
        submission.status = 'COMPLETED'
        db.session.commit()
        print(f"[AI Queue] Hoàn tất chấm bài Submission ID: {submission_id}. Tổng điểm: {total_score}")

def trigger_ai_grading(app, submission_id):
    """
    Kích hoạt chấm điểm ngầm.
    Sau này cài Celery/Redis, chỉ cần đổi hàm này thành: async_grade_submission.delay(submission_id)
    """
    thread = Thread(target=async_grade_submission, args=(app, submission_id))
    thread.daemon = True
    thread.start()
