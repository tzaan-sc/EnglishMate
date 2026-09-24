# 📖 KỊCH BẢN TRIỂN KHAI GIAO DIỆN & TÍNH NĂNG
## CHUYÊN TRANG: ĐỌC HIỂU (READING) · ENGLISHMATE

> **Đường dẫn chuẩn danh mục:** `http://127.0.0.1:5000/reading`  
> **Đường dẫn chuẩn bài đọc:** `http://127.0.0.1:5000/reading/<id>` (Ví dụ: `http://127.0.0.1:5000/reading/18`)  
> **Nguyên tắc thiết kế:** Giao diện tinh gọn · Ít chữ, thoáng mắt · Đọc tập trung (Reader-Centric) · Đồng bộ 100% Hệ thống EnglishMate.

---

## I. NGUYÊN TẮC THIẾT KẾ & ĐỒNG BỘ HỆ THỐNG

### 1. Tối giản nội dung – Tránh rối mắt (Clean & Minimal UI)
- **Không nhồi nhét chữ ở danh mục:** Thẻ bài đọc chỉ hiển thị tiêu đề, thể loại văn bản, ước tính thời gian đọc (ví dụ: `⏱️ 3 phút · ~180 từ`) và mô tả ngắn tối đa 2 dòng.
- **Bố cục thoáng đãng:** Giữ khoảng cách đệm rộng rãi (`padding`, `gap`), tỷ lệ lề trang chuẩn, dễ quan sát cả trên màn hình Desktop và Mobile.
- **Thao tác đơn giản:** Mỗi thẻ bài chỉ có 1 nút hành động chính duy nhất (`Vào đọc` hoặc `Đọc lại`) cùng nút yêu thích hình tim.

### 2. Đồng bộ Màu sắc theo Hệ thống (`app.css` & `dashboard`)
- **Nền Hero Banner Đọc Hiểu:** Deep Teal / Emerald gradient chuẩn hệ thống:  
  `linear-gradient(135deg, #0f766e 0%, #0d9488 50%, #14b8a6 100%)`.
- **Màu Kỹ năng Đọc (Reading Theme):** Teal (`#0d9488` / text `#0f766e`, nền badge nhẹ `rgba(13, 148, 136, 0.1)`, viền `#ccfbf1`).
- **Nút hành động chính (Primary CTA):** Xanh thương hiệu `--primary` (`#059669` / hover `#047857`).
- **Nền & Viền trung tính:** Nền tổng thể `--bg-canvas` (`#f8fafc`), bề mặt thẻ `--bg-surface` (`#ffffff`), đường viền mảnh `--border-light` (`#e2e8f0`).

### 3. Đồng bộ Icon chuẩn (Phosphor Icons - Chuẩn toàn hệ thống)
Chỉ sử dụng bộ icon Phosphor đã tích hợp sẵn trong toàn bộ dự án:
- `ph-bold ph-book-open-text` / `ph-fill ph-book-open-text`: Biểu tượng Kỹ năng Đọc hiểu (Sidebar, Hero Banner, Tabs).
- `ph-bold ph-timer`: Ước tính thời gian đọc văn bản (`⏱️ ~3 phút`).
- `ph-bold ph-file-text`: Thể loại bài đọc (Email, Postcard, News, Essay).
- `ph-bold ph-text-aa`: Trình điều chỉnh cỡ chữ khi đọc.
- `ph-bold ph-translate`: Xem giải nghĩa từ vựng / bản dịch gợi ý.
- `ph-bold ph-speaker-high`: Nghe giọng đọc bản ngữ bài văn (Text-to-Speech).
- `ph-bold ph-question`: Câu hỏi trắc nghiệm kiểm tra đọc hiểu.
- `ph-bold ph-check-circle`: Trạng thái hoàn thành bài học.
- `ph-bold ph-heart` / `ph-fill ph-heart`: Đánh dấu bài đọc yêu thích.
- `ph-bold ph-arrow-left`: Nút quay lại danh mục Đọc Hiểu.
- `ph-bold ph-arrow-right`: Nút chuyển sang bài đọc tiếp theo.

### 4. Chuẩn Hóa Cấu Trúc Đường Dẫn & Điều Hướng (Cực kỳ quan trọng)
- **Tuyệt đối không dùng tiền tố chung `/lessons/`**:
  - Trang danh mục Đọc Hiểu: `http://127.0.0.1:5000/reading` (tự động chuyển hướng từ `/lessons?skill=Reading`).
  - Trang bài đọc chi tiết: `http://127.0.0.1:5000/reading/<id>` (ví dụ: `http://127.0.0.1:5000/reading/18`).
- **Cơ chế chuyển tiếp tương thích (Auto-Redirect 302):**
  - Truy cập bất kỳ `/lessons/<reading_id>` sẽ tự động redirect sang `/reading/<reading_id>`.
- **Thanh Breadcrumb bên trong bài đọc:**
  - `Trang Chủ` (`/dashboard`) ➔ `Đọc Hiểu` (`/reading`) ➔ `[Level]` ➔ `[Tên bài]`
- **Nút Quay lại (Back button):**
  - `"Quay lại Đọc Hiểu"` trỏ chính xác về `http://127.0.0.1:5000/reading`.
- **Menu Sidebar:**
  - Mục `"Đọc Hiểu"` (`ph-bold ph-book-open-text text-teal`) liên kết trực tiếp `/reading`, sáng active khi đang ở đường dẫn bắt đầu bằng `/reading`.

---

## II. BỐ CỤC TỔNG THỂ 2 GIAO DIỆN (UI ARCHITECTURE)

### 1. Bố cục Giao diện Danh mục Đọc Hiểu (`/reading`)

```
┌────────────────────────────────────────────────────────────────────────┐
│ ZONE 1: HERO BANNER ĐỌC HIỂU (Chuẩn Deep Teal Gradient)               │
│ 📖 KỸ NĂNG ĐỌC HIỂU · READING                                          │
│ Rèn Luyện Tư Duy & Vốn Từ Qua Văn Bản            [📖 Tiếp tục bài: B2] │
│ ┌──────────────┬──────────────┬──────────────┬───────────────────────┐ │
│ │ 📚 12 bài đọc│ ✓ 4 đã đọc   │ 📈 33% xong  │ ⏱️ ~45 phút đọc       │ │
│ └──────────────┴──────────────┴──────────────┴───────────────────────┘ │
├────────────────────────────────────────────────────────────────────────┤
│ ZONE 2: BỘ LỌC TỐI GIẢN (1 CARD GỌN GÀNG)                              │
│ Kỹ năng: [Tất cả] [🎧 Luyện Nghe] [📖 Đọc Hiểu (Active)] [Nói] [Viết]  │
│ Bộ lọc: [Cấp độ: Tất cả / A1 / A2 / B1 / B2] [Thể loại] [Tìm kiếm 🔍]   │
├────────────────────────────────────────────────────────────────────────┤
│ ZONE 3: LƯỚI THẺ BÀI ĐỌC (THOÁNG ĐÃNG, TINH TẾ)                        │
│ ┌─────────────────────────┐  ┌─────────────────────────┐               │
│ │ [A1] Bưu thiếp    [♡]   │  │ [B2] Email công việc[♡] │ (Lưới 3 cột)  │
│ │ A Simple Postcard...    │  │ Professional Workplace..│               │
│ │ ⏱️ ~2 phút · 120 từ      │  │ ⏱️ ~4 phút · 280 từ      │               │
│ │ Đọc bưu thiếp chào mừng │  │ Đọc và phân tích email.. │               │
│ │ ─────────────────────── │  │ ─────────────────────── │               │
│ │ Chưa đọc       [Vào đọc]│  │ ✓ Đã xong      [Đọc lại]│               │
│ └─────────────────────────┘  └─────────────────────────┘               │
└────────────────────────────────────────────────────────────────────────┘
```

---

### 2. Bố cục Giao diện Chi tiết Bài Đọc (`/reading/<id>`)

```
┌────────────────────────────────────────────────────────────────────────┐
│ TOP BAR: BREADCRUMB & NÚT QUAY LẠI                                     │
│ Trang Chủ / Đọc Hiểu / A1 / A Simple Postcard from London              │
│ [← Quay lại Đọc Hiểu]                            [♡ Yêu thích] [Chia sẻ]│
├────────────────────────────────────────────────────────────────────────┤
│ SMART READING TOOLBAR (THANH ĐIỀU KHIỂN ĐỌC THÔNG MINH)                │
│ [Cỡ chữ: A- / A+] [🔊 Nghe đọc văn bản] [💡 Hiện nghĩa từ vựng]        │
├───────────────────────────────────┬────────────────────────────────────┤
│ CỘT TRÁI: VĂN BẢN BÀI ĐỌC (60%)   │ CỘT PHẢI: BÀI TẬP & TỪ KHÓA (40%)  │
│ ┌───────────────────────────────┐ │ [💡 Từ vựng] [❓ Câu hỏi] [📝 Ghi chú]│
│ │ 🏷️ Bưu thiếp · London (A1)    │ │ ┌────────────────────────────────┐ │
│ │                               │ │ │ 1. postcard (n): bưu thiếp     │ │
│ │ Dear Tom,                     │ │ │    /ˈpoʊst.kɑːrd/              │ │
│ │ Greetings from London! The    │ │ │ 2. lovely (adj): đáng yêu, đẹp │ │
│ │ weather is lovely today. We   │ │ │    /ˈlʌv.li/                   │ │
│ │ visited Big Ben and rode the  │ │ ├────────────────────────────────┤ │
│ │ London Eye. See you soon!     │ │ │ [✓ Hoàn thành bài đọc (+20 XP)]│ │
│ └───────────────────────────────┘ │ └────────────────────────────────┘ │
└───────────────────────────────────┴────────────────────────────────────┘
```

---

## III. CHI TIẾT TỪNG PHÂN VÙNG GIAO DIỆN

### 1. Trang Danh mục Đọc Hiểu (`/reading`)

#### A. Zone 1: Hero Banner (Deep Teal)
- **Tiêu đề:** `Đọc hiểu` kèm huy hiệu `KỸ NĂNG ĐỌC HIỂU · READING`.
- **Mô tả:** 1 dòng súc tích: *"Phát triển khả năng đọc hiểu, mở rộng vốn từ và ngữ cảnh qua các văn bản thực tế."*
- **Nút CTA tiếp tục:** `btn-light rounded-pill` trỏ trực tiếp đến bài đọc gần nhất `{{ next_lesson.url }}`.
- **4 Thẻ thống kê tinh gọn:**
  1. `ph-bold ph-book-open-text`: Tổng bài đọc (`12 bài`).
  2. `ph-bold ph-check-circle`: Đã hoàn thành (`4 bài`).
  3. `ph-bold ph-chart-line-up`: Tỷ lệ hoàn thành (`33%`).
  4. `ph-bold ph-clock`: Thời gian đã đọc (`45 phút`).

#### B. Zone 2: Bộ lọc tối giản
- Hàng nút chọn nhanh Kỹ năng: `Tất cả`, `Luyện Nghe`, `Đọc Hiểu` (Active viền teal), `Luyện Nói`, `Luyện Viết`.
- Ô tìm kiếm từ khóa với icon `ph-bold ph-magnifying-glass`.
- Lọc theo Cấp độ CEFR: `A1`, `A2`, `B1`, `B2`, `C1`.
- Lọc theo Thể loại: `Tất cả thể loại`, `Bưu thiếp / Thư từ`, `Email công việc`, `Tin tức / Bài báo`, `Truyện ngắn`.

#### C. Zone 3: Thẻ bài đọc (Reading Cards)
Mỗi thẻ bài được thiết kế thoáng mắt, tối giản hóa:
1. **Header thẻ:**
   - Badge Cấp độ: `A1` (nền `bg-primary-subtle text-primary`).
   - Badge Thể loại: `Bưu thiếp` hoặc `Email` (nền `bg-teal-subtle text-teal`).
   - Nút thả tim yêu thích: `ph-bold ph-heart`.
2. **Tiêu đề & Thông số đọc:**
   - Tiêu đề in đậm, tối đa 1 dòng kèm link trực tiếp đến `{{ lesson.url }}` (ví dụ: `/reading/18`).
   - Thông số đọc nhanh: `⏱️ ~2 phút · ~120 từ` với icon `ph-bold ph-timer`.
3. **Mô tả ngắn:**
   - 2 dòng tóm lược nội dung (`-webkit-line-clamp: 2`).
4. **Footer thẻ:**
   - Trạng thái: `✓ Đã đọc` hoặc `Chưa đọc`.
   - Nút hành động: `Vào đọc` hoặc `Đọc lại` kèm icon `ph-bold ph-arrow-right` dẫn thẳng đến `{{ lesson.url }}`.

---

### 2. Trang Chi Tiết Bài Đọc (`/reading/<id>`)

#### A. Thanh điều hướng & Breadcrumb
- Đường dẫn chính xác: `Trang Chủ` (`/dashboard`) ➔ `Đọc Hiểu` (`/reading`) ➔ `[Level]` ➔ `[Tên bài]`
- Nút quay lại: `<a href="/reading" class="btn btn-light rounded-pill"> <i class="ph-bold ph-arrow-left"></i> Quay lại Đọc Hiểu </a>`

#### B. Thanh công cụ đọc thông minh (Smart Reading Toolbar)
Đặt ngay trên đầu văn bản bài đọc, bao gồm:
- **Bộ chỉnh cỡ chữ (`ph-bold ph-text-aa`):** 3 mức cỡ chữ: `16px` (Chuẩn), `18px` (Thoải mái), `20px` (Dễ nhìn) để người dùng đọc lâu không bị mỏi mắt.
- **Nút Nghe giọng đọc (`ph-bold ph-speaker-high`):** Hỗ trợ phát âm thanh toàn bài bằng Web Speech Synthesis bản ngữ giúp vừa đọc vừa luyện tai.
- **Nút Tra từ nhanh (`ph-bold ph-translate`):** Bật/tắt chế độ gạch chân từ vựng quan trọng trong bài đọc.

#### C. Khung Đọc Văn Bản (Reader Studio - Cột trái 60%)
- Định dạng thẻ nổi bật với giấy nền sáng dịu mắt (`#ffffff`), lề rộng, chữ màu than đậm (`#1e293b`), khoảng cách dòng rộng thoáng (`line-height: 1.85`).
- Tiêu đề bài văn + huy hiệu thể loại và cấp độ.
- Văn bản được trình bày theo từng đoạn rõ ràng. Nhấp đúp vào bất kỳ từ nào sẽ hiển thị popup nghĩa tiếng Việt nhanh.

#### D. Khu vực Bài tập & Tương tác (Cột phải 40%)
Chia làm 3 Tabs tinh gọn:
1. **Tab 1: 💡 Từ vựng then chốt (Key Vocabulary):**
   - Danh sách 3-5 từ vựng quan trọng nhất trong bài đọc kèm loại từ, phiên âm IPA, nghĩa tiếng Việt và ví dụ ngữ cảnh.
   - Nút bấm nghe phát âm từng từ riêng biệt.
2. **Tab 2: ❓ Câu hỏi đọc hiểu (Comprehension Check):**
   - 2-3 câu hỏi trắc nghiệm ngắn nhằm kiểm tra mức độ nắm bắt ý chính và chi tiết của bài đọc.
   - Chọn đáp án có phản hồi ngay (xanh lá nếu đúng kèm giải thích câu văn dẫn chứng, đỏ nếu sai).
3. **Tab 3: 📝 Ghi chú & Hoàn thành:**
   - Ô ghi chú mẹo học hoặc cấu trúc ngữ pháp cần nhớ.
   - Nút **"Đánh dấu đã đọc xong"** (`+20 XP` tích lũy và cập nhật tiến độ học tập).

---

## IV. ĐẶC TẢ KỸ THUẬT & CODE MINH HỌA

### 1. Template Thẻ Bài Đọc Chuẩn Hệ Thống (`lessons.html`)

```html
<!-- Thẻ bài đọc Đọc Hiểu: Gọn gàng, ít chữ, chuẩn đường dẫn /reading/<id> -->
<article class="card-modern p-3.5 h-100 d-flex flex-column justify-content-between position-relative transition-hover card-lesson-clickable"
         data-detail-url="{{ lesson.url }}">
  <div>
    <!-- Header thẻ: Level, Thể loại, Yêu thích -->
    <div class="d-flex justify-content-between align-items-center mb-2.5">
      <div class="d-flex align-items-center gap-1.5">
        <span class="badge bg-primary-subtle text-primary border border-primary-subtle rounded-pill px-2.5 py-0.5 fw-bold" style="font-size: 0.74rem;">
          {{ lesson.level }}
        </span>
        <span class="badge rounded-pill px-2 py-0.5 fw-semibold" style="font-size: 0.72rem; background-color: rgba(13, 148, 136, 0.1); color: #0f766e; border: 1px solid rgba(13, 148, 136, 0.2);">
          <i class="ph-bold ph-file-text me-0.5"></i>Bài đọc
        </span>
      </div>

      <button type="button" class="btn btn-link p-0 text-decoration-none shadow-none btn-fav-toggle" data-lesson-id="{{ lesson.id }}" title="Yêu thích">
        <i class="ph-bold ph-heart fs-5 {{ 'text-danger ph-fill' if lesson.id in favorite_ids else 'text-muted opacity-50' }}"></i>
      </button>
    </div>

    <!-- Tiêu đề & Thông số đọc -->
    <h6 class="fw-bold text-dark mb-1 line-clamp-1" style="font-size: 1rem;">
      <a href="{{ lesson.url }}" class="text-dark text-decoration-none hover-primary">
        {{ lesson.title }}
      </a>
    </h6>
    <div class="text-muted d-inline-flex align-items-center gap-1.5 mb-2.5" style="font-size: 0.76rem;">
      <i class="ph-bold ph-timer text-teal"></i>
      <span>~3 phút đọc</span>
      <span>•</span>
      <span>{{ lesson.content|length // 5 }} từ</span>
    </div>

    <!-- Mô tả vắn tắt 2 dòng -->
    <p class="text-secondary small mb-3" style="font-size: 0.84rem; line-height: 1.5; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;">
      {{ lesson.short_description }}
    </p>
  </div>

  <!-- Footer thẻ: Trạng thái & Nút Vào đọc -->
  <div class="pt-2.5 border-top border-light d-flex align-items-center justify-content-between mt-auto">
    {% if lesson.id in done %}
    <span class="badge bg-success-subtle text-success rounded-pill px-2 py-0.5 fw-bold" style="font-size: 0.72rem;">
      ✓ Đã đọc
    </span>
    {% else %}
    <span class="text-muted" style="font-size: 0.74rem;">Chưa đọc</span>
    {% endif %}

    <a href="{{ lesson.url }}" 
       class="btn btn-primary btn-sm rounded-pill px-3 py-1 fw-bold shadow-xs d-inline-flex align-items-center gap-1"
       style="font-size: 0.8rem;">
      <span>{{ 'Đọc lại' if lesson.id in done else 'Vào đọc' }}</span>
      <i class="ph-bold ph-arrow-right"></i>
    </a>
  </div>
</article>
```

### 2. Định Tuyến & Điều Hướng Trong Flask (`app/modules/learning/routes.py`)

Hệ thống đã tích hợp sẵn và cần bảo đảm liên kết chuẩn xác:
```python
# 1. Hub danh mục Đọc Hiểu:
@bp.get("/reading")
@login_required
def reading_hub():
    return redirect(url_for("learning.lessons", skill="Reading"))

# 2. Chi tiết bài đọc chuẩn:
@bp.get("/reading/<int:lesson_id>")
@login_required
def reading_detail(lesson_id):
    lesson = Lesson.query.filter_by(id=lesson_id, is_active=True).first_or_404()
    return _render_lesson_page(lesson)

# 3. Chuyển tiếp tự động từ URL cũ:
@bp.get("/lessons/<int:lesson_id>")
@login_required
def lesson_detail(lesson_id):
    lesson = Lesson.query.filter_by(id=lesson_id, is_active=True).first_or_404()
    skill_slug = (lesson.skill or "").lower()
    if skill_slug in ["listening", "reading", "speaking", "writing"]:
        return redirect(f"/{skill_slug}/{lesson.id}")
    return _render_lesson_page(lesson)
```

### 3. Đồng Bộ Mục "Đọc Hiểu" Trên Sidebar (`app/templates/_sidebar.html`)

```html
<!-- Mục Đọc Hiểu trên Menu Sidebar chính -->
<li class="nav-item">
  <a class="nav-link d-flex align-items-center gap-2.5 px-3 py-2 rounded-3 text-secondary text-decoration-none {% if request.path.startswith('/reading') or (request.endpoint == 'learning.lessons' and request.args.get('skill') == 'Reading') %}active bg-primary-subtle text-primary fw-bold{% endif %}"
     href="/reading">
    <i class="ph-bold ph-book-open-text fs-5 text-teal"></i>
    <span>Đọc Hiểu</span>
  </a>
</li>
```

---

## V. DANH SÁCH BÀI ĐỌC CÓ SẴN TRONG CƠ SỞ DỮ LIỆU ĐỂ KIỂM THỬ

Hệ thống hiện đã nạp sẵn các bài đọc thực tế trải dài từ cấp độ A1 đến C1:
1. **Bài 18 (A1):** *A Simple Postcard from London* ➔ `http://127.0.0.1:5000/reading/18`
2. **Bài 19 (A2):** *Hotel Services & Guest Information* ➔ `http://127.0.0.1:5000/reading/19`
3. **Bài 20 (B1):** *Reading for the Main Idea* ➔ `http://127.0.0.1:5000/reading/20`
4. **Bài 21 (B2):** *Professional Workplace Email* ➔ `http://127.0.0.1:5000/reading/21`
5. **Bài 22 (C1):** *Sustainable Energy & Future Cities* ➔ `http://127.0.0.1:5000/reading/22`

---

## VI. BẢNG KIỂM TRA ĐỒNG BỘ TRƯỚC KHI TRIỂN KHAI (CHECKLIST)

- [x] **URL & Breadcrumb chuẩn xác:**
  - Danh mục: `http://127.0.0.1:5000/reading`
  - Chi tiết bài đọc: `http://127.0.0.1:5000/reading/<id>` (không dùng `/lessons/<id>`).
  - Breadcrumb: `Trang Chủ` ➔ `Đọc Hiểu` (`/reading`) ➔ `[Level]` ➔ `[Tên bài]`.
  - Nút quay lại: `"Quay lại Đọc Hiểu"` dẫn về `/reading`.
- [x] **Giao diện thoáng & ít chữ:** Thẻ danh mục súc tích, mô tả 2 dòng, thông số thời gian đọc ngắn gọn.
- [x] **Màu sắc chuẩn hệ thống:** Deep Teal / Emerald gradient cho Hero, tông màu Teal (`#0d9488` / `#0f766e`) cho badge và điểm nhấn Đọc Hiểu, nút CTA xanh `--primary`.
- [x] **Icon Phosphor đồng bộ:** 100% icon từ thư viện Phosphor (`ph-book-open-text`, `ph-timer`, `ph-text-aa`, `ph-translate`, `ph-speaker-high`, `ph-heart`, `ph-arrow-right`).
- [x] **Tích hợp Sidebar:** Có mục "Đọc Hiểu" dẫn thẳng đến `/reading` với hiệu ứng active đồng bộ.
