# DANH SÁCH TÍNH NĂNG CỐT LÕI (CORE FEATURES) - WEB-ENGLISH LEARNING SYSTEM
================================================================================
Tài liệu danh mục các chức năng cần thiết để hệ thống web học tiếng Anh vận hành ổn định, đầy đủ và đáp ứng nhu cầu học tập thực tế.
Ghi chú:
- [x] : Tính năng ĐÃ ĐƯỢC XÂY DỰNG & HOÀN THIỆN trong mã nguồn.
- [ ] : Tính năng CẦN THIẾT NÂNG CẤP THÊM trong các phiên bản tiếp theo.
================================================================================

1. AUTHENTICATION & USER MANAGEMENT (XÁC THỰC & QUẢN LÝ NGƯỜI DÙNG)
================================================================================

1.1. Registration & Login (Đăng ký & Đăng nhập)
[x] - User Registration with email validation - Đăng ký người dùng mới với xác thực định dạng email và kiểm tra trùng lặp.
[x] - Password Strength Indicator - Thanh hiển thị độ mạnh mật khẩu theo thời gian thực (Độ dài, chữ hoa, số, ký tự đặc biệt).
[x] - Terms & Conditions Checkbox - Checkbox bắt buộc đồng ý với điều khoản sử dụng & chính sách bảo mật kèm Modal xem trực tiếp.
[x] - User Login with Session Management - Đăng nhập tài khoản với quản lý phiên Flask-Login và bảo vệ an toàn.
[x] - Remember Me Functionality - Ghi nhớ đăng nhập dài hạn qua Secure HttpOnly Cookies.
[x] - Login Attempt Limiting & Lockout - Giới hạn 5 lần đăng nhập sai và tự động khóa tạm thời 15 phút chống dò mật khẩu.
[x] - Show/Hide Password Eye Toggle - Nút icon con mắt (👁️) hiển thị/ẩn mật khẩu trên tất cả các form nhập.
[x] - Social Login Integration (Simulation) - Đăng nhập nhanh 1-click qua Google, Facebook, Apple, LinkedIn.
[x] - Magic Link Authentication - Đăng nhập không cần mật khẩu qua đường dẫn một lần gửi về email.

1.2. Security & Account Recovery (Bảo mật & Khôi phục tài khoản)
[x] - Two-Factor Authentication (2FA) - Bảo mật 2 yếu tố sử dụng ứng dụng Google Authenticator / TOTP.
[x] - 2FA Backup Codes Management - Cấp 10 mã dự phòng dùng 1 lần và hỗ trợ nút tải về tệp `.txt`.
[x] - Password Reset via Email - Quy trình khôi phục mật khẩu gửi mã Token xác thực qua email có thời hạn 1 giờ.
[x] - Email Verification System - Xác thực địa chỉ email tài khoản, hỗ trợ gửi lại email xác thực và thay đổi email mới.
[x] - Device Management - Quản lý các thiết bị/phiên đăng nhập active (IP, Browser, OS) và nút thu hồi đăng xuất từ xa.
[x] - Security Question Backup - Cài đặt câu hỏi bảo mật dự phòng và quy trình khôi phục tài khoản khi mất email.
[ ] - Biometric Authentication (WebAuthn / Fingerprint) - Xác thực sinh trắc học vân tay hoặc Face ID trên thiết bị di động.
[ ] - Enterprise Single Sign-On (SSO) - Đăng nhập một lần chuẩn SAML 2.0 / OpenID Connect cho tổ chức.

1.3. Role & Permission Management (Phân quyền & Vai trò)
[x] - Role-based Access Control (RBAC) - Phân quyền hệ thống theo các vai trò USER và ADMIN.
[x] - Admin Account Management - Danh sách người dùng, tìm kiếm, lọc trạng thái, khóa/mở khóa tài khoản người dùng vi phạm.
[x] - Admin Self-Lock Protection - Logic rào chắn ngăn Admin đang đăng nhập tự khóa tài khoản của chính mình.
[ ] - Temporary Role Assignment - Cấp quyền vai trò tạm thời có thời hạn cho giảng viên / trợ giảng.

---

2. GRAMMAR & LESSONS (NGỮ PHÁP & BÀI HỌC KỸ NĂNG)
================================================================================

2.1. Lesson Catalog & Filtering (Danh mục & Bộ lọc bài học)
[x] - Lesson Catalog View - Hiển thị danh sách bài học dạng thẻ (Card UI) trực quan với tiêu đề, mô tả, nhãn level và kỹ năng.
[x] - Multi-Filter by Level & Skill - Lọc nhanh bài học theo trình độ (A1, A2, B1, B2) và kỹ năng (Ngữ pháp, Đọc, Nghe, Từ vựng).
[x] - Real-time Lesson Search - Ô tìm kiếm bài học theo từ khóa thời gian thực.
[x] - Empty & Loading States - Giao diện Skeleton Loading khi nạp dữ liệu và màn hình thông báo khi kết quả tìm kiếm trống.

2.2. Interactive Lesson Viewer (Giao diện bài học tương tác)
[x] - Rich Structured Content Display - Hiển thị nội dung bài học Rich Text/Markdown bao gồm lý thuyết, bảng cấu trúc và ghi chú.
[x] - Interactive Example Accordion - Các ví dụ câu minh họa hỗ trợ ẩn/hiện dịch nghĩa tiếng Việt và phát âm thanh mẫu.
[x] - Embedded Audio Player - Trình phát âm thanh tích hợp cho bài đọc/nghe (Play/Pause, tua 5s, chỉnh tốc độ đọc).
[ ] - End-of-Lesson Checkpoint Quiz - Bài tập trắc nghiệm ngắn 3 câu cuối mỗi bài học để tự kiểm tra kiến thức.

2.3. Lesson Progress Tracking (Theo dõi tiến độ bài học)
[x] - Mark Lesson Complete - Nút ghi nhận hoàn thành bài học lưu vào cơ sở dữ liệu `LessonProgress`.
[x] - Lesson Completion Status Indicator - Biểu tượng dấu tích xanh và nhãn "Đã học" rõ ràng trên các bài đã hoàn tất.
[x] - Daily Activity Auto-Record - Tự động ghi nhận hoạt động hoàn thành bài học vào tiến độ ngày và tích lũy Streak.

---

3. VOCABULARY & FLASHCARDS (TỪ VỰNG & THẺ HỌC THÔNG MINH)
================================================================================

3.1. Vocabulary Hub (Kho từ vựng & Tra cứu)
[x] - Vocabulary Search & Multi-Filter - Tra cứu từ vựng theo từ gốc, phiên âm IPA, nghĩa tiếng Việt, trình độ A1-B2 và chủ đề.
[x] - Audio Pronunciation Player - Bấm nút loa phát âm thanh chuẩn Anh-Anh (UK) và Anh-Mỹ (US).
[x] - Vocabulary Learned Status Toggle - Đánh dấu trạng thái "Đã thuộc" hoặc "Cần ôn tập" trực tiếp từ danh sách.

3.2. Interactive Flashcard Player (Thẻ học Flashcard 3D)
[x] - 3D Card Flip Animation - Hiệu ứng lật thẻ 3D mượt mà giữa mặt từ vựng (IPA, từ loại, audio) và mặt sau (nghĩa, ví dụ, ảnh).
[x] - Self-Assessment Feedback - Nút tự đánh giá "Chưa nhớ" hoặc "Biết rồi" để cập nhật số lượt ôn `review_count` và `is_known`.
[x] - Flashcard Session Summary - Màn hình tổng kết lượt ôn tập hiển thị số từ đã thuộc, số từ cần ôn và tỷ lệ chính xác.

3.3. Custom User Flashcard Sets (Bộ từ vựng cá nhân)
[x] - Create Personal Flashcard Set - Tạo bộ thẻ từ vựng riêng với Tiêu đề, Mô tả và lựa chọn Công khai / Riêng tư.
[x] - Manage Flashcard Items - Thêm, sửa, xóa, sắp xếp thứ tự các thẻ từ (Thuật ngữ, Định nghĩa, Đường dẫn ảnh minh họa).
[ ] - Spaced Repetition System (SRS) Algorithm - Thuật toán tự động tính khoảng thời gian nhắc lại từ vựng (1, 3, 7, 30 ngày).
[ ] - Daily Due Words Widget - Bảng thông báo tổng hợp danh sách từ vựng đến hạn cần ôn tập trong ngày trên Dashboard.

---

4. EXAM & PRACTICE SYSTEM (HỆ THỐNG LUYỆN ĐỀ & THI THỬ)
================================================================================

4.1. Exam Bank & Discovery (Ngân hàng đề thi & Bộ lọc)
[x] - Exam Catalog & Categorization - Phân loại đề thi theo loại kỳ thi: TOEIC Full Test (200 câu), TOEIC Part 5/6/7, IELTS Reading, THPT QG.
[x] - Exam Summary Info Card - Hiển thị số lượng câu hỏi, thời gian làm bài quy định, số lượt làm và điểm số cao nhất cá nhân.
[x] - Exam Search & Filter - Tìm kiếm đề thi theo tên và sắp xếp theo đề thi mới nhất hoặc đề chưa làm.

4.2. Online Test Room (Phòng thi trực tuyến)
[x] - Real-time Countdown Timer - Đồng hồ đếm ngược thời gian thực, đổi màu cảnh báo đỏ và tự động nộp bài khi hết giờ.
[x] - Interactive Question Palette Grid - Bảng ma trận điều khiển 200 câu hỏi, đổi màu câu đã làm/chưa làm và nhảy nhanh đến câu bất kỳ.
[x] - Passage Split Screen Reader - Giao diện chia đôi màn hình cho bài đọc (Part 6/7) hoặc bài nghe (Part 1-4).
[x] - Flag Question for Review - Đánh dấu cờ câu hỏi chưa chắc chắn để xem lại trước khi nộp bài.
[x] - Exam Audio Player with Part Jump - Trình nghe âm thanh đề thi phân đoạn theo từng Part và câu hỏi.

4.3. Grading & Result Analysis (Chấm điểm & Báo cáo kết quả)
[x] - Instant Auto-Grading - Chấm điểm trắc nghiệm tự động ngay lập tức khi bấm Nộp bài.
[x] - Exam Result Summary Dashboard - Màn hình báo cáo kết quả chi tiết: Tổng điểm, tỷ lệ %, thời gian làm bài, số câu đúng/sai/bỏ qua.
[x] - Detailed Answer Key & Explanations - Xem lại toàn bộ bài làm, hiển thị đáp án chọn (Đúng/Sai), đáp án đúng và lời giải chi tiết.
[x] - Audio Transcript Viewer with Timestamps - Bật/tắt Script đoạn hội thoại nghe kèm mốc thời gian (Timestamp) âm thanh.

4.4. Section Practice Mode (Luyện tập theo Part / Câu hỏi)
[x] - Part-by-Part Practice Mode - Luyện tập tách biệt từng Part (VD: 30 câu TOEIC Part 5) không bị tính thời gian thi thật.
[x] - Custom Topic & Level Quiz Generator - Khởi tạo bài thi trắc nghiệm ngắn 10-20 câu ngẫu nhiên theo cấp độ và chủ đề chọn trước.

---

5. GAMIFICATION & ENGAGEMENT (GAME HỌC TẬP & GAMIFICATION)
================================================================================

5.1. Mini Game Arcade Lobby (Sảnh Game học tập)
[x] - Game Lobby Hub - Sảnh tổng hợp các trò chơi tiếng Anh với giao diện hiện đại và lựa chọn mức độ khó.
[x] - Game Session History Tracking - Lưu lịch sử lượt chơi game (`GameSession`): loại game, số câu đúng, độ chính xác (%), thời gian.

5.2. Multi-Game Modes (Chế độ chơi đa dạng)
[x] - Matching Game - Trò chơi ghép cặp từ tiếng Anh và nghĩa tiếng Việt với tính điểm thưởng Combo Multiplier.
[x] - Typing Game - Trò chơi gõ từ nhanh theo âm thanh phát âm hoặc nghĩa tiếng Việt trong thời gian đếm ngược.
[x] - Listening Rush Game - Trò chơi phản xạ nghe ngắn và chọn đáp án đúng trước khi hết thời gian.

5.3. Daily Streak & Goals (Chuỗi học tập & Mục tiêu ngày)
[x] - Daily Streak Counter - Bộ đếm chuỗi ngày học liên tục (`current_streak`) và chuỗi kỷ lục dài nhất (`longest_streak`).
[x] - Streak Auto-Reset Rule - Tự động reset Streak về 0 nếu quá 1 ngày không hoàn thành bài học/hoạt động nào.
[x] - Daily Goal Progress Bar - Thanh tiến độ hoàn thành mục tiêu bài học/câu hỏi hàng ngày cập nhật thời gian thực.
[ ] - Weekly / Monthly Leaderboard - Bảng xếp hạng thành tích người dùng theo điểm kinh nghiệm (XP) theo Tuần/Tháng.
[ ] - Achievement Badges System - Hệ thống mở khóa huy hiệu thưởng khi đạt mốc thành tích học tập.

---

6. AI-POWERED EVALUATION (CHẤM ĐIỂM & TRỢ LÝ AI)
================================================================================

6.1. AI Writing Evaluator (AI Chấm điểm bài viết luận)
[x] - Async Background AI Grading Queue - Đẩy bài thi tự luận (Essay) vào luồng xử lý ngầm (`async_grade_submission`) không gây treo UI.
[x] - AI Multi-Criteria Scoring - AI phân tích và chấm điểm bài viết dựa trên Ngữ pháp, Từ vựng, Cấu trúc và Độ mạch lạc.
[x] - AI Detailed Feedback & Suggestion - AI tự động sinh nhận xét chi tiết, chỉ ra lỗi sai và cung cấp phiên bản sửa chuẩn.
[x] - Async Submission Status Update - Tự động chuyển trạng thái bài làm từ `PENDING` sang `COMPLETED` khi AI chấm xong.
[ ] - AI Speech-to-Text & Pronunciation Rating - AI phân tích phát âm, ngữ điệu và độ trôi chảy từ file thu âm bài nói.
[ ] - AI Adaptive Weakness Analyzer - AI phân tích câu sai trong các đề thi để chỉ ra lỗ hổng kiến thức và đề xuất bài học khắc phục.

---

7. ANALYTICS & PROGRESS DASHBOARD (THỐNG KÊ & TIẾN ĐỘ HỌC TẬP)
================================================================================

7.1. Personal Dashboard (Bảng điều khiển cá nhân)
[x] - Core Metrics Cards - Hiển thị 4 thẻ thống kê: Tổng bài học đã học, Tổng từ vựng đã thuộc, Điểm thi trung bình, Chuỗi Streak.
[x] - Recommended Next Lessons Widget - Đề xuất bài học tiếp theo dựa trên trình độ cá nhân và các bài chưa học.
[x] - Recent Activity Timeline Stream - Dòng thời gian hiển thị các hoạt động học tập vừa thực hiện gần đây.
[x] - Exam & Quiz Attempt History - Bảng tổng hợp lịch sử các lần làm bài thi/quiz kèm liên kết xem lại chi tiết.
[ ] - Score Progress Trend Chart - Biểu đồ trực quan hóa xu hướng điểm số bài thi theo thời gian.
[ ] - Skill Competency Breakdown Radar Chart - Biểu đồ đa giác phân tích tỷ lệ thành thạo 4 kỹ năng.

---

8. SYSTEM ADMINISTRATION - ADMIN PANEL (QUẢN TRỊ HỆ THỐNG)
================================================================================

8.1. Admin Overview Dashboard (Tổng quan quản trị)
[x] - Admin System Overview Metrics - Thống kê tổng số người dùng, số bài học active, tổng từ vựng, số lượt nộp bài thi.
[x] - Admin Quick Navigation - Thanh điều hướng nhanh đến các khu vực quản lý CMS và người dùng.

8.2. CMS & Content Management (Quản lý nội dung)
[x] - Lesson CRUD & Soft Delete - Thêm, sửa nội dung bài học Rich Text. Thao tác xóa sử dụng Xóa mềm (`is_active=False`) bảo toàn dữ liệu.
[x] - Vocabulary Management & Integrity Guard - Thêm, sửa từ vựng. Hệ thống chặn xóa cứng từ vựng đã có lịch sử học của user.
[x] - Question Bank Management - Quản lý ngân hàng câu hỏi trắc nghiệm: Nội dung câu hỏi, 4 đáp án A-B-C-D, đáp án đúng, lời giải.
[x] - Exam Builder & Media Manager - Soạn thảo đề thi, gắn câu hỏi, tải lên tệp âm thanh MP3 bài nghe hoặc ảnh đoạn văn Reading.

8.3. Audit & System Protection (Nhật ký & Bảo vệ hệ thống)
[x] - Custom Exception Error Pages - Trang báo lỗi 403 Forbidden (Không có quyền) và 404 Not Found (Không tìm thấy trang) thiết kế riêng.
[x] - Flash Toast Notification Engine - Phát thông báo phản hồi thao tác (Thành công, Lỗi, Cảnh báo) cho người dùng và Admin.

================================================================================
TỔNG KẾT HỆ THỐNG CỐT LÕI:
- Tổng số Module chính: 8
- Tổng số tính năng đã hoàn thành [x]: 63 tính năng cốt lõi
- Tổng số tính năng chưa hoàn thành [ ]: 14 tính năng mở rộng
================================================================================
