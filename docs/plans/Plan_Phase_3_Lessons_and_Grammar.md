# 📖 KẾ HOẠCH TRIỂN KHAI GIAI ĐOẠN 3: BÀI HỌC KỸ NĂNG & NGỮ PHÁP



---

# Kế hoạch Triển khai Tính năng 3.1: Lesson Dashboard (Bảng điều khiển bài học)

Tài liệu này chi tiết hóa kế hoạch xây dựng và hoàn thiện toàn bộ **8 hạng mục con** thuộc **Mục 3.1: Lesson Dashboard (Bảng điều khiển bài học)** của dự án **EnglishMate**.

> [!IMPORTANT]
> **Cam kết thiết kế**: Giữ nguyên 100% design, màu sắc, font chữ (`Manrope`), layout, spacing và UI/UX hiện tại của hệ thống. Tái sử dụng tối đa các component Bootstrap 5, stat card, progress bar, badge và CSS utility sẵn có.

---

## 1. Mục tiêu & Phạm vi (Scope of Work)

Hoàn thiện đầy đủ 8 hạng mục con thuộc Mục 3.1:

1. **[x] Total lessons count display**: Hiển thị tổng số lượng bài học có trong hệ thống.
2. **[x] Completed lessons count**: Số lượng bài học học viên đã học hoàn thành thành công.
3. **[x] In-progress lessons count**: Số lượng bài học đang trong quá trình thực hành / xem dở.
4. **[x] Lesson progress by level**: Tiến độ hoàn thành bài học chi tiết phân chia theo các Cấp độ (A1, A2, B1, B2, C1, C2).
5. **[x] Lesson progress by skill**: Tiến độ hoàn thành bài học chi tiết phân chia theo các Kỹ năng (Grammar, Vocabulary, Reading, Listening, Speaking).
6. **[x] Current lesson display**: Thẻ nổi bật hiển thị bài học hiện tại mà học viên đang học dở hoặc vừa truy cập gần đây.
7. **[x] Recommended next lesson**: Thẻ đề xuất bài học tiếp theo phù hợp nhất với trình độ và tiến độ học hiện tại.
8. **[x] Daily lesson goal**: Mục tiêu hoàn thành bài học hàng ngày (ví dụ: 1/2 bài hôm nay) kèm thanh phần trăm tiến độ.

---

## 2. Các thay đổi Kiến trúc & Mã nguồn

### 2.1. Controller & Analytics Logic (`app/modules/learning/routes.py`)
- Cập nhật controller `GET /learning/lessons`:
  - **Lesson Counters**: Tổng số bài (`total_lessons`), số bài hoàn thành (`completed_count`), số bài đang học (`in_progress_count`).
  - **Level Progress Breakdown**: Phần trăm hoàn thành bài học theo từng cấp độ A1, A2, B1, B2, C1, C2.
  - **Skill Progress Breakdown**: Phần trăm hoàn thành bài học theo từng kỹ năng Grammar, Vocabulary, Reading, Listening, Speaking.
  - **Current Lesson**: Lấy bài học gần đây nhất học viên vừa xem/học.
  - **Recommended Next Lesson**: Tự động gợi ý bài học tiếp theo chưa hoàn thành ở cấp độ/kỹ năng tương ứng.
  - **Daily Lesson Goal**: Thống kê số bài học đã hoàn thành hôm nay so với mục tiêu hàng ngày (Mặc định 2 bài/ngày).

### 2.2. Giao diện Người dùng (`app/templates/learning/lessons.html`)
Nâng cấp trang Bảng điều khiển Bài học với layout chuẩn UI/UX EnglishMate:
- **Thẻ Thống kê Tổng quan (Metric Grid Cards)**: Tổng số bài, Bài đã hoàn thành, Bài đang học, Bài học đề xuất.
- **Khối Bài học Hiện tại & Bài học Đề xuất Tiếp theo (Current & Recommended Card)**: 2 thẻ nổi bật dẫn trực tiếp tới bài học.
- **Thanh Tiến độ Mục tiêu Bài học Hàng ngày (Daily Lesson Goal)**: Tiến trình hoàn thành bài học hôm nay.
- **Phân tích Tiến độ theo Cấp độ & Kỹ năng (Level & Skill Breakdown)**: Các thanh progress bar hiển thị phần trăm tiến độ từng level và kỹ năng.
- **Thanh Công cụ Lọc & Danh sách Bài học (Lesson Library Grid)**: Danh sách thẻ bài học với bộ lọc Level & Kỹ năng.

---

## 3. Kế hoạch Kiểm thử & Xác nhận (Verification Plan)

### Automated Tests (`tests/test_lesson_dashboard.py`)
1. Test truy cập giao diện Bảng điều khiển bài học `/learning/lessons`.
2. Test tính toán chính xác số lượng bài học (Total, Completed, In-progress).
3. Test phân tích tiến độ bài học theo Level (A1-C2) và Skill (Grammar, Reading, v.v.).
4. Test trích xuất Bài học hiện tại & Bài học đề xuất tiếp theo.
5. Test ghi nhận tiến độ mục tiêu bài học hàng ngày.

### Manual Verification
1. Truy cập `/learning/lessons`.
2. Kiểm tra các thẻ thống kê tổng số bài, bài đã hoàn thành và bài học đang học.
3. Kiểm tra các thanh tiến độ theo Cấp độ (A1-C2) và Kỹ năng (Grammar, Reading...).
4. Bấm "Bắt đầu học" tại thẻ Bài học Đề xuất tiếp theo ➔ Hoàn thành bài ➔ Quay lại kiểm tra các chỉ số tăng tương ứng.

---

# Kế hoạch Triển khai Tính năng 3.2: Lesson List (Danh sách bài học)

Tài liệu này chi tiết hóa kế hoạch xây dựng và hoàn thiện toàn bộ **15 hạng mục con** thuộc **Mục 3.2: Lesson List (Danh sách bài học)** của dự án **EnglishMate**.

> [!IMPORTANT]
> **Cam kết thiết kế**: Giữ nguyên 100% design, màu sắc, font chữ (`Manrope`), layout, spacing và UI/UX hiện tại của hệ thống. Tái sử dụng tối đa các component Bootstrap 5, card, thumbnail, modal, badge và CSS utility sẵn có.

---

## 1. Mục tiêu & Phạm vi (Scope of Work)

Hoàn thiện đầy đủ 15 hạng mục con thuộc Mục 3.2:

1. **[x] Browse lessons by level (A1-C2)**: Duyệt bài học trực quan theo từng Cấp độ CEFR (A1, A2, B1, B2, C1, C2).
2. **[x] Browse lessons by skill (Grammar/Vocabulary/Reading/Listening/Speaking)**: Duyệt bài học theo từng Kỹ năng trọng tâm.
3. **[x] Search lessons by title**: Tìm kiếm bài học chính xác theo tiêu đề.
4. **[x] Search lessons by content**: Tìm kiếm bài học theo nội dung chi tiết hoặc mô tả tóm tắt.
5. **[x] Filter by level**: Bộ lọc bài học theo Cấp độ.
6. **[x] Filter by skill**: Bộ lọc bài học theo Kỹ năng.
7. **[x] Filter by status (New/In Progress/Completed)**: Bộ lọc trạng thái bài học (Bài mới chưa học, Bài đang học dở, Bài đã hoàn thành).
8. **[x] Sort by difficulty**: Sắp xếp bài học theo độ khó (A1 ➔ C2 hoặc C2 ➔ A1).
9. **[x] Sort by popularity**: Sắp xếp bài học theo độ phổ biến (lượt xem / lượt học nhiều nhất).
10. **[x] Sort by recent**: Sắp xếp bài học mới nhất vừa được thêm vào hệ thống.
11. **[x] Lesson list view with thumbnails**: Chế độ hiển thị danh sách bài học kèm hình ảnh thu nhỏ thumbnail chất lượng cao.
12. **[x] Lesson detail preview**: Modal xem trước chi tiết bài học (Mô tả, cấp độ, kỹ năng, nội dung xem trước).
13. **[x] Mark lesson as favorite**: Đánh dấu thả tim bài học yêu thích (`LessonFavorite`).
14. **[x] Start lesson button**: Nút "Bắt đầu học" nổi bật dành cho bài học mới.
15. **[x] Continue lesson button**: Nút "Tiếp tục học" / "Xem lại" dành cho bài học đang học dở hoặc đã học xong.

---

## 2. Các thay đổi Kiến trúc & Mã nguồn

### 2.1. Cơ sở dữ liệu & Model (`app/modules/learning/models.py` & `patch_db.py`)
- Cập nhật model `Lesson`:
  - `thumbnail_url`: String(255) - Đường dẫn ảnh thu nhỏ của bài học.
  - `view_count`: Integer (default=0) - Số lượt truy cập bài học để phục vụ sắp xếp theo độ phổ biến.
- Tạo mới model `LessonFavorite`:
  - `id`, `user_id`, `lesson_id`, `created_at`.
- Cập nhật script `patch_db.py`:
  - Tự động bổ sung các cột `thumbnail_url` và `view_count` vào bảng `lesson`.
  - Tự động tạo bảng `lesson_favorite`.

### 2.2. Controller & API Routes (`app/modules/learning/routes.py`)
- Route `GET /learning/lessons/list`: Trang Danh sách bài học nâng cao hỗ trợ bộ tìm kiếm tiêu đề & nội dung (`q`), lọc Level, Skill, Status (New, In Progress, Completed), sắp xếp Độ khó, Phổ biến, Mới nhất.
- Route `POST /learning/lessons/<id>/favorite`: API toggle trạng thái yêu thích bài học.
- Route `GET /learning/lessons/<id>/preview`: API / Modal trả về dữ liệu xem trước chi tiết bài học.

### 2.3. Giao diện Người dùng (`app/templates/learning/lessons_list.html` & `app/templates/learning/lessons.html`)
- **Thanh Tìm kiếm & Bộ lọc Đa năng**: Tìm theo Tiêu đề/Nội dung, Duyệt nhanh theo Level tabs & Skill tabs, Bộ lọc trạng thái (Mới, Đang học, Đã xong), Bộ sắp xếp (Độ khó, Phổ biến, Mới nhất).
- **Danh sách Bài học Thumbnail (Grid / Card List)**: Hiển thị bài học với Thumbnail đẹp mắt, Badge Level & Skill, nút Thả tim ❤️, nút Xem trước 👁️.
- **Nút Hành động Động (Contextual Action Button)**: Tự động thay đổi giữa "Bắt đầu học" (nút Primary màu xanh) và "Tiếp tục học / Xem lại" (nút Secondary / Success).
- **Modal Xem trước Chi tiết Bài học (Lesson Preview Modal)**: Modal hiển thị xem trước tóm tắt bài học.

---

## 3. Kế hoạch Kiểm thử & Xác nhận (Verification Plan)

### Automated Tests (`tests/test_lesson_list.py`)
1. Test duyệt danh sách bài học `/learning/lessons/list`.
2. Test tìm kiếm theo tiêu đề & nội dung bài học.
3. Test lọc theo Level, Skill, Status (New, In Progress, Completed).
4. Test sắp xếp theo Độ khó, Phổ biến, Mới nhất.
5. Test tính năng Đánh dấu bài học yêu thích (Favorite Toggle).
6. Test nút Bắt đầu học & Tiếp tục học.

### Manual Verification
1. Truy cập `/learning/lessons/list`.
2. Thử tìm kiếm từ khóa "Present Simple", lọc Level A1, Skill Grammar, Status New, Sắp xếp Phổ biến.
3. Nhấp vào nút Thả tim ❤️ trên bài học ➔ Kiểm tra trạng thái yêu thích.
4. Bấm "Xem trước 👁️" ➔ Kiểm tra hiển thị Modal thông tin chi tiết bài học.
5. Bấm "Bắt đầu học" ➔ Chuyển sang bài học ➔ Đánh dấu hoàn thành ➔ Quay lại trang danh sách bài học kiểm tra nút đổi thành "Xem lại ✓".

---

# Kế hoạch Triển khai Tính năng 3.3: Lesson Content (Nội dung bài học)

Tài liệu này chi tiết hóa kế hoạch xây dựng và hoàn thiện toàn bộ **16 hạng mục con** thuộc **Mục 3.3: Lesson Content (Nội dung bài học)** của dự án **EnglishMate**.

> [!IMPORTANT]
> **Cam kết thiết kế**: Giữ nguyên 100% design, màu sắc, font chữ (`Manrope`), layout, spacing và UI/UX hiện tại của hệ thống. Tái sử dụng tối đa các component Bootstrap 5, progress bar, section card, modal, badge và CSS utility sẵn có.

---

## 1. Mục tiêu & Phạm vi (Scope of Work)

Hoàn thiện đầy đủ 16 hạng mục con thuộc Mục 3.3:

1. **[x] Display lesson title**: Hiển thị tiêu đề bài học.
2. **[x] Display lesson description**: Hiển thị mô tả bài học tóm tắt.
3. **[x] Display lesson level**: Badge cấp độ bài học (A1-C2).
4. **[x] Display lesson skill**: Badge kỹ năng bài học (Grammar, Reading...).
5. **[x] Display lesson content**: Hiển thị nội dung lý thuyết chính của bài học.
6. **[x] Display lesson examples**: Hiển thị các ví dụ minh họa thực tế.
7. **[x] Display lesson explanations**: Hiển thị phần giải thích bổ trợ chuyên sâu.
8. **[x] Section-by-section navigation**: Điều hướng chia bài học thành từng phần (Section 1: Lý thuyết, Section 2: Ví dụ & Giải thích, Section 3: Thực hành & Ghi nhớ).
9. **[x] Progress indicator within lesson**: Thanh chỉ số tiến độ % đọc bài học theo từng phần.
10. **[x] Next section button**: Nút chuyển sang "Phần tiếp theo →".
11. **[x] Previous section button**: Nút quay lại "← Phần trước".
12. **[x] Complete lesson button**: Nút "✓ Đánh dấu hoàn thành bài học".
13. **[x] Add lesson notes**: Cho phép học viên ghi chép ghi chú cá nhân trong bài học (`LessonNote`).
14. **[x] Bookmark section**: Đánh dấu lưu bookmark 🔖 các phần quan trọng trong bài (`LessonBookmark`).
15. **[x] Share lesson button**: Nút chia sẻ bài học 🔗 kèm tính năng sao chép liên kết.
16. **[x] Report lesson content**: Gửi báo cáo góp ý / báo lỗi nội dung bài học 🚩 (`LessonReport`).

---

## 2. Các thay đổi Kiến trúc & Mã nguồn

### 2.1. Cơ sở dữ liệu & Models (`app/modules/learning/models.py` & `patch_db.py`)
- [NEW] Model `LessonNote`:
  - `id`, `user_id`, `lesson_id`, `content`, `updated_at`.
- [NEW] Model `LessonBookmark`:
  - `id`, `user_id`, `lesson_id`, `section_index`, `created_at`.
- [NEW] Model `LessonReport`:
  - `id`, `user_id`, `lesson_id`, `reason`, `details`, `status`, `created_at`.
- Cập nhật `patch_db.py`:
  - Tự động tạo các bảng `lesson_note`, `lesson_bookmark`, `lesson_report` trong SQLite database.

### 2.2. Controller & API Routes (`app/modules/learning/routes.py`)
- Cập nhật `GET /learning/lessons/<int:lesson_id>`:
  - Chia tách nội dung thành các Sections.
  - Lấy thông tin ghi chú cá nhân (`user_note`), các vị trí bookmarks (`bookmarks`), trạng thái hoàn thành.
- Route `POST /learning/lessons/<int:lesson_id>/notes`: Lưu/Cập nhật ghi chú cá nhân cho bài học.
- Route `POST /learning/lessons/<int:lesson_id>/bookmark`: Toggle lưu bookmark vị trí phần học.
- Route `POST /learning/lessons/<int:lesson_id>/report`: Gửi báo cáo lỗi/góp ý nội dung bài học.

### 2.3. Giao diện Người dùng (`app/templates/learning/lesson_detail.html`)
- **Header Bài học**: Tiêu đề, Mô tả, Badge Level, Skill, Nút "🔗 Chia sẻ", Nút "🚩 Báo cáo".
- **Thanh Tiến độ Bài học (Reading Progress Bar)**: Hiển thị chỉ số phần trăm tiến độ % đọc bài học (ví dụ: Phần 1/3 - 33%, Phần 2/3 - 67%, Phần 3/3 - 100%).
- **Hệ thống Section Tabs / Step Navigation**:
  - Section 1: Lý thuyết & Nội dung trọng tâm.
  - Section 2: Ví dụ minh họa & Giải thích chi tiết.
  - Section 3: Ghi chú cá nhân & Đánh giá bài học.
- **Nút Điều hướng Phần**: "← Phần trước" & "Phần tiếp theo →" & "✓ Đánh dấu hoàn thành bài học".
- **Khối Ghi chú Cá nhân**: Ô nhập văn bản lưu ghi chú cá nhân theo thời gian thực.
- **Modals**:
  - Modal Chia sẻ bài học (kèm sao chép link).
  - Modal Báo cáo nội dung bài học.

---

## 3. Kế hoạch Kiểm thử & Xác nhận (Verification Plan)

### Automated Tests (`tests/test_lesson_content.py`)
1. Test hiển thị đầy đủ chi tiết bài học `/learning/lessons/<id>`.
2. Test chuyển đổi các Section trong bài học.
3. Test lưu và đọc ghi chú bài học (`LessonNote`).
4. Test bookmark vị trí phần bài học (`LessonBookmark`).
5. Test gửi báo cáo lỗi nội dung bài học (`LessonReport`).
6. Test đánh dấu hoàn thành bài học.

### Manual Verification
1. Truy cập bài học `/learning/lessons/1`.
2. Chuyển từ Section 1 sang Section 2 và Section 3 ➔ Kiểm tra thanh phần trăm tiến độ nhảy 33% ➔ 67% ➔ 100%.
3. Nhập ghi chú cá nhân và nhấn "Lưu ghi chú" ➔ F5 kiểm tra ghi chú hiển thị lại đúng nội dung.
4. Nhấn nút "🔗 Chia sẻ" ➔ Kiểm tra Modal hiển thị và chép link thành công.
5. Nhấn nút "🚩 Báo cáo nội dung" ➔ Nhập lý do và gửi ➔ Kiểm tra thông báo thành công.
6. Bấm "✓ Đánh dấu hoàn thành bài học" ➔ Đảm bảo hệ thống lưu tiến độ thành công.

---

# Kế hoạch Triển khai Tính năng 3.4: Grammar Learning (Học ngữ pháp)

Tài liệu này chi tiết hóa kế hoạch xây dựng và hoàn thiện toàn bộ **12 hạng mục con** thuộc **Mục 3.4: Grammar Learning (Học ngữ pháp)** của dự án **EnglishMate**.

> [!IMPORTANT]
> **Cam kết thiết kế**: Giữ nguyên 100% design, màu sắc, font chữ (`Manrope`), layout, spacing và UI/UX hiện tại của hệ thống. Tái sử dụng tối đa các component Bootstrap 5, card, alert, accordion, badge và CSS utility sẵn có.

---

## 1. Mục tiêu & Phạm vi (Scope of Work)

Hoàn thiện đầy đủ 12 hạng mục con thuộc Mục 3.4:

1. **[x] Grammar topics overview**: Bảng tổng quan tất cả chủ đề ngữ pháp kèm các thẻ thống kê số lượng & tiến độ học.
2. **[x] Browse grammar by category**: Duyệt chủ đề ngữ pháp theo Danh mục (Các thì, Cấu trúc câu, Động từ khuyết thiếu, Mệnh đề, Danh từ/Tính từ...).
3. **[x] Search grammar topics**: Tìm kiếm chủ đề ngữ pháp theo từ khóa tiêu đề hoặc nội dung.
4. **[x] Filter by level**: Lọc chủ đề ngữ pháp theo Cấp độ (A1, A2, B1, B2, C1, C2).
5. **[x] Filter by difficulty**: Lọc chủ đề ngữ pháp theo Độ khó (Easy, Medium, Hard).
6. **[x] Grammar rule explanation**: Giải thích công thức và quy tắc ngữ pháp chi tiết.
7. **[x] Grammar examples with explanations**: Ví dụ ngữ pháp thực tế kèm giải thích phân tích.
8. **[x] Common mistakes**: Khối cảnh báo các Lỗi ngữ pháp thường gặp & cách khắc phục.
9. **[x] Tips and tricks**: Các Mẹo ghi nhớ & thủ thuật áp dụng ngữ pháp nhanh chóng.
10. **[x] Related topics links**: Liên kết giới thiệu các Chủ đề ngữ pháp liên quan.
11. **[x] Mark topic as complete**: Đánh dấu hoàn thành chủ đề ngữ pháp.
12. **[x] Add topic to favorites**: Đánh dấu thả tim chủ đề ngữ pháp yêu thích.

---

## 2. Các thay đổi Kiến trúc & Mã nguồn

### 2.1. Cơ sở dữ liệu & Models (`app/modules/learning/models.py` & `patch_db.py`)
- [NEW] Model `GrammarTopic`:
  - `id`, `title`, `category`, `level`, `difficulty`, `summary`, `rule_explanation`, `examples_json`, `common_mistakes`, `tips_tricks`, `related_topic_ids`, `is_active`, `created_at`, `updated_at`.
- [NEW] Model `GrammarProgress`:
  - `id`, `user_id`, `topic_id`, `is_completed`, `is_favorite`, `completed_at`, `updated_at`.
- Cập nhật `patch_db.py`:
  - Tự động tạo các bảng `grammar_topic` và `grammar_progress` trong SQLite database.

### 2.2. Controller & Routes (`app/modules/learning/routes.py`)
- `GET /learning/grammar`: Trang Tổng quan & Thư viện chủ đề ngữ pháp.
  - Hỗ trợ Tìm kiếm (`q`), Lọc theo Category, Level (A1-C2), Difficulty (Easy/Medium/Hard).
  - Trích xuất tiến độ học (Số bài đã hoàn thành, bài đã yêu thích).
- `GET /learning/grammar/<int:topic_id>`: Trang Chi tiết nội dung ngữ pháp.
  - Hiển thị Công thức, Ví dụ giải thích, Lỗi thường gặp, Mẹo ghi nhớ, Chủ đề liên quan.
- `POST /learning/grammar/<int:topic_id>/complete`: Toggle đánh dấu hoàn thành bài học ngữ pháp.
- `POST /learning/grammar/<int:topic_id>/favorite`: Toggle thêm vào danh sách yêu thích.

### 2.3. Giao diện Người dùng (Templates HTML)
- [NEW] `app/templates/learning/grammar.html`: Trang Tổng quan Thư viện Ngữ pháp với các thẻ Metric, bộ lọc Category pills, bộ lọc Level/Difficulty và danh sách Card chủ đề.
- [NEW] `app/templates/learning/grammar_detail.html`: Trang Bài học Ngữ pháp chi tiết với Khối Công thức (Formula Card), Ví dụ thực tế (Examples List), Khối Lỗi thường gặp (Common Mistakes Alert Box), Khối Mẹo ghi nhớ (Tips Callout Card) và Các chủ đề liên quan (Related Topics Cards).

---

## 3. Kế hoạch Kiểm thử & Xác nhận (Verification Plan)

### Automated Tests (`tests/test_grammar_learning.py`)
1. Test truy cập trang tổng quan ngữ pháp `/learning/grammar`.
2. Test tìm kiếm và lọc chủ đề theo Category, Level, Difficulty.
3. Test xem chi tiết chủ đề ngữ pháp `/learning/grammar/<id>`.
4. Test đánh dấu hoàn thành bài ngữ pháp.
5. Test thả tim bài ngữ pháp yêu thích.

### Manual Verification
1. Truy cập `/learning/grammar`.
2. Lọc theo Danh mục "Tenses", Cấp độ "A1", Độ khó "Easy".
3. Nhấp xem chi tiết bài "Thì Hiện Tại Đơn".
4. Kiểm tra hiển thị công thức, ví dụ giải thích, khối cảnh báo Lỗi thường gặp và Mẹo ghi nhớ.
5. Bấm "✓ Đánh dấu hoàn thành" và "❤️ Yêu thích" ➔ Kiểm tra dữ liệu cập nhật chính xác.

---

# Kế hoạch Triển khai Tính năng 3.5: Grammar Exercises (Bài tập ngữ pháp)

Tài liệu này chi tiết hóa kế hoạch xây dựng và hoàn thiện toàn bộ **23 hạng mục con** thuộc **Mục 3.5: Grammar Exercises (Bài tập ngữ pháp)** của dự án **EnglishMate**.

> [!IMPORTANT]
> **Cam kết thiết kế**: Giữ nguyên 100% design, màu sắc, font chữ (`Manrope`), layout, spacing và UI/UX hiện tại của hệ thống. Tái sử dụng tối đa các component Bootstrap 5, timer card, progress bar, quiz option pills, modal, alert và CSS utility sẵn có.

---

## 1. Mục tiêu & Phạm vi (Scope of Work)

Hoàn thiện đầy đủ 23 hạng mục con thuộc Mục 3.5:

1. **[x] Exercise list by topic**: Danh sách bài tập ngữ pháp phân chia theo chủ đề.
2. **[x] Exercise difficulty selector**: Tùy chọn độ khó bài tập (Easy, Medium, Hard, Tất cả).
3. **[x] Question count selector**: Tùy chọn số lượng câu hỏi thực hành (5, 10, 15, 20 câu).
4. **[x] Start exercise button**: Nút "Bắt đầu bài tập".
5. **[x] Display grammar question**: Hiển thị văn bản câu hỏi ngữ pháp kèm vị trí khuyết `___`.
6. **[x] Display answer options**: Hiển thị 4 lựa chọn đáp án A, B, C, D.
7. **[x] Select answer button**: Nút chọn đáp án cho từng câu hỏi.
8. **[x] Submit answer button**: Nút nộp câu trả lời / kiểm tra đáp án.
9. **[x] Show correct answer**: Hiển thị đáp án chính xác sau khi nộp/xem lại.
10. **[x] Show detailed explanation**: Hiển thị phần giải thích chi tiết cho từng câu hỏi.
11. **[x] Show grammar rule reference**: Khối tham chiếu quy tắc ngữ pháp tương ứng.
12. **[x] Related examples**: Hiển thị các ví dụ minh họa liên quan.
13. **[x] Next question button**: Nút chuyển sang câu hỏi tiếp theo.
14. **[x] Previous question button**: Nút quay lại câu hỏi trước đó.
15. **[x] Mark for review**: Nút cờ 🚩 đánh dấu câu hỏi cần xem lại trước khi nộp bài.
16. **[x] Exercise timer**: Đồng hồ đếm ngược / đếm thời gian làm bài thực tế.
17. **[x] Exercise progress bar**: Thanh chỉ số phần trăm tiến độ làm bài (ví dụ: Câu 3/10 - 30%).
18. **[x] Submit exercise**: Nộp toàn bộ bài tập và chấm điểm tự động.
19. **[x] Exercise summary**: Giao diện tổng kết kết quả bài tập sau khi hoàn thành.
20. **[x] Score display**: Hiển thị điểm số, số câu đúng/sai, phần trăm chính xác %.
21. **[x] Incorrect answers review**: Danh sách xem lại các câu trả lời sai kèm đáp án đúng & giải thích.
22. **[x] Add to error log**: Tự động lưu các câu làm sai vào Nhật ký lỗi ngữ pháp (`GrammarErrorLog`).
23. **[x] Retry incorrect answers**: Nút "Thử lại các câu sai" để rèn luyện lại ngay lập tức.

---

## 2. Các thay đổi Kiến trúc & Mã nguồn

### 2.1. Cơ sở dữ liệu & Models (`app/modules/learning/models.py` & `patch_db.py`)
- [NEW] Model `GrammarExerciseAttempt`:
  - `id`, `user_id`, `topic_id`, `difficulty`, `question_count`, `score`, `total_questions`, `duration_seconds`, `completed_at`.
- [NEW] Model `GrammarErrorLog`:
  - `id`, `user_id`, `question_id`, `user_answer`, `correct_answer`, `is_resolved`, `created_at`, `updated_at`.
- Cập nhật `patch_db.py`:
  - Tự động tạo các bảng `grammar_exercise_attempt` và `grammar_error_log` trong SQLite database.

### 2.2. Controller & Routes (`app/modules/learning/routes.py`)
- `GET /learning/grammar/exercises`: Trang Thiết lập & Chọn bài tập ngữ pháp (Lựa chọn Topic, Difficulty, Question Count: 5/10/15/20).
- `POST /learning/grammar/exercises/start`: Khởi tạo phiên bài tập.
- `GET /learning/grammar/exercises/do`: Màn hình giao diện làm bài tập tương tác (Display Question, Options A/B/C/D, Next/Prev, Mark for Review 🚩, Timer, Progress Bar, Rule Reference Toggle).
- `POST /learning/grammar/exercises/submit`: Nộp bài tập ➔ Chấm điểm, tính thời gian, lưu `GrammarExerciseAttempt`, tự động lưu các câu sai vào `GrammarErrorLog`.
- `GET /learning/grammar/exercises/summary/<int:attempt_id>`: Trang Bảng tổng kết kết quả bài tập (Score Display, Incorrect Answers Review, Add to Error Log, Retry Button).
- `GET & POST /learning/grammar/exercises/retry/<int:attempt_id>`: Chế độ Thử lại riêng cho các câu làm sai ở lần tập trước.

### 2.3. Giao diện Người dùng (Templates HTML)
- [NEW] `app/templates/learning/grammar_exercises_setup.html`: Giao diện thiết lập bài tập (Chọn chủ đề, độ khó, số câu).
- [NEW] `app/templates/learning/grammar_exercises_do.html`: Màn hình tương tác làm bài tập ngữ pháp với Timer đếm thời gian, Progress bar, cờ Mark review 🚩, tham chiếu quy tắc ngữ pháp.
- [NEW] `app/templates/learning/grammar_exercises_summary.html`: Màn hình Tổng kết điểm số, Xem lại các câu sai kèm giải thích & Nút "Thử lại các câu sai".

---

## 3. Kế hoạch Kiểm thử & Xác nhận (Verification Plan)

### Automated Tests (`tests/test_grammar_exercises.py`)
1. Test truy cập giao diện thiết lập bài tập ngữ pháp `/learning/grammar/exercises`.
2. Test khởi tạo phiên làm bài tập với tùy chọn 5/10 câu, độ khó Easy/Medium/Hard.
3. Test chọn đáp án, chuyển câu hỏi, đánh dấu cờ review và đếm ngược thời gian.
4. Test nộp bài tập, tính toán điểm số và lưu nhật ký lỗi (`GrammarErrorLog`).
5. Test giao diện tổng kết, xem lại câu sai và chế độ thử lại câu sai.

### Manual Verification
1. Truy cập `/learning/grammar/exercises`.
2. Chọn chủ đề "Thì Hiện Tại Đơn", độ khó "Easy", số lượng "5 câu" ➔ Bấm "Bắt đầu bài tập".
3. Làm bài: Chọn đáp án A/B/C/D cho các câu, bấm cờ 🚩 xem lại ở câu 2, dùng nút "Phần tiếp theo" & "Phần trước đó".
4. Bấm "Nộp bài tập" ➔ Kiểm tra hiển thị màn hình Tổng kết với điểm số %, thời gian làm bài, danh sách xem lại câu sai.
5. Bấm "Thử lại các câu sai" ➔ Đảm bảo chỉ xuất hiện lại các câu đã chọn sai ở lần tập trước.

---

# Kế hoạch Triển khai Tính năng 3.6: Grammar Reference (Tài liệu tham khảo ngữ pháp)

Tài liệu này chi tiết hóa kế hoạch xây dựng và hoàn thiện toàn bộ **11 hạng mục con** thuộc **Mục 3.6: Grammar Reference (Tài liệu tham khảo ngữ pháp)** của dự án **EnglishMate**.

> [!IMPORTANT]
> **Cam kết thiết kế**: Giữ nguyên 100% design, màu sắc, font chữ (`Manrope`), layout, spacing và UI/UX hiện tại của hệ thống. Tái sử dụng tối đa các component Bootstrap 5, table, badge, modal, alert và CSS utility sẵn có.

---

## 1. Mục tiêu & Phạm vi (Scope of Work)

Hoàn thiện đầy đủ 11 hạng mục con thuộc Mục 3.6:

1. **[x] Grammar rules index**: Chỉ mục tổng hợp các quy tắc ngữ pháp phân loại rõ ràng.
2. **[x] Search grammar rules**: Ô tìm kiếm quy tắc ngữ pháp theo từ khóa nhanh chóng.
3. **[x] Browse by category (tenses, clauses, etc.)**: Duyệt quy tắc theo Danh mục (Các thì, Mệnh đề, Động từ, Tính từ, Danh từ, Dấu câu...).
4. **[x] Rule detail view**: Chế độ xem chi tiết nội dung quy tắc ngữ pháp.
5. **[x] Rule explanation**: Phần giải thích quy tắc chi tiết.
6. **[x] Examples**: Danh sách ví dụ thực tế minh họa quy tắc.
7. **[x] Exceptions**: Khối tổng hợp các Trường hợp Ngoại lệ (Exceptions) trong ngữ pháp.
8. **[x] Common errors**: Khối các Lỗi thường gặp (Common errors) và cách phòng tránh.
9. **[x] Quick reference tables**: Bảng tham khảo nhanh (Quick Reference Tables) dạng bảng tóm tắt ngắn gọn.
10. **[x] Bookmark rules**: Tính năng Bookmark 🔖 lưu quy tắc ngữ pháp quan trọng vào danh sách cá nhân.
11. **[x] Print-friendly view**: Chế độ xem & in ấn tối ưu (Print-friendly view) tích hợp CSS `@media print`.

---

## 2. Các thay đổi Kiến trúc & Mã nguồn

### 2.1. Cơ sở dữ liệu & Models (`app/modules/learning/models.py` & `patch_db.py`)
- [NEW] Model `GrammarRule`:
  - `id`, `title`, `category`, `summary`, `explanation`, `examples`, `exceptions`, `common_errors`, `quick_table_html`, `created_at`, `updated_at`.
- [NEW] Model `GrammarRuleBookmark`:
  - `id`, `user_id`, `rule_id`, `created_at`.
- Cập nhật `patch_db.py`:
  - Tự động tạo các bảng `grammar_rule` và `grammar_rule_bookmark` trong SQLite database.

### 2.2. Controller & Routes (`app/modules/learning/routes.py`)
- `GET /learning/grammar/reference`: Trang Chỉ mục Tra cứu Quy tắc Ngữ pháp (Tìm kiếm `q`, lọc theo `category`, bộ lọc `bookmarked_only`).
- `GET /learning/grammar/reference/<int:rule_id>`: Trang Chi tiết Quy tắc Ngữ pháp (Giải thích, Ví dụ, Ngoại lệ, Lỗi thường gặp, Bảng tham khảo nhanh, Nút Bookmark, Nút In).
- `POST /learning/grammar/reference/<int:rule_id>/bookmark`: Toggle Bookmark quy tắc ngữ pháp.
- `GET /learning/grammar/reference/<int:rule_id>/print`: Chế độ xem in ấn (Print-friendly View).

### 2.3. Giao diện Người dùng (Templates HTML)
- [NEW] `app/templates/learning/grammar_reference.html`: Chỉ mục tra cứu Quy tắc Ngữ pháp kèm bộ lọc Category & các Bảng tham khảo nhanh.
- [NEW] `app/templates/learning/grammar_rule_detail.html`: Chế độ xem chi tiết Quy tắc Ngữ pháp tích hợp Khối Ngoại lệ, Lỗi thường gặp, Bảng tóm tắt nhanh, Nút Bookmark & Nút In.
- [NEW] `app/templates/learning/grammar_rule_print.html`: Trang xem tối ưu dành riêng cho máy in (Print View).

---

## 3. Kế hoạch Kiểm thử & Xác nhận (Verification Plan)

### Automated Tests (`tests/test_grammar_reference.py`)
1. Test truy cập chỉ mục tra cứu ngữ pháp `/learning/grammar/reference`.
2. Test tìm kiếm từ khóa và lọc danh mục quy tắc.
3. Test xem chi tiết quy tắc `/learning/grammar/reference/<id>`.
4. Test bookmark quy tắc ngữ pháp.
5. Test giao diện in ấn `/learning/grammar/reference/<id>/print`.

### Manual Verification
1. Truy cập `/learning/grammar/reference`.
2. Tìm kiếm từ khóa "OSASCOMP" hoặc chọn danh mục "Adjectives".
3. Nhấp xem chi tiết bài quy tắc.
4. Kiểm tra hiển thị Giải thích, Ví dụ, Ngoại lệ, Lỗi thường gặp, Bảng tham khảo nhanh.
5. Nhấp nút Bookmark 🔖 ➔ Kiểm tra dữ liệu lưu thành công.
6. Nhấp nút "🖨️ In ấn" ➔ Kiểm tra giao diện in sạch sẽ chuẩn khổ giấy.