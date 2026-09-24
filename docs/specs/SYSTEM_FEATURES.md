# 📋 ĐẶC TẢ TÍNH NĂNG TOÀN DIỆN & NÚT TƯƠNG TÁC — ENGLISHMATE SYSTEM
================================================================================
Tài liệu danh mục toàn diện các tính năng hệ thống từ cốt lõi, nâng cao đến lộ trình mở rộng tương lai (Bao gồm chi tiết tương tác giao diện và các nút bấm).
Ghi chú trạng thái:
- [x] : Tính năng ĐÃ ĐƯỢC XÂY DỰNG & HOÀN THIỆN trong hệ thống hiện tại.
- [ ] : Tính năng MỞ RỘNG / NÂNG CẤP TƯƠNG LAI trong lộ trình phát triển.
================================================================================

## 1. AUTHENTICATION & USER MANAGEMENT (XÁC THỰC & QUẢN LÝ NGƯỜI DÙNG)
================================================================================

### 1.1. Registration & Authentication (Đăng ký & Xác thực)
- [x] **User Registration with email validation**: Đăng ký người dùng mới với xác thực định dạng email, username duy nhất và kiểm tra trùng lặp.
- [x] **Password Strength Indicator**: Hiển thị độ mạnh của mật khẩu theo thời gian thực (Độ dài, chữ hoa, chữ số, ký tự đặc biệt).
- [x] **Terms & Conditions Checkbox**: Checkbox bắt buộc đồng ý với điều khoản sử dụng & chính sách bảo mật kèm Modal xem trực tiếp.
- [x] **User Login with Session Management**: Đăng nhập với quản lý phiên an toàn sử dụng Flask-Login.
- [x] **Remember Me Functionality**: Ghi nhớ đăng nhập dài hạn qua Secure HttpOnly Cookies.
- [x] **Login Attempt Limiting & Lockout**: Giới hạn 5 lần đăng nhập sai và tự động khóa tạm thời 15 phút chống dò mật khẩu.
- [x] **Show/Hide Password Eye Toggle**: Nút icon con mắt (👁️) hiển thị/ẩn mật khẩu trên các ô nhập liệu.
- [x] **Social Login Integration (Google, Facebook)**: Đăng nhập nhanh 1-click qua Google OAuth 2.0 và Facebook Graph API (kèm chế độ demo fallback).
- [x] **Email Verification System (OTP 6 digits)**: Gửi mã OTP xác thực email có thời hạn 15 phút, hỗ trợ gửi lại mã và log Dev Terminal.
- [x] **Password Reset via Email**: Khôi phục mật khẩu gửi mã Token xác thực qua email có thời hạn 1 giờ.
- [x] **Session Timeout & Inactivity Auto-logout**: Tự động đăng xuất sau 30 phút không hoạt động, Modal cảnh báo trước 5 phút.
- [x] **Multi-device Session Management**: Quản lý các thiết bị/phiên active (IP, Browser, OS) và nút thu hồi đăng xuất từ xa hoặc đăng xuất tất cả.
- [ ] **Two-Factor Authentication (2FA)**: Bảo mật 2 yếu tố sử dụng ứng dụng Google Authenticator / TOTP.
- [ ] **Biometric Authentication**: Hỗ trợ đăng nhập sinh trắc học vân tay hoặc Face ID trên thiết bị di động.
- [ ] **Single Sign-On (SSO)**: Đăng nhập một lần chuẩn SAML 2.0 / OpenID Connect cho trường học, tổ chức.

#### Các nút tương tác chi tiết:
- `[Login Button]`: Nút đăng nhập chính với trạng thái loading và validation.
- `[Register Button]`: Nút đăng ký tài khoản mới.
- `[Social Login Buttons]`: Nút đăng nhập Google & Facebook.
- `[Forgot Password Link]`: Link chuyển hướng đến trang khôi phục mật khẩu.
- `[Reset Password Button]`: Nút đặt lại mật khẩu mới.
- `[Resend OTP Button]`: Nút gửi lại mã xác nhận email.
- `[Revoke Session Button]`: Nút hủy phiên đăng nhập từ xa.

### 1.2. Profile & Account Settings (Hồ sơ & Cài đặt)
- [x] **View & Edit Profile Information**: Xem và chỉnh sửa họ tên hiển thị cá nhân.
- [x] **Avatar Upload & Management**: Tải lên và đổi ảnh đại diện (JPG, PNG, WEBP), tạo tên file uuid an toàn và avatar chữ cái mặc định.
- [x] **Change Email with Verification**: Thay đổi email bảo mật 2 bước qua mã xác thực OTP gửi về email mới.
- [x] **Password Change**: Đổi mật khẩu với xác thực mật khẩu cũ và kiểm tra độ mạnh mật khẩu mới.
- [x] **Account Deactivation**: Vô hiệu hóa tài khoản tạm thời (`is_active=False`) và tự động đăng xuất.
- [x] **Account Deletion**: Xóa tài khoản vĩnh viễn với xác nhận mật khẩu (kèm cơ chế Admin Self-Lock Protection chặn Admin tự xóa chính mình).
- [ ] **Learning Goal Preferences**: Tùy chỉnh mục tiêu học tập daily và lịch nhắc nhở cá nhân.
- [ ] **Theme Preference Settings**: Chuyển đổi giao diện Sáng (Light) / Tối (Dark).

---

## 2. PERSONAL DASHBOARD & ANALYTICS (BẢNG ĐIỀU KHIỂN & PHÂN TÍCH TIẾN ĐỘ)
================================================================================

### 2.1. Personal Dashboard (Bảng điều khiển cá nhân)
- [x] **Core Metrics Cards**: 4 thẻ chỉ số: Bài học hoàn thành, Từ vựng đã thuộc, Điểm thi trung bình, Chuỗi Streak.
- [x] **Weekly Learning Calendar**: Lịch học 7 ngày trong tuần (T2 - CN) hiển thị trạng thái hoàn thành bài học.
- [x] **Skill Competency Breakdown**: Phân tích tiến độ và mức độ cân bằng 4 kỹ năng: Từ vựng, Ngữ pháp, Đọc hiểu, Nghe hiểu.
- [x] **Level & Progression**: Hệ thống 9 cấp bậc người học (Tân thủ -> Thần đồng), thanh tiến độ kinh nghiệm XP và dự báo ngày thăng cấp.
- [x] **Time Spent Learning**: Thống kê thời gian học hôm nay, tuần này và tổng thời gian tích lũy.
- [x] **Calendar Activity Heatmap**: Bản đồ nhiệt hoạt động 365 ngày cả năm kiểu GitHub với bộ chọn năm (2026, 2025, 2024) và 5 cấp độ màu sắc.
- [x] **Performance Trends Chart**: Biểu đồ đường thể hiện điểm số (%) của 7 bài kiểm tra gần nhất theo thời gian.
- [x] **Today's Schedule Widget**: Đề xuất bài học tiếp theo, thẻ từ vựng SRS đến hạn ôn, bài quiz gợi ý.
- [x] **Today's Achievements & Daily Reward**: Thống kê XP kiếm được hôm nay, chuỗi streak và nút nhận rương thưởng ngày.
- [x] **Daily Motivation Quote**: Trích dẫn danh ngôn tạo động lực song ngữ Anh - Việt thay đổi mỗi ngày.

---

## 3. LESSONS & 4 CORE SKILLS (BÀI HỌC & 4 KỸ NĂNG CỐT LÕI)
================================================================================

### 3.1. Lesson Catalog & Discovery (Danh mục bài học)
- [x] **Lesson Catalog by 4 Skills**: Phân loại bài học theo 4 kỹ năng: Listening, Reading, Speaking, Writing.
- [x] **Multi-Filter by Level & Skill**: Lọc bài học theo cấp độ chuẩn CEFR (A1 đến C2) và kỹ năng.
- [x] **Real-time Lesson Search**: Tìm kiếm bài học theo từ khóa thời gian thực.
- [x] **Lesson Quick Preview**: Modal xem trước nhanh thông tin bài học mà không cần chuyển trang.
- [x] **Status Badges**: Chỉ báo trạng thái "Đã học" (tích xanh) hoặc "Chưa học".

### 3.2. Interactive Lesson Viewer (Giao diện bài học tương tác)
- [x] **Rich Structured Content View**: Nội dung bài học Rich-Text/Markdown với bảng biểu và khối chú ý.
- [x] **Embedded Audio Player**: Trình nghe âm thanh cho bài học Nghe (Play/Pause, tua 5s, điều chỉnh tốc độ).
- [x] **Interactive Example Accordion**: Ví dụ câu minh họa hỗ trợ ẩn/hiện dịch nghĩa tiếng Việt và phát âm thanh.
- [x] **Vocabulary Tooltips**: Bấm vào từ vựng nổi bật để xem nhanh nghĩa và phiên âm.
- [x] **Lesson Favorite**: Đánh dấu bài học yêu thích với AJAX.
- [x] **Personal Notes**: Viết và lưu trữ ghi chú riêng cho từng bài học.
- [x] **Lesson Bookmarking**: Đánh dấu vị trí phần đang học dở.
- [x] **Content Report**: Báo cáo nội dung bài học sai sót gửi Admin.
- [x] **Mark Lesson Complete & Streak Activation**: Ghi nhận hoàn thành bài học, cộng +20 XP, kích hoạt chuỗi Streak và modal pháo hoa chúc mừng.

---

## 4. VOCABULARY & SPACED REPETITION (TỪ VỰNG & FLASHCARD SRS)
================================================================================

### 4.1. Vocabulary Hub & Dictionary (Kho từ vựng & Tra cứu)
- [x] **Vocabulary Catalog**: Kho 1,200+ từ vựng từ A1 đến C2 kèm IPA, audio chuẩn US/UK, nghĩa tiếng Việt, câu ví dụ song ngữ, collocations, từ đồng nghĩa/trái nghĩa.
- [x] **Courses by Category/Subcategory**: Phân chia từ vựng theo giáo trình (CEFR, Oxford, TOEIC...) và chia nhỏ theo Unit có nút reset unit.
- [x] **Daily Vocabulary Goal**: Thiết lập mục tiêu từ vựng hàng ngày (10 - 50 từ/ngày) với thanh tiến độ.
- [x] **Vocabulary Actions**: Đánh dấu đã học, chuyển đổi trạng thái đã thuộc, yêu thích, bỏ qua (skip), báo cáo từ vựng.

### 4.2. Interactive 3D Flashcard & SRS Algorithm (Thẻ Flashcard 3D & SRS)
- [x] **3D Card Flip Animation**: Hiệu ứng lật thẻ 3D mượt mà giữa mặt trước (từ vựng, IPA, audio) và mặt sau (nghĩa, ví dụ, collocations, ảnh).
- [x] **Self-Assessment Rating**: 4 mức đánh giá: Dễ (Easy), Tốt (Good), Khó (Hard), Quên/Chưa thuộc (Incorrect).
- [x] **SRS Interval Engine**: Hỗ trợ 3 thuật toán lặp lại ngắt quãng (Tiêu chuẩn, Tăng tốc, Nhẹ nhàng). Tự động thăng cấp lên Mastered khi đạt SRS Level 7.
- [x] **Review Session Summary**: Màn hình tổng kết phiên ôn tập hiển thị số từ thành thạo và số từ cần ôn thêm.

### 4.3. Vocabulary Management & Statistics (Quản lý & Thống kê từ vựng)
- [x] **Vocabulary Management**: Tìm kiếm, lọc theo trạng thái (Mới, Đang học, Cần ôn, Thành thạo), cấp SRS (1-7), trình độ, sắp xếp, ghi chú cá nhân, ví dụ riêng, reset tiến độ, xóa, thao tác hàng loạt.
- [x] **Vocabulary Statistics**: Thống kê tỷ lệ nhớ từ, biểu đồ phân bổ mức SRS 1-7, phân tích chủ đề thành thạo/yếu, dòng thời gian từ đã thuộc, biểu đồ tăng trưởng từ vựng ngày/tuần/tháng.
- [x] **Vocabulary Settings**: Cài đặt giọng đọc US/UK, tự động phát âm, thời gian ôn ưu tiên, chế độ hiển thị thẻ/danh sách.
- [x] **Custom User Flashcard Sets**: Tự tạo và quản lý bộ thẻ từ vựng riêng (thêm, sửa, xóa thẻ, học và đồng bộ tiến độ).

---

## 5. GRAMMAR SYSTEM & REFERENCE (HỆ THỐNG NGỮ PHÁP & SỔ TAY TRA CỨU)
================================================================================

### 5.1. 12 Major Grammar Categories (12 Đại danh mục ngữ pháp)
- [x] **12 Categories Catalog**: Từ loại, Cấu trúc câu, 12 Thì, Động từ, Danh từ & Mạo từ, Đại từ & Từ hạn định, Tính từ & Trạng từ, Giới từ, Câu bị động, Mệnh đề & Liên từ, Cấu trúc nâng cao, Cấu trúc đặc biệt & Ngữ pháp ứng dụng.
- [x] **TOEIC Target Weighting**: Phân loại các chủ đề ngữ pháp trọng tâm theo Part 5 & 6 đề thi TOEIC.
- [x] **Dual View Mode**: Chế độ xem dạng lưới 12 danh mục lớn hoặc danh sách các chủ đề con.
- [x] **Grammar Detail Viewer**: Lý thuyết, cấu trúc, bảng quy tắc, ví dụ song ngữ, mục "Lỗi sai thường gặp", mục "Mẹo làm bài nhanh", chủ đề liên quan, bài tập trắc nghiệm cuối bài.
- [x] **Complete & Favorite**: Đánh dấu hoàn thành và thêm vào yêu thích với AJAX.

### 5.2. Grammar Exercises & Error Log (Bài tập ngữ pháp & Sổ lỗi)
- [x] **Practice Setup**: Chọn chủ đề, độ khó (Easy, Medium, Hard), số lượng câu hỏi (5 - 20 câu).
- [x] **Exercise Room**: Đồng hồ đếm giờ, chuyển đổi câu hỏi nhanh, đổi màu câu đã làm.
- [x] **Scoring & Error Log**: Tự động chấm điểm, lưu các câu sai vào Sổ nhật ký lỗi (`GrammarErrorLog`), xem giải thích chi tiết từng câu.
- [x] **Retry Incorrect Questions**: Chế độ thử lại riêng các câu vừa làm sai để khắc phục lỗ hổng kiến thức.

### 5.3. Grammar Quick Reference & Print Mode (Sổ tay tra cứu & In ấn)
- [x] **Rules Quick Reference**: Bảng tra cứu tóm tắt các quy tắc chính tả, trật tự từ OSASCOMP, động từ bất quy tắc...
- [x] **Search & Bookmark**: Tìm kiếm quy tắc, Bookmark quy tắc để tra cứu nhanh.
- [x] **Print-friendly View**: Chế độ xem tối ưu hóa để in ấn hoặc lưu PDF tài liệu học tập.

---

## 6. QUIZZES SYSTEM (HỆ THỐNG BÀI KIỂM TRA TRẮC NGHIỆM)
================================================================================

- [x] **Quiz Dashboard**: 5 chỉ số hiệu suất, phân tích theo danh mục, cảnh báo kỹ năng yếu (<60%), lịch sử 10 bài gần nhất.
- [x] **Quiz Catalog & Browse**: Lọc theo cấp độ, kỹ năng, độ khó, trạng thái; sắp xếp theo độ phổ biến hoặc mới nhất; xem trước nhanh AJAX Modal.
- [x] **Online Quiz Taking Room**: Đồng hồ đếm ngược, ma trận điều hướng câu hỏi, cờ đánh dấu xem lại (Flag for review), lưu đáp án tự động qua AJAX, tạm dừng/tiếp tục bài thi, tự động nộp khi hết giờ.
- [x] **Quiz Results**: Bảng điểm, xếp loại (Xuất sắc/Giỏi/Khá/Cần cố gắng), xem lại đáp án và giải thích chi tiết, tự động lưu câu sai vào sổ lỗi, xuất báo cáo ra file PDF.

---

## 7. EXAMS & AI EVALUATION (HỆ THỐNG LUYỆN THI & CHẤM ĐIỂM AI)
================================================================================

- [x] **TOEIC Full Test Simulation**: Đề thi format chuẩn (Part 5, 6, 7), giao diện chia đôi màn hình cho đoạn văn dài và chùm câu hỏi, đồng hồ đếm ngược 120 phút, tự động chấm điểm và giải thích chi tiết.
- [x] **Comprehensive Exam Bank**: Ngân hàng đề thi đa dạng (TOEIC, IELTS, THPT QG, Placement Test, Progress Assessment, Timed Practice).
- [x] **Rich Question Types**: Trắc nghiệm một đáp án, điền từ vào chỗ trống, viết bài luận tự luận, thu âm bài nói.
- [x] **AI Essay Auto-Grading**: Luồng xử lý ngầm (Background Thread) chấm điểm bài viết tự luận theo 4 tiêu chí (Ngữ pháp, Từ vựng, Tính mạch lạc, Cấu trúc), sinh nhận xét và bài sửa chuẩn.
- [x] **Specialized Exams & Timed Practice**: Đề thi phân lớp, kiểm tra định kỳ, luyện tập có bấm giờ.
- [x] **Unified Exam History & Compare**: Lịch sử làm bài hợp nhất, so sánh 2 lần thi (Compare attempts), xuất lịch sử thi ra file CSV, cài đặt phòng thi cá nhân.
- [ ] **AI Speech-to-Text & Pronunciation Rating**: AI phân tích phát âm, ngữ điệu từ file thu âm bài nói.
- [ ] **24/7 AI Tutor Chat Assistant**: Trợ lý gia sư AI trò chuyện hội thoại tiếng Anh tự nhiên.

---

## 8. GAMIFICATION & LEARNING GAMES (TRÒ CHƠI HÓA & SẢNH GAME)
================================================================================

- [x] **Daily Streak Engine**: Tính theo ngày lịch, kiểm tra gãy chuỗi, lưu kỷ lục chuỗi dài nhất, Modal pháo hoa chúc mừng.
- [x] **Experience Points & Leveling**: Hệ thống cộng điểm XP, 9 cấp bậc danh hiệu, tự động loại trừ Admin khỏi bảng xếp hạng.
- [x] **Student Leaderboards**: 3 Bảng xếp hạng học viên (Tuần, Chuỗi ngày, Mọi thời đại) với huy chương Vàng, Bạc, Đồng.
- [x] **Achievement Badges Engine**: Động cơ tự động mở khóa huy hiệu thành tích kèm thưởng XP.
- [x] **Learning Challenges**: Nhiệm vụ ngày và tuần, thanh tiến độ, nút nhận thưởng Claim XP.
- [x] **Daily Goal Reward**: Rương thưởng hoàn thành mục tiêu ngày (+50 XP).
- [x] **Arcade Game Lobby & 4 Mini Games**: Sảnh Game và 4 trò chơi: Trò chơi Ghép thẻ (Matching Game), Gõ phím nhanh (Typing Game), Phản xạ nghe (Listening Rush), Trắc nghiệm tốc độ (Speed Quiz); lưu lịch sử `GameSession`.

---

## 9. ADMIN PANEL & CMS (TRANG QUẢN TRỊ VIÊN & NHẬP LIỆU)
================================================================================

- [x] **Admin Dashboard & Notifications**: 4 chỉ số vận hành cốt lõi, chuông thông báo Header cảnh báo tài khoản bị khóa và lượt nộp bài.
- [x] **User Management**: Tìm kiếm, lọc, Khóa/Mở khóa tài khoản vi phạm, Đổi vai trò USER <-> ADMIN, Phân vai trò tạm thời có hạn, rào chắn Admin Self-Lock Protection.
- [x] **Role & Permission Management (RBAC CMS)**: Tạo vai trò tùy chỉnh, gán ma trận quyền hạn (Permissions), phân cấp vai trò cha - con.
- [x] **Lesson Management CMS**: Thêm/Sửa bài học Rich-Text/Markdown, xem trước nhanh dạng Modal, xóa mềm (Soft delete `is_active=False`).
- [x] **Vocabulary Management CMS**: Thêm/Sửa từ vựng, xóa từ vựng có cơ chế Rào chắn toàn vẹn dữ liệu (Integrity Guard chặn xóa nếu đã có học viên học).
- [x] **Exam Builder CMS**: Tạo đề ngẫu nhiên theo cấu hình phần hoặc thủ công, bật/tắt Publish qua AJAX, xem trước đề thi, báo cáo thống kê phổ điểm đề thi.
- [x] **2-Step Bulk Importer Engine**: Tải file mẫu chuẩn Excel/CSV, Bước 1 kiểm tra & xác thực (Validate & Preview), Bước 2 cam kết nạp dữ liệu (Commit Import) theo lô an toàn cho Vocabulary, Lessons, Exams.
- [x] **Admin Audit Logs & CSV Export**: Ghi nhận toàn bộ thao tác nhạy cảm của Admin kèm thời gian chuẩn giờ VN GMT+7, IP, chi tiết; bộ lọc tìm kiếm và Xuất nhật ký ra file CSV.
- [x] **Dev Tooling**: Endpoint tự động kiểm tra Live-reload templates/static, log mã OTP và link reset mật khẩu ra console.

---

## 10. ADVANCED ECOSYSTEM & FUTURE ROADMAP (LỘ TRÌNH NÂNG CẤP TƯƠNG LAI)
================================================================================
- [ ] **Virtual Classroom (VR / AR)**: Môi trường lớp học ảo luyện giao tiếp tiếng Anh tương tác.
- [ ] **Native Mobile Application**: Ứng dụng di động iOS/Android ưu tiên học ngoại tuyến (Offline-first).
- [ ] **Smart Watch App**: Xem nhanh thẻ từ vựng trên Apple Watch / Wear OS.
- [ ] **Car Audio Learning Mode**: Chế độ học nghe an toàn khi lái xe (CarPlay / Android Auto).
- [ ] **Developer Open API & Webhooks**: Cung cấp API mở RESTful/GraphQL cho bên thứ ba kết nối.
- [ ] **Automated AI Proctoring**: Giám thị thi trực tuyến bằng AI nhận diện khuôn mặt và màn hình.

================================================================================
TỔNG KẾT HỆ THỐNG:
- Tổng số Module phân loại: 10 Module lớn
- Tổng số tính năng đã hoàn thiện [x]: 110+ tính năng cốt lõi & nâng cao
- Tổng số tính năng mở rộng [ ]: 12 tính năng nâng cấp tương lai
================================================================================
