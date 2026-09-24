# 📚 KẾ HOẠCH TRIỂN KHAI GIAI ĐOẠN 2: HỆ THỐNG TỪ VỰNG & SRS FLASHCARD



---

# Kế hoạch Triển khai Tính năng 2.1: Vocabulary Dashboard (Bảng điều khiển từ vựng)

Tài liệu này chi tiết hóa kế hoạch xây dựng và hoàn thiện toàn bộ cụm tính năng thuộc **Mục 2.1: Vocabulary Dashboard (Bảng điều khiển từ vựng)** của dự án **EnglishMate**.

> [!IMPORTANT]
> **Cam kết thiết kế**: Giữ nguyên 100% design, màu sắc, font chữ (`Manrope`), layout, spacing và UI/UX hiện tại của hệ thống. Tái sử dụng tối đa các component Bootstrap 5, progress bar, stat card và CSS utility sẵn có.

---

## 1. Mục tiêu & Phạm vi (Scope of Work)

Hoàn thiện đầy đủ 10 hạng mục con thuộc Mục 2.1:

1. **[x] Total vocabulary count display**: Hiển thị tổng số từ vựng có trên hệ thống.
2. **[x] Mastered vocabulary count**: Số từ vựng người dùng đã học thành thạo (đã học/ôn $\ge 3$ lần).
3. **[x] Learning vocabulary count**: Số từ vựng đang trong quá trình ghi nhớ (học/ôn 1–2 lần).
4. **[x] New vocabulary count**: Số từ mới chưa từng học.
5. **[x] Review vocabulary count**: Số từ vựng cần ôn tập lại.
6. **[x] Vocabulary progress bar**: Thanh phần trăm tiến độ tổng quan trực quan.
7. **[x] Level vocabulary progress**: Tiến độ từ vựng phân chia theo các Cấp độ (A1, A2, B1, B2, C1, C2) với phần trăm riêng biệt.
8. **[x] Daily vocabulary goal (20/30/40 words)**: Bộ chọn mục tiêu từ vựng hàng ngày (20 từ / 30 từ / 40 từ) cho phép người dùng tùy chỉnh.
9. **[x] Today's learned count**: Thống kê số từ vựng đã học mới trong ngày hôm nay.
10. **[x] Today's reviewed count**: Thống kê số từ vựng đã ôn tập lại trong ngày hôm nay.

---

## 2. Các thay đổi Kiến trúc & Mã nguồn

### 2.1. Cơ sở dữ liệu & Model (`app/modules/auth/models.py` & `patch_db.py`)
- Bổ sung trường `daily_vocab_goal` (Integer, mặc định 20) vào bảng `user` để lưu cài đặt mục tiêu hàng ngày của học viên.
- Cập nhật script `patch_db.py` tự động bổ sung cột `daily_vocab_goal`.

### 2.2. Controller & Business Logic (`app/modules/learning/routes.py`)
- Cập nhật controller `/learning/vocabulary` (hoặc `/vocabulary`):
  - Tính toán các chỉ số thống kê: Total, Mastered, Learning, New, Needs Review.
  - Phân tích tiến độ học từ vựng theo từng Cấp độ (A1, A2, B1, B2, C1, C2).
  - Đếm số từ đã học mới hôm nay (`today_learned_count`) và đã ôn tập hôm nay (`today_reviewed_count`).
  - Thêm endpoint `POST /learning/vocabulary/set-goal` xử lý chọn mục tiêu hàng ngày (20 / 30 / 40 từ).

### 2.3. Giao diện Người dùng (`app/templates/learning/vocabulary.html`)
Nâng cấp trang Bảng điều khiển từ vựng với layout chuẩn UI/UX của EnglishMate:
- **Thẻ Thống kê Tổng quan (Stat Grid Cards)**: Hiển thị 4 thẻ thông tin nổi bật (Tổng từ, Thành thạo, Đang học, Từ mới).
- **Thanh Tiến độ Học tập Tổng quan & Mục tiêu Hàng ngày**: Progress bar theo dõi tiến độ tiến tới mục tiêu 20/30/40 từ hôm nay.
- **Tiến độ theo Cấp độ (Level Breakdown)**: Các thanh tiến độ riêng cho từng level A1, A2, B1, B2, C1, C2.
- **Form Đặt mục tiêu hàng ngày**: Radio/Button switch 20 từ / 30 từ / 40 từ.

---

## 3. Kế hoạch Kiểm thử & Xác nhận (Verification Plan)

### Automated Tests (`tests/test_vocabulary_dashboard.py`)
1. Test tính toán chính xác các chỉ số Vocabulary Dashboard (Total, Mastered, Learning, New).
2. Test tính toán phần trăm tiến độ theo Cấp độ (A1–C2).
3. Test tính năng thiết lập mục tiêu hàng ngày (`POST /learning/vocabulary/set-goal`).
4. Test ghi nhận số từ đã học và đã ôn hôm nay (`today_learned_count`, `today_reviewed_count`).

### Manual Verification
1. Truy cập `/learning/vocabulary` ➔ Kiểm tra các thẻ thống kê và thanh tiến độ hiển thị trực quan.
2. Thử bấm học từ mới và ôn tập ➔ Số liệu hôm nay và thanh tiến độ mục tiêu tăng tương ứng.
3. Thay đổi mục tiêu từ 20 từ thành 30 từ ➔ Giao diện cập nhật mục tiêu mới ngay lập tức.

---

# Kế hoạch Triển khai Tính năng 2.2: Vocabulary Learning (Học từ vựng)

Tài liệu này chi tiết hóa kế hoạch xây dựng và hoàn thiện toàn bộ cụm tính năng thuộc **Mục 2.2: Vocabulary Learning (Học từ vựng)** của dự án **EnglishMate**.

> [!IMPORTANT]
> **Cam kết thiết kế**: Giữ nguyên 100% design, màu sắc, font chữ (`Manrope`), layout, spacing và UI/UX hiện tại của hệ thống. Tái sử dụng tối đa các component Bootstrap 5, modal, badge và CSS utility sẵn có.

---

## 1. Mục tiêu & Phạm vi (Scope of Work)

Hoàn thiện đầy đủ 22 hạng mục con thuộc Mục 2.2:

1. **[x] Learn new words button**: Nút "Học từ mới" nổi bật tại Bảng điều khiển từ vựng.
2. **[x] Display word in English**: Hiển thị từ tiếng Anh cỡ chữ lớn, rõ ràng.
3. **[x] Display pronunciation (IPA)**: Hiển thị ký âm phiên âm chuẩn quốc tế IPA (ví dụ: `/ˈæp.əl/`).
4. **[x] Audio playback button**: Nút phát âm thanh đọc chuẩn bản ngữ bằng Web Speech API (`speechSynthesis`).
5. **[x] Display Vietnamese meaning**: Hiển thị nghĩa tiếng Việt chuẩn xác.
6. **[x] Display example sentence**: Hiển thị câu ví dụ tiếng Anh trong ngữ cảnh thực tế.
7. **[x] Display example translation**: Hiển thị dịch nghĩa tiếng Việt của câu ví dụ.
8. **[x] Display word type (noun/verb/adjective)**: Badge nhãn loại từ (Danh từ, Động từ, Tính từ, Trạng từ).
9. **[x] Display related image**: Hiển thị hình ảnh minh họa liên quan đến từ vựng.
10. **[x] Display collocations**: Hiển thị danh sách các cụm từ hay đi kèm (Collocations).
11. **[x] Display synonyms**: Hiển thị các từ đồng nghĩa (Synonyms).
12. **[x] Display antonyms**: Hiển thị các từ trái nghĩa (Antonyms).
13. **[x] Mark as learned button**: Nút đánh dấu từ đã học thành công (✓ Đã học).
14. **[x] Skip word button**: Nút bỏ qua từ vựng hiện tại (⏭️ Bỏ qua).
15. **[x] Add to favorites button**: Nút thả tim / lưu từ vựng vào danh sách yêu thích (❤️ Yêu thích).
16. **[x] Report word button**: Nút gửi báo cáo lỗi từ vựng (🚩 Báo cáo sai sót).
17. **[x] Next word button**: Nút chuyển sang từ tiếp theo (Từ tiếp ►).
18. **[x] Previous word button**: Nút quay lại từ phía trước (◄ Từ trước).
19. **[x] Auto-play audio option**: Công tắc bật/tắt tự động phát âm thanh mỗi khi chuyển từ mới.
20. **[x] Show/hide meaning option**: Nút con mắt 👁️ che/mở nghĩa tiếng Việt và câu dịch để tự kiểm tra ghi nhớ.
21. **[x] Flashcard mode toggle**: Nút chuyển đổi nhanh sang chế độ thẻ ghi nhớ Flashcard.
22. **[x] Quiz mode toggle**: Nút chuyển đổi nhanh sang chế độ làm bài tập Trắc nghiệm ôn luyện.

---

## 2. Các thay đổi Kiến trúc & Mã nguồn

### 2.1. Cơ sở dữ liệu & Model (`app/modules/learning/models.py` & `patch_db.py`)
- Cập nhật model `Vocabulary`:
  - `image_url`: Đường dẫn ảnh minh họa từ vựng.
  - `collocations`: Chuỗi danh sách cụm từ hay đi cùng.
  - `synonyms`: Chuỗi từ đồng nghĩa.
  - `antonyms`: Chuỗi từ trái nghĩa.
- Cập nhật model `VocabularyProgress`:
  - `is_favorite`: Trạng thái yêu thích (Boolean).
  - `is_skipped`: Trạng thái bỏ qua (Boolean).
- Tạo model `WordReport`: Lưu vết báo cáo sai sót từ vựng từ người dùng (`user_id`, `vocabulary_id`, `reason`, `created_at`).
- Script `patch_db.py`: Tự động vá CSDL bổ sung các cột và bảng mới.

### 2.2. Controller & API Route (`app/modules/learning/routes.py`)
- `GET /learning/vocabulary/study`: Giao diện học từ vựng tương tác từng từ (`index`, `level`, `topic`).
- `POST /learning/vocabulary/<id>/favorite`: Toggle trạng thái yêu thích từ vựng.
- `POST /learning/vocabulary/<id>/skip`: Bỏ qua từ vựng.
- `POST /learning/vocabulary/<id>/report`: Gửi báo cáo lỗi nội dung từ vựng.

### 2.3. Giao diện Học từ vựng (`app/templates/learning/study_vocabulary.html`)
Tạo mới giao diện học từ vựng tương tác thẻ bài đỉnh cao:
- Thanh công cụ phía trên: Công tắc Tự động phát âm thanh, Che/Hiện nghĩa 👁️, Thả tim ❤️, Báo cáo 🚩, Chuyển Flashcard 🎴 / Quiz ❓.
- Khối thông tin từ vựng: Từ tiếng Anh, IPA, Nút loa 🔊 (phát giọng đọc AI Web Speech API), Loại từ, Nghĩa tiếng Việt, Câu ví dụ & dịch nghĩa, Collocations, Từ đồng nghĩa & trái nghĩa, Ảnh minh họa.
- Điều hướng chân trang: Nút ◄ Từ trước, ⏭️ Bỏ qua, ✓ Đã học, Từ tiếp ►.

---

## 3. Kế hoạch Kiểm thử & Xác nhận (Verification Plan)

### Automated Tests (`tests/test_vocabulary_learning.py`)
1. Test truy cập giao diện học tương tác `/learning/vocabulary/study`.
2. Test các nút hành động: Đánh dấu đã học, Bỏ qua từ (Skip), Thêm vào yêu thích (Favorite).
3. Test tính năng gửi Báo cáo từ vựng (Word Report).
4. Test hiển thị đầy đủ thông tin nâng cao (IPA, loại từ, Collocations, Synonyms, Antonyms).

### Manual Verification
1. Truy cập `/learning/vocabulary` ➔ Nhấn **"Bắt đầu học từ mới"** ➔ Mở trang `/learning/vocabulary/study`.
2. Thử nhấn nút Loa 🔊 để nghe phát âm, bấm nút con mắt 👁️ che/mở nghĩa.
3. Thử bật công tắc "Tự động phát âm thanh" ➔ Chuyển từ tiếp ➔ Âm thanh tự động đọc.
4. Bấm thả tim ❤️, thử bấm Bỏ qua ⏭️, thử gửi Báo cáo lỗi 🚩.

---

# Kế hoạch Triển khai Tính năng 2.3: Vocabulary Review (SRS) (Ôn tập từ vựng - SRS)

Tài liệu này chi tiết hóa kế hoạch xây dựng và hoàn thiện toàn bộ 18 hạng mục con thuộc **Mục 2.3: Vocabulary Review (SRS)** của dự án **EnglishMate**.

> [!IMPORTANT]
> **Cam kết thiết kế**: Giữ nguyên 100% design, màu sắc, font chữ (`Manrope`), layout, spacing và UI/UX hiện tại của hệ thống. Tái sử dụng tối đa các component Bootstrap 5, badge, progress bar, modal và CSS utility sẵn có.

---

## 1. Mục tiêu & Phạm vi (Scope of Work)

Hoàn thiện đầy đủ 18 hạng mục con thuộc Mục 2.3:

1. **[x] Review due words notification**: Thông báo số lượng từ vựng đến hạn ôn tập (Due for SRS Review) trên Vocabulary Dashboard và Header/Navbar.
2. **[x] Review queue display**: Hiển thị danh sách / hàng đợi các từ vựng đến hạn ôn tập trong lượt ôn hiện tại (`/learning/vocabulary/review`).
3. **[x] SRS level indicator (1-7)**: Đánh dấu và hiển thị cấp độ lặp lại ngắt quãng SRS Level (Level 1 đến Level 7 - Thành thạo/Mastered).
4. **[x] Review count display**: Hiển thị tổng số lần học viên đã ôn tập từ vựng đó (`review_count`).
5. **[x] Last review date**: Hiển thị mốc thời gian lần ôn tập gần nhất (`last_reviewed_at`).
6. **[x] Next review date**: Hiển thị mốc thời gian ôn tập tiếp theo được tính toán theo thuật toán SRS (`next_review_at`).
7. **[x] Flashcard review mode**: Chế độ ôn tập lật thẻ ghi nhớ Flashcard tương tác.
8. **[x] Meaning review mode**: Chế độ ôn tập trắc nghiệm chọn nghĩa đúng (Tiếng Anh ➔ Tiếng Việt / Tiếng Việt ➔ Tiếng Anh).
9. **[x] Audio review mode**: Chế độ ôn tập qua âm thanh (Nghe phát âm tiếng Anh ➔ Đoán nghĩa / chọn đáp án).
10. **[x] Spelling review mode**: Chế độ ôn tập chính tả (Gõ chính xác từ tiếng Anh dựa trên gợi ý nghĩa / âm thanh).
11. **[x] Show answer button**: Nút "Hiện đáp án" cho phép người dùng lật xem / mở đáp án kiểm tra.
12. **[x] Correct/incorrect buttons**: Nút đánh dấu nhanh Đã nhớ (Correct) / Quên (Incorrect).
13. **[x] Easy/Good/Hard buttons**: Nút đánh giá mức độ ghi nhớ (Easy: +2 Cấp SRS, Good: +1 Cấp SRS, Hard: giữ nguyên SRS / lặp lại sớm).
14. **[x] Skip review button**: Nút bỏ qua từ vựng hiện tại trong hàng đợi ôn tập để chuyển sang từ tiếp theo.
15. **[x] Review progress bar**: Thanh tiến độ trực quan hiển thị số từ đã ôn tập trên tổng số từ trong hàng đợi (ví dụ: 4/12 từ).
16. **[x] Review session summary**: Màn hình tổng kết khi hoàn thành phiên ôn tập (số từ đã hoàn thành, độ chính xác %, thời gian).
17. **[x] Words mastered in session**: Thống kê số lượng từ đạt SRS Level 7 (Thành thạo) ngay trong phiên ôn.
18. **[x] Words needing more review**: Thống kê số từ trả lời chưa tốt (Hard / Incorrect) cần được ôn tập lại trong phiên kế tiếp.

---

## 2. Các thay đổi Kiến trúc & Mã nguồn

### 2.1. Cơ sở dữ liệu & Model (`app/modules/learning/models.py` & `patch_db.py`)
- Cập nhật model `VocabularyProgress`:
  - `srs_level`: Integer (1 đến 7, default=1).
  - `next_review_at`: DateTime(timezone=True) (default=now).
- Cập nhật script `patch_db.py`:
  - Tự động bổ sung 2 cột `srs_level` và `next_review_at` vào bảng `vocabulary_progress`.
  - Khởi tạo giá trị mặc định cho dữ liệu hiện có.

### 2.2. Thuật toán SRS (Spaced Repetition System) & Helper (`app/modules/learning/routes.py`)
- Thiết lập khoảng thời gian ôn tập (Intervals) tương ứng SRS Level:
  - Level 1: +1 ngày
  - Level 2: +2 ngày
  - Level 3: +4 ngày
  - Level 4: +7 ngày
  - Level 5: +14 ngày
  - Level 6: +30 ngày
  - Level 7: +90 ngày (Mastered)
- Hàm cập nhật SRS theo phản hồi của người dùng:
  - **Easy**: `srs_level = min(7, srs_level + 2)`, `next_review_at = now + interval(srs_level)`
  - **Good / Correct**: `srs_level = min(7, srs_level + 1)`, `next_review_at = now + interval(srs_level)`
  - **Hard**: `srs_level = max(1, srs_level)`, `next_review_at = now + 1 day`
  - **Incorrect**: `srs_level = max(1, srs_level - 1)`, `next_review_at = now + 1 day`

### 2.3. Route & API Controller (`app/modules/learning/routes.py`)
- `GET /learning/vocabulary/review`: Giao diện ôn tập SRS (Flashcard, Meaning, Audio, Spelling modes). Hàng đợi `due_words` được lọc theo `next_review_at <= now()`.
- `POST /learning/vocabulary/review/submit`: API tiếp nhận đánh giá (Easy/Good/Hard/Incorrect/Skip) và cập nhật tiến độ SRS real-time cho từ vựng.
- `GET /learning/vocabulary/review/summary`: Giao diện hiển thị tổng kết phiên ôn tập (Review Session Summary).

### 2.4. Giao diện Người dùng (`app/templates/learning/review_vocabulary.html` & `app/templates/learning/review_summary.html` & `app/templates/learning/vocabulary.html`)
- **Thông báo từ cần ôn tập (Due Words Notification)**: Hiển thị Banner Nổi bật + Badge thông báo số lượng từ đến hạn trên Dashboard.
- **Thanh tiến độ ôn tập (Progress Bar)**: Hiển thị tiến trình hoàn thành hàng đợi.
- **Các chế độ Ôn tập (Mode Switches)**:
  - 🎴 Flashcard mode: Lật thẻ hiện mặt sau / nút Hiện đáp án.
  - 📖 Meaning mode: Chọn 1 trong 4 phương án nghĩa tiếng Việt.
  - 🔊 Audio mode: Nghe âm thanh chuẩn ➔ Chọn nghĩa hoặc nhập từ.
  - ✍️ Spelling mode: Gõ chính tả từ tiếng Anh ➔ Đánh giá chính xác.
- **Bảng nút đánh giá**: Nút Nút Hiện đáp án, Nút Đúng/Sai, Easy/Good/Hard, Nút Bỏ qua ôn.
- **Trang Tóm tắt Phiên ôn (Summary Page)**:
  - Thống kê tổng số từ đã ôn tập.
  - Thống kê Số từ đạt Thành thạo (Mastered in Session - SRS Level 7).
  - Thống kê Số từ cần ôn thêm (Words Needing More Review).

---

## 3. Kế hoạch Kiểm thử & Xác nhận (Verification Plan)

### Automated Tests (`tests/test_vocabulary_review.py`)
1. Test truy cập giao diện Ôn tập SRS `/learning/vocabulary/review`.
2. Test hàng đợi từ vựng đến hạn (Review queue filtering by `next_review_at`).
3. Test cập nhật chỉ số SRS Level (1-7) và ngày ôn tiếp theo khi gửi phản hồi Easy/Good/Hard/Incorrect.
4. Test các chế độ ôn tập: Flashcard, Meaning, Audio, Spelling.
5. Test giao diện Tóm tắt phiên ôn (`/learning/vocabulary/review/summary`).

### Manual Verification
1. Truy cập `/learning/vocabulary` ➔ Kiểm tra Banner Thông báo từ cần ôn tập.
2. Bấm "Ôn tập ngay" ➔ Mở trang `/learning/vocabulary/review`.
3. Chuyển đổi giữa 4 chế độ: Flashcard, Meaning, Audio, Spelling.
4. Bấm "Hiện đáp án", thử chọn Easy / Good / Hard / Bỏ qua.
5. Hoàn thành toàn bộ hàng đợi ➔ Chuyển hướng đến màn hình Tóm tắt phiên ôn và kiểm tra các thống kê (Từ thành thạo, từ cần ôn thêm).

---

# Kế hoạch Triển khai Tính năng 2.4: Vocabulary Management (Quản lý từ vựng)

Tài liệu này chi tiết hóa kế hoạch xây dựng và hoàn thiện toàn bộ **16 hạng mục con** thuộc **Mục 2.4: Vocabulary Management (Quản lý từ vựng)** của dự án **EnglishMate**.

> [!IMPORTANT]
> **Cam kết thiết kế**: Giữ nguyên 100% design, màu sắc, font chữ (`Manrope`), layout, spacing và UI/UX hiện tại của hệ thống. Tái sử dụng tối đa các component Bootstrap 5, badge, modal, table/card list và CSS utility sẵn có.

---

## 1. Mục tiêu & Phạm vi (Scope of Work)

Hoàn thiện đầy đủ 16 hạng mục con thuộc Mục 2.4:

1. **[x] Search vocabulary by English**: Tìm kiếm từ vựng chính xác hoặc tương đối theo từ tiếng Anh.
2. **[x] Search vocabulary by Vietnamese**: Tìm kiếm từ vựng theo nghĩa tiếng Việt.
3. **[x] Filter by level (A1-C2)**: Lọc từ vựng theo khung tham chiếu trình độ Châu Âu CEFR (A1, A2, B1, B2, C1, C2).
4. **[x] Filter by topic (Business, Daily Life, etc.)**: Lọc từ vựng theo chủ đề học tập.
5. **[x] Filter by status (New, Learning, Reviewing, Mastered)**: Lọc từ vựng theo trạng thái tiến độ (Từ mới, Đang học, Đến hạn ôn, Thành thạo).
6. **[x] Filter by SRS level (1-7)**: Lọc từ vựng theo cấp độ ghi nhớ lặp lại ngắt quãng (Level 1 đến Level 7).
7. **[x] Sort by learned date**: Sắp xếp danh sách theo ngày bắt đầu học mới nhất / cũ nhất.
8. **[x] Sort by review date**: Sắp xếp danh sách theo ngày ôn tập gần nhất hoặc ngày đến hạn ôn kế tiếp.
9. **[x] Sort by alphabet**: Sắp xếp danh sách từ vựng theo thứ tự bảng chữ cái A-Z hoặc Z-A.
10. **[x] View vocabulary details**: Modal hiển thị chi tiết toàn bộ thông tin từ vựng (Từ, IPA, loại từ, nghĩa, ví dụ, collocations, synonyms, antonyms, ghi chú).
11. **[x] Edit vocabulary notes**: Chỉnh sửa và cập nhật nội dung ghi chú từ vựng cá nhân.
12. **[x] Add personal notes**: Thêm mới ghi chú cá nhân cho từng từ vựng.
13. **[x] Add custom example sentences**: Thêm và cập nhật câu ví dụ tùy chỉnh cá nhân cho từ vựng.
14. **[x] Delete vocabulary from learning**: Xóa từ vựng khỏi danh sách đã học (xóa bản ghi progress cá nhân).
15. **[x] Reset vocabulary progress**: Đặt lại tiến độ học từ vựng về trạng thái ban đầu (`learned_count=0`, `review_count=0`, `srs_level=1`).
16. **[x] Bulk operations (select multiple)**: Chọn hàng loạt từ vựng (Checkbox Select All / Select Item) để thực hiện các thao tác: Đánh dấu đã học hàng loạt, Đặt lại tiến độ hàng loạt, Xóa khỏi danh sách học hàng loạt.

---

## 2. Các thay đổi Kiến trúc & Mã nguồn

### 2.1. Cơ sở dữ liệu & Model (`app/modules/learning/models.py` & `patch_db.py`)
- Cập nhật model `VocabularyProgress`:
  - `personal_notes`: Text (nullable=True) - Lưu ghi chú cá nhân của người dùng cho từ vựng.
  - `custom_example`: Text (nullable=True) - Lưu câu ví dụ tùy chỉnh do người dùng tự tạo.
- Cập nhật script `patch_db.py`:
  - Tự động bổ sung 2 cột `personal_notes` và `custom_example` vào bảng `vocabulary_progress`.

### 2.2. Controller & API Routes (`app/modules/learning/routes.py`)
- `GET /learning/vocabulary/manage`: Trang Quản lý từ vựng chuyên sâu với đầy đủ bộ lọc (Tìm tiếng Anh/Việt, Level A1-C2, Topic, Status, SRS Level 1-7, Sắp xếp A-Z, Ngày học, Ngày ôn).
- `POST /learning/vocabulary/<id>/notes`: API cập nhật ghi chú cá nhân (`personal_notes`) và câu ví dụ tùy chỉnh (`custom_example`).
- `POST /learning/vocabulary/<id>/reset-progress`: API đặt lại tiến độ từ vựng về mặc định.
- `POST /learning/vocabulary/<id>/delete-progress`: API xóa từ vựng khỏi danh sách học cá nhân.
- `POST /learning/vocabulary/bulk-action`: API xử lý thao tác hàng loạt (Bulk Learn, Bulk Reset, Bulk Delete) cho danh sách từ vựng được chọn (`word_ids[]`).

### 2.3. Giao diện Người dùng (`app/templates/learning/manage_vocabulary.html`)
- **Thanh Công cụ Lọc & Tìm kiếm Nâng cao**: Tìm theo Từ EN / Nghĩa VI, Lọc Level, Topic, Status, SRS Level (1-7), Bộ sắp xếp (A-Z, Ngày học, Ngày ôn).
- **Thao tác Hàng loạt (Bulk Action Bar)**: Nút Chọn tất cả (Check all), Menu hành động hàng loạt (Đánh dấu đã học, Đặt lại tiến độ, Xóa khỏi danh sách).
- **Danh sách Từ vựng Quản lý**: Thẻ / Dòng từ vựng tích hợp Badge SRS Level 1-7, Status, Ghi chú cá nhân, và các nút Thao tác nhanh (Xem chi tiết 👁️, Sửa ghi chú 📝, Đặt lại 🔄, Xóa 🗑️).
- **Modal Xem chi tiết & Sửa Ghi chú Cá nhân**: Modal xem thông tin đầy đủ và form nhập Ghi chú cá nhân + Câu ví dụ tự tạo.

---

## 3. Kế hoạch Kiểm thử & Xác nhận (Verification Plan)

### Automated Tests (`tests/test_vocabulary_management.py`)
1. Test truy cập giao diện Quản lý từ vựng `/learning/vocabulary/manage`.
2. Test bộ lọc và tìm kiếm: Tìm kiếm theo EN / VI, Lọc theo Status (New, Learning, Mastered), Lọc SRS Level (1-7), Sắp xếp A-Z.
3. Test cập nhật Ghi chú cá nhân và Câu ví dụ tùy chỉnh.
4. Test đặt lại tiến độ (Reset Progress) và xóa khỏi danh sách học (Delete Progress).
5. Test thao tác hàng loạt Bulk Operations (Bulk Learn, Bulk Reset, Bulk Delete).

### Manual Verification
1. Truy cập `/learning/vocabulary/manage`.
2. Thử gõ tìm kiếm từ tiếng Anh và từ tiếng Việt.
3. Thử chọn bộ lọc Level B2, Topic Personality, Status Learning, SRS Level 1-7, Sắp xếp Z-A.
4. Thử bấm "Xem chi tiết & Ghi chú" ➔ Thêm ghi chú "Từ này hay gặp trong bài thi TOEIC" và câu ví dụ mới ➔ Lưu ➔ Kiểm tra hiển thị.
5. Thử tick chọn 3 từ vựng ➔ Chọn "Đặt lại tiến độ hàng loạt" ➔ Xác nhận dữ liệu được reset.

---

# Kế hoạch Triển khai Tính năng 2.5: Vocabulary Statistics (Thống kê từ vựng)

Tài liệu này chi tiết hóa kế hoạch xây dựng và hoàn thiện toàn bộ **10 hạng mục con** thuộc **Mục 2.5: Vocabulary Statistics (Thống kê từ vựng)** của dự án **EnglishMate**.

> [!IMPORTANT]
> **Cam kết thiết kế**: Giữ nguyên 100% design, màu sắc, font chữ (`Manrope`), layout, spacing và UI/UX hiện tại của hệ thống. Tái sử dụng tối đa các component Bootstrap 5, stat card, progress bar, badge và CSS utility sẵn có.

---

## 1. Mục tiêu & Phạm vi (Scope of Work)

Hoàn thiện đầy đủ 10 hạng mục con thuộc Mục 2.5:

1. **[x] Vocabulary growth chart (daily/weekly/monthly)**: Biểu đồ tăng trưởng số lượng từ vựng tích lũy theo Ngày (7 ngày qua), Tuần (4 tuần qua) và Tháng (6 tháng qua).
2. **[x] SRS level distribution chart**: Biểu đồ phân bổ số từ vựng theo 7 mức SRS Level (Level 1 đến Level 7 - Mastered).
3. **[x] Learning accuracy rate**: Tỷ lệ phần trăm trả lời / học từ vựng chính xác (Learning Accuracy %).
4. **[x] Review success rate**: Tỷ lệ phần trăm các lượt ôn tập SRS đạt kết quả Tốt / Dễ (Review Success %).
5. **[x] Mastered words timeline**: Timeline danh sách các từ vựng mới đạt mốc Thành thạo (SRS Level 7) sắp xếp theo mốc thời gian gần nhất.
6. **[x] Topic mastery breakdown**: Phân tích tỷ lệ phần trăm thành thạo từ vựng chi tiết theo từng Chủ đề (Topic).
7. **[x] Daily learning streak**: Thống kê số ngày duy trì học từ vựng liên tiếp hiện tại (`current_streak`).
8. **[x] Longest learning streak**: Thống kê kỷ lục chuỗi ngày học từ vựng liên tiếp dài nhất (`longest_streak`).
9. **[x] Vocabulary retention rate**: Tỷ lệ giữ lại và duy trì trí nhớ từ vựng lâu dài (Retention Rate %).
10. **[x] Weak vocabulary topics**: Phân tích các chủ đề từ vựng yếu (chủ đề có tỷ lệ thành thạo thấp hoặc từ cần ôn lại nhiều) để học viên chú trọng rèn luyện.

---

## 2. Các thay đổi Kiến trúc & Mã nguồn

### 2.1. Controller & Analytics Logic (`app/modules/learning/routes.py`)
- Route `GET /learning/vocabulary/stats`:
  - **Streak Stats**: Trích xuất `current_user.current_streak` & `current_user.longest_streak`.
  - **Accuracy & Success Rates**: Tính toán tỷ lệ thành công ôn tập SRS và độ chính xác tích lũy.
  - **Retention Rate**: Tính toán tỷ lệ từ vựng duy trì ở SRS Level 4+ so với tổng từ đã học.
  - **SRS Level Distribution**: Đếm số lượng từ vựng ở từng SRS Level (Level 1–7).
  - **Topic Mastery Breakdown**: Tính số từ thành thạo / tổng số từ cho mỗi Topic (Business, Daily Life, Personality, v.v.).
  - **Weak Vocabulary Topics**: Lọc 3 chủ đề có tỷ lệ thành thạo thấp nhất.
  - **Mastered Words Timeline**: Lấy danh sách từ vựng đạt Level 7 gần đây.
  - **Growth Chart Data**: Thống kê tăng trưởng 7 ngày, 4 tuần, 6 tháng.

### 2.2. Giao diện Người dùng (`app/templates/learning/vocabulary_stats.html` & `vocabulary.html`)
- **Trang Bảng Thống kê Từ vựng (`vocabulary_stats.html`)**:
  - **Thẻ Chỉ số Nổi bật (Metric Cards)**: Chuỗi ngày liên tiếp (Streak), Tỷ lệ chính xác %, Tỷ lệ ôn thành công %, Tỷ lệ giữ lại từ vựng %.
  - **Biểu đồ Tăng trưởng Từ vựng (Growth Chart)**: Bộ chuyển đổi xem Ngày / Tuần / Tháng với biểu đồ cột trực quan.
  - **Biểu đồ Phân phối SRS Level (SRS Level 1–7)**: Thanh phân bổ tỷ lệ phần trăm các từ vựng ở từng cấp SRS Level.
  - **Phân tích Thành thạo theo Chủ đề (Topic Mastery Breakdown)**: Danh sách thanh tiến độ theo chủ đề.
  - **Cảnh báo Chủ đề Yếu (Weak Topics Alert)**: Thẻ thông báo gợi ý tập trung ôn tập cho các chủ đề có điểm thành thạo chưa cao.
  - **Timeline Từ vựng Thành thạo (Mastered Words Timeline)**: Timeline danh sách từ đã đạt Mastered.
- **Bảng điều khiển Từ vựng (`vocabulary.html`)**:
  - Bổ sung nút bấm "📈 Thống kê từ vựng" chuyển hướng sang trang `/learning/vocabulary/stats`.

---

## 3. Kế hoạch Kiểm thử & Xác nhận (Verification Plan)

### Automated Tests (`tests/test_vocabulary_stats.py`)
1. Test truy cập trang Thống kê từ vựng `/learning/vocabulary/stats`.
2. Test tính toán chính xác các chỉ số: Streak (Daily & Longest), Learning Accuracy, Review Success Rate, Retention Rate.
3. Test phân bổ SRS Level Distribution (Level 1-7).
4. Test phân tích Topic Mastery Breakdown & Weak Topics.
5. Test Mastered Words Timeline & Growth Data (Daily, Weekly, Monthly).

### Manual Verification
1. Truy cập `/learning/vocabulary/stats`.
2. Kiểm tra các thẻ thông tin Streak, Accuracy %, Success Rate %, Retention Rate %.
3. Kiểm tra Biểu đồ tăng trưởng từ vựng khi chọn mốc Ngày / Tuần / Tháng.
4. Kiểm tra thanh phân bổ SRS Level (1-7) và bảng phân tích thành thạo theo Chủ đề.
5. Kiểm tra danh sách Timeline từ vựng thành thạo.

---

# Kế hoạch Triển khai Tính năng 2.6: Vocabulary Settings (Cài đặt từ vựng)

Tài liệu này chi tiết hóa kế hoạch xây dựng và hoàn thiện toàn bộ **8 hạng mục con** thuộc **Mục 2.6: Vocabulary Settings (Cài đặt từ vựng)** của dự án **EnglishMate**.

> [!IMPORTANT]
> **Cam kết thiết kế**: Giữ nguyên 100% design, màu sắc, font chữ (`Manrope`), layout, spacing và UI/UX hiện tại của hệ thống. Tái sử dụng tối đa các component Bootstrap 5, form switch, card, badge và CSS utility sẵn có.

---

## 1. Mục tiêu & Phạm vi (Scope of Work)

Hoàn thiện đầy đủ 8 hạng mục con thuộc Mục 2.6:

1. **[x] Daily new words goal (10-50)**: Cho phép tùy chỉnh mục tiêu học từ vựng mới hàng ngày (Từ 10 đến 50 từ/ngày).
2. **[x] Review priority setting**: Cài đặt thứ tự ưu tiên ôn tập (Theo hạn ôn `due_date`, Theo SRS Level tăng/giảm dần, Ngẫu nhiên).
3. **[x] Audio auto-play toggle**: Bật/tắt tự động phát âm thanh mỗi khi lật thẻ từ vựng mới.
4. **[x] Pronunciation accent selection (US/UK)**: Lựa chọn giọng đọc tiếng Anh chuẩn Mỹ (en-US) hoặc tiếng Anh chuẩn Anh (en-GB).
5. **[x] Display mode preference (flashcard/list)**: Lựa chọn chế độ hiển thị học ưu thích mặc định (Thẻ Flashcard lật hoặc Danh sách hàng ngang).
6. **[x] Review time preference (morning/evening)**: Lựa chọn khung giờ ưu thích gợi ý ôn tập (Buổi sáng 🌅, Buổi tối 🌙, Hoặc Bất kỳ lúc nào ⏰).
7. **[x] SRS algorithm selection (standard/aggressive/conservative)**: Lựa chọn thuật toán lặp lại ngắt quãng SRS (Tiêu chuẩn - Standard, Nhanh - Aggressive, Thận trọng - Conservative).
8. **[x] Notification settings for review due**: Bật/tắt nhận thông báo & banner nhắc nhở khi có từ vựng đến hạn ôn tập.

---

## 2. Các thay đổi Kiến trúc & Mã nguồn

### 2.1. Cơ sở dữ liệu & Model (`app/modules/auth/models.py` & `patch_db.py`)
- Cập nhật model `User`:
  - `daily_vocab_goal`: Integer (10–50, default=20).
  - `vocab_review_priority`: String(20) (default="due_date").
  - `vocab_auto_play_audio`: Boolean (default=True).
  - `vocab_accent`: String(10) (default="en-US").
  - `vocab_display_mode`: String(20) (default="flashcard").
  - `vocab_review_time`: String(20) (default="anytime").
  - `vocab_srs_algorithm`: String(20) (default="standard").
  - `vocab_notify_review_due`: Boolean (default=True).
- Cập nhật script `patch_db.py`:
  - Tự động bổ sung các cột cài đặt mới vào bảng `user` trong SQLite.

### 2.2. Controller & Business Logic (`app/modules/learning/routes.py`)
- `GET /learning/vocabulary/settings`: Hiển thị trang Cài đặt từ vựng cá nhân hóa.
- `POST /learning/vocabulary/settings`: Tiếp nhận dữ liệu form cài đặt, kiểm tra tính hợp lệ và cập nhật vào `current_user`.
- Cập nhật các controller học/ôn tập (`study_vocabulary`, `review_vocabulary`):
  - Tự động áp dụng giọng đọc US/UK (`vocab_accent`).
  - Áp dụng công tắc `vocab_auto_play_audio`.
  - Áp dụng thuật toán SRS theo lựa chọn Standard / Aggressive / Conservative.
  - Áp dụng ẩn/hiện banner thông báo theo `vocab_notify_review_due`.

### 2.3. Giao diện Người dùng (`app/templates/learning/vocabulary_settings.html` & `vocabulary.html`)
- **Trang Cài đặt Từ vựng (`vocabulary_settings.html`)**:
  - Giao diện form cấu hình nhóm trực quan với các công tắc Switch, Radio pills, Dropdown selector.
  - Thông báo Flash Toast thành công khi lưu cài đặt.
- **Trang Bảng điều khiển từ vựng (`vocabulary.html`)**:
  - Nút chuyển nhanh "⚙️ Cài đặt từ vựng" dẫn đến giao diện tùy chỉnh.

---

## 3. Kế hoạch Kiểm thử & Xác nhận (Verification Plan)

### Automated Tests (`tests/test_vocabulary_settings.py`)
1. Test truy cập giao diện `/learning/vocabulary/settings`.
2. Test lưu và cập nhật các tùy chọn cài đặt từ vựng (Goal 10-50, Accent US/UK, Auto-play, SRS Algorithm, Priority, Review time, Notifications).
3. Test tác động của cài đặt lên các luồng học & ôn tập.

### Manual Verification
1. Truy cập `/learning/vocabulary/settings`.
2. Đổi mục tiêu thành 30 từ/ngày, chọn giọng đọc en-GB, tắt tự động đọc, chọn SRS Aggressive ➔ Bấm Lưu Cài Đặt.
3. Vào trang Học từ vựng và Ôn tập SRS ➔ Kiểm tra phát âm thanh dùng giọng en-GB, công tắc tự động đọc mặc định tắt.