# 🏛️ ENGLISHMATE — KIẾN TRÚC & QUYẾT ĐỊNH THIẾT KẾ (SYSTEM SPECIFICATIONS & ARCHITECTURE)

Tài liệu này lưu trữ chi tiết kỹ thuật chuyên sâu, quyết định kiến trúc hệ thống và quy trình kiểm thử của nền tảng **EnglishMate**.

---

## 🛠️ 1. Công Nghệ & Thư Viện Sử Dụng

- **Backend Framework:** Python 3.10+, Flask 3.1.1, Flask-SQLAlchemy 3.1.1, Flask-Login, Flask-WTF.
- **Database:** PostgreSQL (hỗ trợ chuyển đổi tự động sang SQLite local), connection pool tối ưu.
- **Frontend:** Jinja2 Template Engine, Bootstrap 5, Phosphor Icons, CSS3 Animation & Vanilla JS.
- **Testing & Quality Assurance:** pytest (185+ unit & integration test cases bao phủ toàn bộ module).

---

## 🧠 2. Các Quyết Định Kiến Trúc & Nghiệp Vụ Cốt Lõi

1. **Xóa mềm (Soft Delete):**
   - Bài học (`Lesson`) và Đề thi (`Exam`) sử dụng cờ `is_active=False` khi xóa để bảo toàn dữ liệu tiến độ học tập và lịch sử làm bài của học viên.
2. **Toàn vẹn dữ liệu từ vựng (Integrity Guard):**
   - Từ vựng đã có liên kết tiến độ học (`VocabularyProgress` / Flashcard SRS) được bảo vệ toàn vẹn tham chiếu, hệ thống chặn xóa cứng từ vựng đã có học viên học.
3. **Bảo mật và phân quyền (RBAC):**
   - Sử dụng mô hình Role-Based Access Control (RBAC) chặt chẽ giữa `USER` và `ADMIN`.
   - Mỗi người dùng chỉ có quyền truy cập vào phiên làm bài, lịch sử quiz và dữ liệu cá nhân của chính mình (`current_user.id`).
   - Rào chắn bảo vệ Quản trị viên (Admin Self-Lock Protection): Admin không thể tự khóa tài khoản hoặc tự hạ quyền của chính mình.
4. **Thuật toán Spaced Repetition System (SRS):**
   - Tự động điều chỉnh khoảng cách ngày ôn tập (`interval`) và cấp độ ghi nhớ (`srs_level` 1-7) dựa trên tự đánh giá của người học (Dễ, Tốt, Khó, Quên).
   - Hỗ trợ 3 thuật toán: Tiêu chuẩn (Standard), Tăng tốc (Aggressive), Nhẹ nhàng (Conservative).
5. **Quy tắc Chuỗi học tập (Gamification & Streak Rules):**
   - Chuỗi ngày streak tính theo ngày lịch (calendar date). Chỉ tăng tối đa 1 lần mỗi ngày khi hoàn thành ít nhất 1 hoạt động học tập hợp lệ.
   - Quá 1 ngày không học sẽ tự động reset chuỗi về 0 nhưng vẫn lưu kỷ lục chuỗi dài nhất (`longest_streak`).

---

## 🧪 3. Danh Mục Kịch Bản Kiểm Thử (QA Checklist)

1. **Xác thực (Auth):** Đăng ký tài khoản, đăng nhập thường, đăng nhập Google/Facebook, quên mật khẩu, kích hoạt OTP email, quản lý phiên và thiết bị.
2. **Dashboard & Tiến độ:** Kiểm tra bản đồ nhiệt (Activity Heatmap), biểu đồ tăng trưởng, thanh tiến độ level và danh sách ôn tập đến hạn.
3. **Học tập (Learning):** Mở bài học, đánh dấu yêu thích/bookmark, ghi chú cá nhân, lật thẻ flashcard 3D, luyện mini game ghép từ / gõ phím.
4. **Luyện thi (Exams & Quiz):** Làm bài trắc nghiệm tính giờ, tự động nộp bài khi hết giờ, xem giải thích chi tiết từng câu, chấm điểm AI bài luận.
5. **Quản trị (Admin):** Thống kê hệ thống, quản lý người dùng, tạo bài học/từ vựng/đề thi, nhập dữ liệu hàng loạt qua file CSV/Excel 2 bước, nhật ký Audit Log.
