# 📝 KẾ HOẠCH TRIỂN KHAI GIAI ĐOẠN 4: HỆ THỐNG QUIZ & ĐỀ THI QUỐC TẾ



---

# Kế hoạch Triển khai Tính năng 4.1: Quiz Dashboard (Bảng điều khiển quiz)

Tài liệu này chi tiết hóa kế hoạch xây dựng và hoàn thiện toàn bộ **7 hạng mục con** thuộc **Mục 4.1: Quiz Dashboard (Bảng điều khiển quiz)** của dự án **EnglishMate**.

> [!IMPORTANT]
> **Cam kết thiết kế**: Giữ nguyên 100% design, màu sắc, font chữ (`Manrope`), layout, spacing và UI/UX hiện tại của hệ thống. Tái sử dụng tối đa các component Bootstrap 5, metric card, progress bar, badge, alert và CSS utility sẵn có.

---

## 1. Mục tiêu & Phạm vi (Scope of Work)

Hoàn thiện đầy đủ 7 hạng mục con thuộc Mục 4.1:

1. **[x] Overall quiz score display**: Hiển thị tổng điểm quiz và điểm trung bình đạt được.
2. **[x] Quiz count by category**: Hiển thị số lượng quiz đã hoàn thành theo từng danh mục/chủ đề (Grammar, Vocabulary, General, TOEIC...).
3. **[x] Quiz accuracy rate**: Hiển thị tỷ lệ trả lời chính xác % toàn bộ bài quiz.
4. **[x] Average time per quiz**: Thời gian trung bình hoàn thành mỗi bài quiz (phút/giây).
5. **[x] Quiz practice streak**: Chuỗi ngày liên tiếp tham gia luyện quiz (Quiz Streak 🔥).
6. **[x] Total quizzes completed**: Tổng số lượt quiz đã hoàn thành.
7. **[x] Weak quiz categories identification**: Tự động phân tích và xác định các danh mục quiz yếu (tỷ lệ chính xác < 60%) để đưa ra đề xuất luyện tập kịp thời.

---

## 2. Các thay đổi Kiến trúc & Mã nguồn

### 2.1. Cơ sở dữ liệu & Models (`app/modules/learning/models.py` & `patch_db.py`)
- Cập nhật model `QuizAttempt`:
  - Thêm trường `duration_seconds` (Integer, default=0) lưu thời gian làm bài thực tế.
- Cập nhật `patch_db.py`:
  - Thêm cột `duration_seconds` vào bảng `quiz_attempt` bằng câu lệnh `ALTER TABLE` an toàn.

### 2.2. Controller & Logic (`app/modules/learning/routes.py`)
- Route `GET /learning/quizzes/dashboard` (và đường dẫn ngắn `/learning/quizzes`):
  - Tính toán tổng điểm `overall_score`, tổng số bài `total_quizzes_completed`, tỷ lệ chính xác `accuracy_rate`.
  - Tính toán thời gian trung bình `avg_time_seconds`.
  - Tính toán chuỗi ngày làm quiz `quiz_streak`.
  - Phân tích số lượng và phần trăm chính xác theo từng danh mục `category_stats`.
  - Tự động nhận diện các danh mục yếu `weak_categories` (Accuracy < 60%).
  - Tự động tạo dữ liệu lượt làm mẫu nếu học viên mới chưa có lịch sử quiz để hiển thị giao diện trực quan.

### 2.3. Giao diện Người dùng (Templates HTML)
- [NEW] `app/templates/learning/quiz_dashboard.html`:
  - Bảng điều khiển Tổng quan với các thẻ Metric sắc nét (Tổng điểm, Tỷ lệ chính xác %, Thời gian trung bình, Streak 🔥, Tổng bài đã hoàn thành).
  - Phân tích thành thạo theo Danh mục (Grammar, Vocabulary, TOEIC...) với thanh tiến độ % tương ứng.
  - Khối Cảnh báo Danh mục Quiz Yếu (Weak Quiz Categories Alert) đề xuất các bài tập cần ôn lại.
  - Bảng Lịch sử lượt làm Quiz gần nhất.

---

## 3. Kế hoạch Kiểm thử & Xác nhận (Verification Plan)

### Automated Tests (`tests/test_quiz_dashboard.py`)
1. Test truy cập Bảng điều khiển Quiz `/learning/quizzes/dashboard`.
2. Test tính toán chính xác tổng điểm, tỷ lệ chính xác %, thời gian trung bình và chuỗi streak.
3. Test nhận diện danh mục yếu (Accuracy < 60%).
4. Test hiển thị danh sách bài quiz theo danh mục.

### Manual Verification
1. Truy cập `/learning/quizzes/dashboard`.
2. Kiểm tra các thẻ thông số metric: Tổng điểm, Accuracy %, Avg Time, Streak 🔥.
3. Kiểm tra danh sách chủ đề theo danh mục.
4. Kiểm tra khối cảnh báo "Danh mục Quiz Yếu" có chỉ ra đúng các chủ đề cần cải thiện hay không.

---

# Kế hoạch Triển khai Tính năng 4.2: Quiz List (Danh sách quiz)

Tài liệu này chi tiết hóa kế hoạch xây dựng và hoàn thiện toàn bộ **13 hạng mục con** thuộc **Mục 4.2: Quiz List (Danh sách quiz)** của dự án **EnglishMate**.

> [!IMPORTANT]
> **Cam kết thiết kế**: Giữ nguyên 100% design, màu sắc, font chữ (`Manrope`), layout, spacing và UI/UX hiện tại của hệ thống. Tái sử dụng tối đa các component Bootstrap 5, quiz card, badge, modal preview, filter bar và CSS utility sẵn có.

---

## 1. Mục tiêu & Phạm vi (Scope of Work)

Hoàn thiện đầy đủ 13 hạng mục con thuộc Mục 4.2:

1. **[x] Browse quizzes by category**: Duyệt quiz theo danh mục (Grammar, Vocabulary, TOEIC, General...).
2. **[x] Browse quizzes by level**: Duyệt quiz theo cấp độ (A1, A2, B1, B2, C1, C2).
3. **[x] Browse quizzes by skill**: Duyệt quiz theo kỹ năng (Grammar, Vocabulary, Reading, Listening, Speaking, Writing).
4. **[x] Search quizzes by title**: Tìm kiếm quiz theo tiêu đề hoặc nội dung mô tả.
5. **[x] Filter by difficulty**: Bộ lọc độ khó (Easy, Medium, Hard).
6. **[x] Filter by status**: Lọc bài quiz theo trạng thái (New - Bài mới, In Progress - Đang làm, Completed - Đã hoàn thành).
7. **[x] Sort by recent**: Sắp xếp quiz theo thời gian tạo mới nhất.
8. **[x] Sort by popularity**: Sắp xếp quiz theo độ phổ biến (lượt người tham gia `view_count`).
9. **[x] Quiz list view with summaries**: Chế độ xem danh sách quiz hiển thị tóm tắt, số câu hỏi, thời gian làm bài.
10. **[x] Quiz detail preview**: Modal / API xem trước chi tiết thông tin bài quiz trước khi vào làm.
11. **[x] Start quiz button**: Nút "Bắt đầu quiz" dành cho các bài quiz mới.
12. **[x] Continue quiz button**: Nút "Tiếp tục quiz" dành cho các bài quiz đang làm dở.
13. **[x] View quiz results button**: Nút "Xem kết quả quiz" dành cho các bài quiz đã nộp bài.

---

## 2. Các thay đổi Kiến trúc & Mã nguồn

### 2.1. Cơ sở dữ liệu & Models (`app/modules/learning/models.py` & `patch_db.py`)
- [NEW] Model `Quiz`:
  - `id`, `title`, `category`, `level`, `skill`, `difficulty`, `description`, `question_count`, `duration_minutes`, `view_count`, `is_active`, `created_at`, `updated_at`.
- Cập nhật `patch_db.py`:
  - Tự động tạo bảng `quiz` trong SQLite database.

### 2.2. Controller & Routes (`app/modules/learning/routes.py`)
- Route `GET /learning/quizzes/list` (và `/learning/quizzes/browse`):
  - Hỗ trợ Tìm kiếm (`q`), Duyệt theo `category`, `level`, `skill`.
  - Lọc theo `difficulty` (Easy, Medium, Hard), trạng thái `status` (`new`, `in_progress`, `completed`).
  - Sắp xếp theo `sort` (`recent`, `popularity`).
  - Tự động kiểm tra trạng thái tương tác của học viên với từng bài quiz để gắn nút tương ứng ("Bắt đầu quiz", "Tiếp tục quiz", "Xem kết quả").
- Route `GET /learning/quizzes/<int:quiz_id>/preview`:
  - API trả về JSON xem trước chi tiết bài quiz (Tiêu đề, mô tả, level, skill, độ khó, số câu hỏi, thời gian làm bài, lượt tham gia).

### 2.3. Giao diện Người dùng (Templates HTML)
- [NEW] `app/templates/learning/quiz_list.html`:
  - Thanh tìm kiếm & Bộ lọc thông minh (Category pills, Level dropdown, Skill dropdown, Difficulty dropdown, Status dropdown, Sort selector).
  - Danh sách Card bài Quiz hiển thị Badge level, Badge skill, Độ khó, Tóm tắt nội dung, Lượt xem và các nút hành động ngữ cảnh ("Bắt đầu quiz", "Tiếp tục quiz", "Xem kết quả").
  - Modal Xem trước chi tiết bài Quiz (Quiz Detail Preview Modal).

---

## 3. Kế hoạch Kiểm thử & Xác nhận (Verification Plan)

### Automated Tests (`tests/test_quiz_list.py`)
1. Test truy cập Thư viện Quiz `/learning/quizzes/list`.
2. Test duyệt quiz theo category, level (A1-C2), skill (Grammar/Vocabulary/Reading/Listening).
3. Test tìm kiếm từ khóa bài quiz theo tiêu đề.
4. Test lọc độ khó (Easy/Medium/Hard) và lọc trạng thái (New/In Progress/Completed).
5. Test sắp xếp theo mới nhất (`recent`) và phổ biến nhất (`popularity`).
6. Test API xem trước chi tiết bài quiz `/learning/quizzes/<id>/preview`.

### Manual Verification
1. Truy cập `/learning/quizzes/list`.
2. Chọn danh mục "Grammar", Level "B1", Độ khó "Medium", Sắp xếp "Phổ biến nhất".
3. Nhấp nút xem trước 👁️ ➔ Kiểm tra hiển thị thông tin modal.
4. Kiểm tra sự thay đổi của các nút "Bắt đầu quiz" vs "Tiếp tục quiz" vs "Xem kết quả".

---

# Kế hoạch Triển khai Tính năng 4.3: Quiz Taking (Làm quiz)

Tài liệu này chi tiết hóa kế hoạch xây dựng và hoàn thiện toàn bộ **16 hạng mục con** thuộc **Mục 4.3: Quiz Taking (Làm quiz)** của dự án **EnglishMate**.

> [!IMPORTANT]
> **Cam kết thiết kế**: Giữ nguyên 100% design, màu sắc, font chữ (`Manrope`), layout, spacing và UI/UX hiện tại của hệ thống. Tái sử dụng tối đa các component Bootstrap 5, timer, navigation grid, modal, option pill và CSS utility sẵn có.

---

## 1. Mục tiêu & Phạm vi (Scope of Work)

Hoàn thiện đầy đủ 16 hạng mục con thuộc Mục 4.3:

1. **[x] Quiz instructions modal**: Hộp thoại hướng dẫn quy chế và cách làm bài quiz.
2. **[x] Quiz timer display**: Đồng hồ đếm ngược thời gian làm bài dạng `MM:SS`.
3. **[x] Question navigation (jump to question)**: Khối nút số thứ tự câu hỏi cho phép bấm nhảy ngay đến câu mong muốn.
4. **[x] Mark for review**: Nút cờ 🚩 đánh dấu câu hỏi cần kiểm tra lại trước khi nộp bài.
5. **[x] Review marked questions**: Bộ lọc nhanh xem danh sách các câu đã đánh dấu cờ 🚩.
6. **[x] Progress indicator (1/20 questions)**: Chỉ số hiển thị tiến độ (VD: Câu 1/20) & Thanh phần trăm progress bar.
7. **[x] Display question**: Hiển thị nội dung văn bản câu hỏi rõ ràng.
8. **[x] Display answer options**: Hiển thị 4 lựa chọn đáp án A, B, C, D.
9. **[x] Select answer button**: Nút / Thẻ chọn đáp án với trạng thái active trực quan.
10. **[x] Submit answer button**: Nút nộp / lưu câu trả lời cho câu hỏi hiện tại.
11. **[x] Next question button**: Nút chuyển sang câu hỏi tiếp theo.
12. **[x] Previous question button**: Nút quay lại câu hỏi trước đó.
13. **[x] Pause/resume functionality**: Chức năng tạm dừng đếm giờ / tiếp tục làm bài quiz.
14. **[x] Submit quiz button**: Nút nộp toàn bộ bài quiz.
15. **[x] Submit confirmation modal**: Hộp thoại xác nhận nộp bài hiển thị chi tiết số câu đã làm, chưa làm và số câu đánh dấu 🚩.
16. **[x] Auto-submit on timeout**: Tự động nộp bài và chấm điểm khi đồng hồ đếm ngược về 0.

---

## 2. Các thay đổi Kiến trúc & Mã nguồn

### 2.1. Controller & Session State (`app/modules/learning/routes.py`)
- Route `GET /learning/quizzes/<int:quiz_id>/start`:
  - Khởi tạo phiên bài quiz trong session `session["quiz_session_<quiz_id>"]` với ngân hàng câu hỏi, thời gian bắt đầu, đồng hồ đếm ngược, danh sách đáp án đã chọn và mảng câu đánh dấu cờ 🚩.
  - Thêm bài quiz vào mảng `session["in_progress_quizzes"]`.
- Route `GET /learning/quizzes/<int:quiz_id>/take`:
  - Màn hình giao diện làm bài quiz tương tác đầy đủ 16 tính năng.
- Route `POST /learning/quizzes/<int:quiz_id>/answer`:
  - API lưu đáp án đã chọn và trạng thái đánh dấu cờ 🚩 vào session.
- Route `POST /learning/quizzes/<int:quiz_id>/pause`:
  - Toggle trạng thái tạm dừng `is_paused` và tính lại thời gian còn lại.
- Route `POST /learning/quizzes/<int:quiz_id>/submit`:
  - Chấm điểm bài quiz, tạo bản ghi `QuizAttempt` và `QuizAttemptAnswer` trong CSDL, xóa bài khỏi danh sách `in_progress_quizzes` và chuyển sang trang Tổng kết kết quả.

### 2.2. Giao diện Người dùng (Templates HTML)
- [NEW] `app/templates/learning/quiz_take.html`:
  - Header Bar: Nút Hướng dẫn ℹ️, Đồng hồ ⏱️, Nút Tạm dừng ⏸️, Nút Nộp bài 📤.
  - Question Nav Sidebar: Nút số thứ tự câu hỏi (1..N) cho phép nhảy trực tiếp, kèm bộ lọc "Xem câu đánh dấu 🚩".
  - Center Workspace: Tiến độ câu hỏi (`Câu 1/20`), Văn bản câu hỏi, Lựa chọn A/B/C/D, Nút Đánh dấu 🚩.
  - Bottom Bar: Nút Câu trước ⬅️, Nút Câu sau ➡️, Nút Nộp bài.
  - Modals: Hướng dẫn làm bài, Tạm dừng/Tiếp tục, Hộp thoại xác nhận nộp bài (Submit confirmation modal).

---

## 3. Kế hoạch Kiểm thử & Xác nhận (Verification Plan)

### Automated Tests (`tests/test_quiz_taking.py`)
1. Test khởi tạo bài quiz `/learning/quizzes/<id>/start`.
2. Test lưu đáp án và chuyển câu hỏi nhảy trực tiếp (Jump to question).
3. Test đánh dấu cờ 🚩 xem lại câu hỏi.
4. Test chức năng tạm dừng / tiếp tục bài quiz.
5. Test nộp bài quiz thành công và tạo bản ghi `QuizAttempt`.
6. Test tự động nộp bài khi hết giờ (Auto-submit on timeout).

### Manual Verification
1. Chọn bài quiz từ danh sách ➔ Nhấp "Bắt đầu quiz".
2. Kiểm tra hiển thị Hướng dẫn làm bài ℹ️.
3. Làm thử vài câu, bấm Đánh dấu cờ 🚩, chọn nhảy câu từ Navigation bar.
4. Bấm "Tạm dừng" ⏸️ ➔ Kiểm tra đồng hồ dừng và nội dung ẩn ➔ Bấm "Tiếp tục làm bài".
5. Bấm "Nộp bài" ➔ Kiểm tra Modal hiển thị số câu đã làm, số câu chưa làm, số câu đánh dấu 🚩.
6. Xác nhận nộp bài ➔ Chuyển thành công sang giao diện kết quả.

---

# Kế hoạch Triển khai Tính năng 4.4: Quiz Results (Kết quả quiz)

Tài liệu này chi tiết hóa kế hoạch xây dựng và hoàn thiện toàn bộ **11 hạng mục con** thuộc **Mục 4.4: Quiz Results (Kết quả quiz)** của dự án **EnglishMate**.

> [!IMPORTANT]
> **Cam kết thiết kế**: Giữ nguyên 100% design, màu sắc, font chữ (`Manrope`), layout, spacing và UI/UX hiện tại của hệ thống. Tái sử dụng tối đa các component Bootstrap 5, stat card, progress ring, badge, modal share, print layout và CSS utility sẵn có.

---

## 1. Mục tiêu & Phạm vi (Scope of Work)

Hoàn thiện đầy đủ 11 hạng mục con thuộc Mục 4.4:

1. **[x] Score display after submission**: Hiển thị điểm số ngay sau khi nộp bài (VD: 8/10 điểm).
2. **[x] Detailed score breakdown**: Phân tích chi tiết số câu đúng, số câu sai, số câu chưa trả lời.
3. **[x] Accuracy analysis**: Phân tích tỷ lệ chính xác % (`accuracy_rate`) kèm xếp loại kết quả (Xuất sắc / Giỏi / Khá / Cần cố gắng).
4. **[x] Time spent analysis**: Phân tích thời gian làm bài thực tế (tổng thời gian và thời gian trung bình mỗi câu hỏi).
5. **[x] Incorrect answers review**: Danh sách xem lại các câu trả lời sai.
6. **[x] Correct answers display**: Hiển thị đáp án đúng cho từng câu hỏi trong danh sách xem lại.
7. **[x] Explanations display**: Hiển thị phần giải thích kiến thức chi tiết cho từng câu hỏi.
8. **[x] Add to error log**: Tự động lưu các câu làm sai vào Nhật ký lỗi (`GrammarErrorLog`) để phục vụ ôn tập lại.
9. **[x] Retake quiz option**: Nút "Làm lại bài quiz này" cho phép thực hành lại ngay lập tức.
10. **[x] Share results**: Modal & Nút chia sẻ kết quả học tập (Copy link / Web Share API).
11. **[x] Download report PDF**: Chế độ xem & tải báo cáo kết quả bài test dạng PDF / In ấn khổ giấy A4.

---

## 2. Các thay đổi Kiến trúc & Mã nguồn

### 2.1. Controller & Logic (`app/modules/learning/routes.py`)
- Route `GET /learning/quizzes/results/<int:attempt_id>` (và route đồng bộ `/learning/quizzes/summary/<int:attempt_id>`):
  - Truy vấn kết quả `QuizAttempt` và danh sách `QuizAttemptAnswer`.
  - Phân tích tổng điểm, điểm phần trăm %, thời gian làm bài, số câu đúng/sai/bỏ trống.
  - Tự động kiểm tra và thêm các câu trả lời sai vào `GrammarErrorLog`.
- Route `GET /learning/quizzes/results/<int:attempt_id>/pdf`:
  - Trả về giao diện báo cáo PDF / In ấn khổ A4 cho bài quiz.

### 2.2. Giao diện Người dùng (Templates HTML)
- [NEW] `app/templates/learning/quiz_results.html`:
  - Banner Tổng kết Kết quả hoành tráng với Thẻ điểm số, Vòng % Accuracy, Đánh giá xếp loại và Thống kê thời gian.
  - Bộ lọc xem câu hỏi (Tất cả / Chỉ câu sai / Chỉ câu đúng).
  - Khối xem chi tiết từng câu hỏi: Văn bản câu hỏi, Đáp án của bạn, Đáp án đúng và Khối giải thích chi tiết.
  - Toolbar hành động: Nút Làm lại quiz 🔄, Nút Chia sẻ kết quả 🔗 (kèm Modal share), Nút Tải/In báo cáo PDF 📄.
- [NEW] `app/templates/learning/quiz_results_pdf.html`:
  - Giao diện báo cáo PDF in ấn tối ưu sạch đẹp chuẩn khổ A4.

---

## 3. Kế hoạch Kiểm thử & Xác nhận (Verification Plan)

### Automated Tests (`tests/test_quiz_results.py`)
1. Test xem kết quả bài quiz `/learning/quizzes/results/<attempt_id>`.
2. Test hiển thị điểm số, tỷ lệ chính xác %, phân tích thời gian đã dùng.
3. Test tự động ghi nhận câu sai vào `GrammarErrorLog`.
4. Test tùy chọn làm lại quiz (Retake quiz option).
5. Test chia sẻ kết quả và xuất báo cáo PDF `/learning/quizzes/results/<attempt_id>/pdf`.

### Manual Verification
1. Hoàn thành một bài quiz ➔ Kiểm tra tự động chuyển hướng đến màn hình Kết quả.
2. Kiểm tra các thẻ thông số: Điểm số, Accuracy %, Thời gian sử dụng.
3. Kiểm tra danh sách câu sai hiển thị đúng Đáp án của bạn, Đáp án đúng và Phần giải thích.
4. Bấm "🔄 Làm lại quiz" ➔ Kiểm tra hệ thống tạo bài làm mới.
5. Bấm "🔗 Chia sẻ kết quả" ➔ Kiểm tra hiển thị Modal chia sẻ.
6. Bấm "📄 Tải báo cáo PDF" ➔ Kiểm tra giao diện báo cáo PDF in ấn A4.

---

# Kế hoạch Triển khai Tính năng 4.5: Exam Management (Quản lý đề thi - Admin)

Tài liệu này chi tiết hóa kế hoạch xây dựng và hoàn thiện toàn bộ **16 hạng mục con** thuộc **Mục 4.5: Exam Management (Quản lý đề thi - Admin)** của dự án **EnglishMate**.

> [!IMPORTANT]
> **Cam kết thiết kế**: Giữ nguyên 100% design, màu sắc, font chữ (`Manrope`), layout, spacing và UI/UX hiện tại của hệ thống. Tái sử dụng tối đa các component Bootstrap 5, admin table, badge, modal preview, stat card và CSS utility sẵn có.

---

## 1. Mục tiêu & Phạm vi (Scope of Work)

Hoàn thiện đầy đủ 16 hạng mục con thuộc Mục 4.5:

1. **[x] Create new exam button**: Nút "Tạo đề thi mới" tại trang Quản lý Admin.
2. **[x] Exam configuration form**: Form cấu hình đầy đủ các thông số đề thi.
3. **[x] Exam title input**: Trường nhập tiêu đề đề thi.
4. **[x] Exam category selection**: Bộ chọn danh mục đề thi (TOEIC, IELTS, TOEFL, Custom, Placement, Progress...).
5. **[x] Exam duration setting**: Cài đặt thời lượng làm bài (tính theo phút).
6. **[x] Exam difficulty setting**: Cài đặt độ khó đề thi (Easy, Medium, Hard).
7. **[x] Question bank selection**: Chọn ngân hàng câu hỏi (Grammar bank, Vocabulary bank, TOEIC bank, IELTS bank...).
8. **[x] Random question selection**: Tùy chọn tự động lấy câu hỏi ngẫu nhiên.
9. **[x] Manual question selection**: Tùy chọn chọn danh sách câu hỏi thủ công.
10. **[x] Question count setting**: Cài đặt số lượng câu hỏi của đề thi.
11. **[x] Exam preview**: Giao diện xem trước nội dung & cấu trúc đề thi trước khi xuất bản.
12. **[x] Publish exam button**: Nút / Toggle xuất bản / ẩn đề thi.
13. **[x] Edit exam button**: Nút & Form chỉnh sửa cấu hình đề thi.
14. **[x] Delete exam button**: Nút xóa đề thi kèm hộp thoại xác nhận.
15. **[x] Exam statistics view**: Trang xem tổng quan thống kê tất cả các đề thi.
16. **[x] Exam performance analytics**: Bảng phân tích chi tiết hiệu suất đề thi (Tổng lượt thi, Điểm trung bình, Tỷ lệ Đạt %, Thời gian trung bình làm bài).

---

## 2. Các thay đổi Kiến trúc & Mã nguồn

### 2.1. Cơ sở dữ liệu & Models (`app/modules/learning/models.py` & `patch_db.py`)
- [NEW] Model `Exam`:
  - `id`, `title`, `category`, `duration_minutes`, `difficulty`, `question_bank`, `selection_type`, `selected_question_ids`, `question_count`, `is_published`, `created_at`, `updated_at`.
- Cập nhật `patch_db.py`:
  - Tự động tạo bảng `exam` trong SQLite database.

### 2.2. Controller & Routes (`app/modules/admin/routes.py`)
- `GET /admin/exams`: Trang Danh sách & Tổng quan Quản lý đề thi.
- `GET/POST /admin/exams/new`: Form Tạo mới đề thi.
- `GET/POST /admin/exams/<int:exam_id>/edit`: Form Chỉnh sửa đề thi.
- `POST /admin/exams/<int:exam_id>/publish`: Toggle Xuất bản đề thi.
- `POST /admin/exams/<int:exam_id>/delete`: Xóa đề thi.
- `GET /admin/exams/<int:exam_id>/preview`: Xem trước nội dung đề thi.
- `GET /admin/exams/<int:exam_id>/stats`: Xem Phân tích hiệu suất đề thi (Total attempts, Avg score, Pass rate %, Avg duration).

### 2.3. Giao diện Người dùng (Admin Templates HTML)
- [NEW] `app/templates/admin/exams.html`: Bảng điều khiển Quản lý đề thi với Nút Tạo đề thi mới, Bảng đề thi, Nút Xuất bản, Nút Sửa, Nút Xóa, Nút Xem trước & Nút Xem Phân tích hiệu suất.
- [NEW] `app/templates/admin/exam_form.html`: Form cấu hình đề thi với đầy đủ các trường thiết lập.
- [NEW] `app/templates/admin/exam_preview.html`: Màn hình xem trước cấu trúc đề thi.
- [NEW] `app/templates/admin/exam_stats.html`: Trang phân tích chi tiết hiệu suất bài thi.

---

## 3. Kế hoạch Kiểm thử & Xác nhận (Verification Plan)

### Automated Tests (`tests/test_admin_exam_management.py`)
1. Test truy cập trang Quản lý đề thi Admin `/admin/exams`.
2. Test tạo mới đề thi với Form cấu hình đầy đủ.
3. Test chỉnh sửa đề thi.
4. Test xuất bản / ẩn đề thi.
5. Test xóa đề thi.
6. Test xem trước đề thi `/admin/exams/<id>/preview`.
7. Test xem phân tích hiệu suất đề thi `/admin/exams/<id>/stats`.

### Manual Verification
1. Đăng nhập tài khoản Admin ➔ Truy cập `/admin/exams`.
2. Bấm "➕ Tạo đề thi mới" ➔ Nhập tiêu đề, chọn TOEIC/IELTS, cài đặt thời gian, chọn chọn ngẫu nhiên / chọn thủ công.
3. Bấm "👁️ Xem trước đề thi" ➔ Kiểm tra hiển thị cấu trúc đề thi.
4. Bấm "🌐 Xuất bản" ➔ Kiểm tra thay đổi trạng thái đề thi.
5. Bấm "📊 Phân tích hiệu suất" ➔ Kiểm tra hiển thị biểu đồ thống kê điểm số & thời gian.

---

# Kế hoạch Triển khai Tính năng 4.6: Specialized Exams (Đề thi chuyên biệt)

Tài liệu này chi tiết hóa kế hoạch xây dựng và hoàn thiện toàn bộ **8 hạng mục con** thuộc **Mục 4.6: Specialized Exams (Đề thi chuyên biệt)** của dự án **EnglishMate**.

> [!IMPORTANT]
> **Cam kết thiết kế**: Giữ nguyên 100% design, màu sắc, font chữ (`Manrope`), layout, spacing và UI/UX hiện tại của hệ thống. Tái sử dụng tối đa các component Bootstrap 5, exam card, category badge, timer widget và CSS utility sẵn có.

---

## 1. Mục tiêu & Phạm vi (Scope of Work)

Hoàn thiện đầy đủ 8 hạng mục con thuộc Mục 4.6:

1. **[x] TOEIC Simulation**: Mô phỏng thi TOEIC chuẩn định dạng Full 200 câu & theo từng Part.
2. **[x] IELTS Practice**: Luyện thi IELTS 4 kỹ năng (Listening, Reading, Speaking, Writing) tích hợp chấm AI.
3. **[x] TOEFL Preparation**: Đề luyện thi chuẩn bị TOEFL iBT.
4. **[x] Custom Skill Tests**: Bài kiểm tra kỹ năng tùy chỉnh theo từng kỹ năng đơn lẻ (Grammar/Vocabulary/Listening/Reading/Speaking/Writing).
5. **[x] Placement Tests**: Bài kiểm tra xếp lớp phân loại trình độ đầu vào từ A1 đến C2.
6. **[x] Progress Assessment Tests**: Bài kiểm tra đánh giá tiến độ học tập định kỳ.
7. **[x] Timed Practice Sessions**: Các phiên luyện tập có tùy chỉnh giới hạn thời gian thực tế.
8. **[x] Mock Exams**: Đề thi thử tổng hợp áp lực thời gian thật.

---

## 2. Các thay đổi Kiến trúc & Mã nguồn

### 2.1. Controller & Logic (`app/modules/exams/routes.py`)
- Route `GET /exams/specialized`: Specialized Exams Hub (`specialized_exams_hub`), hiển thị 8 danh mục Đề thi chuyên biệt kèm bộ lọc và tìm kiếm.
- Route `GET /exams/specialized/placement`: Bắt đầu nhanh Bài kiểm tra xếp lớp Placement Test.
- Route `GET /exams/specialized/progress`: Bắt đầu nhanh Bài kiểm tra đánh giá tiến độ Progress Assessment.
- Route `GET/POST /exams/specialized/timed-practice`: Launcher cài đặt và khởi tạo Phiên luyện tập có giới hạn thời gian Timed Practice Session.

### 2.2. Giao diện Người dùng (Templates HTML)
- [NEW] `app/templates/exams/specialized_hub.html`: Trang Trung tâm Đề thi chuyên biệt với Banner giới thiệu, 8 Thẻ danh mục chuyên biệt, Thanh tìm kiếm & lọc, Bảng danh sách đề thi kèm thời gian & độ khó.
- [NEW] `app/templates/exams/timed_practice.html`: Màn hình cài đặt thông số Phiên luyện tập có giới hạn thời gian (Chọn số câu, thời gian 5-60 phút, độ khó).

---

## 3. Kế hoạch Kiểm thử & Xác nhận (Verification Plan)

### Automated Tests (`tests/test_specialized_exams.py`)
1. Test truy cập Trung tâm Đề thi chuyên biệt `/exams/specialized`.
2. Test các lối tắt Placement Test `/exams/specialized/placement` và Progress Test `/exams/specialized/progress`.
3. Test khởi tạo Phiên luyện tập thời gian `/exams/specialized/timed-practice`.
4. Test lọc đề thi theo 8 danh mục chuyên biệt (TOEIC, IELTS, TOEFL, Custom, Placement, Progress, Timed, Mock).

### Manual Verification
1. Đăng nhập học viên ➔ Truy cập Trung tâm Đề thi chuyên biệt `/exams/specialized`.
2. Bấm chọn danh mục "TOEIC Simulation" / "IELTS Practice" / "Placement Test".
3. Thử tạo một Phiên luyện tập có thời gian "Timed Practice Session".
4. Kiểm tra giao diện làm bài thi tương thích với từng loại đề thi chuyên biệt.

---

# Kế hoạch Triển khai Tính năng 4.7: Test History (Lịch sử kiểm tra)

Tài liệu này chi tiết hóa kế hoạch xây dựng và hoàn thiện toàn bộ **11 hạng mục con** thuộc **Mục 4.7: Test History (Lịch sử kiểm tra)** của dự án **EnglishMate**.

> [!IMPORTANT]
> **Cam kết thiết kế**: Giữ nguyên 100% design, màu sắc, font chữ (`Manrope`), layout, spacing và UI/UX hiện tại của hệ thống. Tái sử dụng tối đa các component Bootstrap 5, history table, badge, compare view, modal và CSS utility sẵn có.

---

## 1. Mục tiêu & Phạm vi (Scope of Work)

Hoàn thiện đầy đủ 11 hạng mục con thuộc Mục 4.7:

1. **[x] View all past tests**: Xem tất cả các lượt làm bài kiểm tra trong quá khứ từ tất cả các loại hình (Quiz, TOEIC, IELTS, TOEFL, Placement, Progress, Grammar).
2. **[x] Filter by test type**: Lọc lịch sử theo loại bài kiểm tra (Tất cả, Quiz, TOEIC, IELTS, TOEFL, Placement, Progress, Grammar Exercise).
3. **[x] Filter by date range**: Lọc bài thi theo khoảng thời gian (Từ ngày - Đến ngày hoặc chọn nhanh 7 ngày/30 ngày/Tất cả).
4. **[x] Filter by score range**: Lọc bài thi theo khoảng điểm phần trăm % (VD: 0-50%, 50-80%, 80-100%).
5. **[x] Sort by date/score**: Sắp xếp danh sách lịch sử theo Ngày làm (Mới nhất/Cũ nhất) hoặc Theo điểm số (Cao nhất/Thấp nhất).
6. **[x] Test list view with summary**: Chế độ xem danh sách bài thi với thẻ tóm tắt tổng số bài thi, Điểm trung bình, Điểm cao nhất và Tổng thời gian luyện tập.
7. **[x] Test detail view**: Chế độ xem chi tiết kết quả lượt kiểm tra.
8. **[x] Review specific test**: Xem lại chi tiết từng câu hỏi, lựa chọn của học viên, đáp án đúng và lời giải thích trong một bài thi cụ thể.
9. **[x] Compare tests**: Chức năng so sánh song song (Side-by-Side Comparison) giữa 2 lượt thi để xem sự tiến bộ về điểm số và thời gian.
10. **[x] Export test history**: Xuất danh sách lịch sử làm bài ra định dạng CSV/Excel.
11. **[x] Delete test record**: Xóa bản ghi lịch sử kiểm tra khỏi hệ thống kèm hộp thoại xác nhận.

---

## 2. Các thay đổi Kiến trúc & Mã nguồn

### 2.1. Controller & Logic (`app/modules/exams/routes.py` & `app/modules/learning/routes.py`)
- Route `GET /exams/history` (và route đồng bộ `/learning/quizzes/history`):
  - Tổng hợp dữ liệu lượt thi từ `QuizAttempt`, `ExamSubmission`, `ToeicAttempt`, `GrammarExerciseAttempt`.
  - Thực thi các bộ lọc: Loại bài thi (`type`), Khoảng ngày (`date_from`, `date_to`), Khoảng điểm (`min_score`, `max_score`) và Sắp xếp (`sort`).
- Route `GET /exams/history/review/<string:source>/<int:record_id>`:
  - Xem chi tiết từng câu hỏi và lời giải cho lượt thi chỉ định.
- Route `GET /exams/history/compare`:
  - So sánh 2 lượt làm bài thi lựa chọn.
- Route `GET /exams/history/export`:
  - Tải danh sách lịch sử làm bài dưới dạng file CSV/Excel.
- Route `POST /exams/history/<string:source>/<int:record_id>/delete`:
  - Xóa bản ghi lịch sử tương ứng.

### 2.2. Giao diện Người dùng (Templates HTML)
- [NEW] `app/templates/exams/test_history.html`: Trang Lịch sử Kiểm tra với 4 Thẻ tổng quan, Thanh công cụ lọc & sắp xếp đa chiều, Bảng danh sách bài thi kèm checkbox chọn so sánh, Nút Xem chi tiết 👁️, Nút Xem lại 📝, Nút So sánh ⚖️, Nút Xuất dữ liệu 📥, Nút Xóa 🗑️.
- [NEW] `app/templates/exams/test_compare.html`: Màn hình so sánh song song 2 bài làm thi.

---

## 3. Kế hoạch Kiểm thử & Xác nhận (Verification Plan)

### Automated Tests (`tests/test_test_history.py`)
1. Test truy cập trang Lịch sử kiểm tra `/exams/history`.
2. Test lọc theo loại bài thi, khoảng ngày, khoảng điểm và sắp xếp.
3. Test xem chi tiết lượt làm bài `/exams/history/review/<source>/<id>`.
4. Test so sánh 2 lượt làm bài `/exams/history/compare`.
5. Test xuất file lịch sử CSV/Excel `/exams/history/export`.
6. Test xóa bản ghi lịch sử `/exams/history/<source>/<id>/delete`.

### Manual Verification
1. Đăng nhập học viên ➔ Truy cập `/exams/history`.
2. Thử chọn lọc loại bài thi "TOEIC", chọn thời gian 30 ngày gần nhất, điểm > 60%.
3. Tích chọn 2 bài thi ➔ Bấm "⚖️ So sánh 2 bài thi" ➔ Kiểm tra hiển thị bảng so sánh.
4. Bấm "📥 Xuất dữ liệu CSV" ➔ Kiểm tra tải file CSV lịch sử.
5. Bấm "🗑️ Xóa" ➔ Kiểm tra xóa bản ghi thành công.