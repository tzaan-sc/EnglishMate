# 🎧 KỊCH BẢN TRIỂN KHAI GIAO DIỆN & TÍNH NĂNG
## CHUYÊN TRANG: LUYỆN NGHE (LISTENING) · ENGLISHMATE
> **Đường dẫn:** `http://127.0.0.1:5000/lessons?skill=Listening`  
> **Nguyên tắc thiết kế:** Gọn gàng · Tối giản chữ (Clean UI) · Tập trung vào âm thanh (Audio-First) · Đồng bộ 100% Hệ thống.

---

## I. NGUYÊN TẮC THIẾT KẾ & ĐỒNG BỘ HỆ THỐNG

### 1. Tối giản nội dung – Tránh rối mắt (Minimal & Clean UI)
- **Không nhồi nhét chữ:** Thẻ bài học chỉ giữ tiêu đề, mô tả súc tích (tối đa 2 dòng), và thông số âm thanh cần thiết nhất.
- **Bố cục thoáng đãng:** Giữ khoảng cách đệm (`padding`, `gap`) rộng rãi, dễ quan sát trên cả máy tính và điện thoại.
- **Tập trung thao tác (Single Primary Action):** Mỗi thẻ bài chỉ có 1 nút phát nghe nhanh và 1 nút vào học chính, không dàn trải 3-4 nút phụ.

### 2. Đồng bộ Màu sắc theo Hệ thống (`app.css` & `dashboard`)
- **Nền Hero Banner:** `.hero-brand-card` (`linear-gradient(135deg, #064e3b 0%, #065f46 50%, #047857 100%)` - Deep Emerald).
- **Màu Kỹ năng Nghe (Listening):** `--warning` (`#f59e0b` / nền `--warning-subtle: #fffbeb`) đồng bộ với Dashboard.
- **Nút hành động chính (Primary CTA):** `--primary` (`#059669` / hover `#047857`).
- **Nền & Viền trung tính:** `--bg-canvas` (`#f8fafc`), `--bg-surface` (`#ffffff`), viền `--border-light` (`#e2e8f0`).

### 3. Đồng bộ Icon chuẩn (Phosphor Icons - Thống nhất toàn app)
Dùng chính xác các icon đang có trong hệ thống, không dùng icon lạ:
- `ph-bold ph-headphones`: Biểu tượng Kỹ năng Nghe (Sidebar, Hero, Tabs).
- `ph-fill ph-play` / `ph-fill ph-pause`: Nút phát / dừng âm thanh.
- `ph-bold ph-clock`: Thời lượng audio (đồng bộ với thẻ thống kê Hero).
- `ph-bold ph-arrow-counter-clockwise` / `ph-bold ph-arrow-clockwise`: Tua lùi / tiến 5 giây.
- `ph-bold ph-magnifying-glass`: Tìm kiếm bài học.
- `ph-bold ph-heart` / `ph-fill ph-heart`: Yêu thích bài học.
- `ph-bold ph-eye`: Xem trước nội dung bài.
- `ph-bold ph-arrow-right`: Nút vào học / ôn tập.
- `ph-bold ph-x`: Đóng trình phát hoặc xóa bộ lọc.

---

## II. BỐ CỤC GIAO DIỆN TINH GỌN (UI LAYOUT)

```
┌────────────────────────────────────────────────────────────────────────┐
│ ZONE 1: HERO LISTENING (Chuẩn .hero-brand-card của hệ thống)          │
│ 🎧 KỸ NĂNG NGHE HIỂU · LISTENING                                       │
│ Luyện Nghe Tiếng Anh Mỗi Ngày                    [▶ Học tiếp: B1 Cafe] │
│ ┌──────────────┬──────────────┬──────────────┬───────────────────────┐ │
│ │ 📖 15 bài    │ ✓ 6 đã học   │ 📈 40% xong  │ ⏱️ 30 phút audio     │ │
│ └──────────────┴──────────────┴──────────────┴───────────────────────┘ │
├────────────────────────────────────────────────────────────────────────┤
│ ZONE 2: THANH CHỌN KỸ NĂNG & BỘ LỌC GỌN GÀNG                           │
│ Kỹ năng: [Tất cả] [🎧 Luyện Nghe (Active)] [Đọc hiểu] [Nói] [Viết]     │
│ Lọc nhanh: [Cấp độ: A1 A2 B1 B2] [Giọng: Tất cả / US / UK] [Tìm kiếm] │
├────────────────────────────────────────────────────────────────────────┤
│ ZONE 3: DANH SÁCH BÀI HỌC (THẺ BÀI THOÁNG ĐÃNG, ÍT CHỮ)                │
│ ┌─────────────────────────┐  ┌─────────────────────────┐               │
│ │ [A1] 🇺🇸 US       [♡]   │  │ [B1] 🇬🇧 UK       [♡]   │  (Lưới 3 cột) │
│ │ (▶) Daily Morning Conf  │  │ (▶) Ordering at Café    │               │
│ │     ⏱️ 02:45            │  │     ⏱️ 03:15            │               │
│ │ Lắng nghe hội thoại...  │  │ Nghe đặt đồ uống...     │               │
│ │ ─────────────────────── │  │ ─────────────────────── │               │
│ │ Chưa học       [Vào học]│  │ ✓ Đã xong      [Ôn tập] │               │
│ └─────────────────────────┘  └─────────────────────────┘               │
├────────────────────────────────────────────────────────────────────────┤
│ ZONE 4: THANH PHÁT NỔI Ở ĐÁY (CHỈ XUẤT HIỆN KHI ĐANG BẤM PHÁT BÀI)    │
│ [▶/⏸] [01:12 / 02:45] Tên bài nghe...   [⏮ 5s] [⏭ 5s] [1.0x]      [✕] │
└────────────────────────────────────────────────────────────────────────┘
```

---

## III. CHI TIẾT CÁC KHU VỰC HIỂN THỊ

### 1. Zone 1: Hero Banner (Giữ nguyên cấu trúc chuẩn, không thêm chữ)
- **Nội dung:** 
  - Tiêu đề: **Luyện Nghe** kèm badge `KỸ NĂNG NGHE HIỂU · LISTENING`.
  - Lời dẫn: 1 dòng ngắn gọn duy nhất.
  - Bên phải: Nút **"Học tiếp bài gần nhất"** dạng pill trắng chữ xanh (`btn-light rounded-pill`).
- **4 Khối thống kê (Pills chuẩn):**
  1. `ph-bold ph-book-open`: Tổng bài nghe (`15 bài`).
  2. `ph-bold ph-check-circle`: Đã hoàn thành (`6 bài`).
  3. `ph-bold ph-chart-line-up`: Tiến độ (`40%`).
  4. `ph-bold ph-clock`: Thời lượng đã nghe (`30 phút`).

---

### 2. Zone 2: Bộ lọc tối giản (Clean Filter Bar)
- **Dải Tabs Kỹ năng:** Giữ nguyên 5 nút pill đồng bộ: `Tất cả` (`ph-sparkle`), `Luyện Nghe` (`ph-headphones`), `Đọc hiểu` (`ph-book-open-text`), `Luyện Nói` (`ph-chats-circle`), `Luyện Viết` (`ph-pen-nib`).
- **Dòng lọc nhanh gọn gàng trong 1 card:**
  - Ô tìm kiếm từ khóa với icon `ph-bold ph-magnifying-glass`.
  - Dropdown Cấp độ: `A1` đến `C2`.
  - Dropdown Giọng đọc: `Tất cả giọng` | `🇺🇸 Giọng Mỹ (US)` | `🇬🇧 Giọng Anh (UK)`.
  - Hàng nút bấm nhanh: `Tất cả` | `A1` | `A2` | `B1` | `B2` | `✓ Đã học`.

---

### 3. Zone 3: Thẻ bài học Audio tinh gọn (Audio Cards)
Loại bỏ hoàn toàn các thông số rườm rà (không để wpm, không để nhiều dòng tag). Mỗi thẻ chỉ gồm 4 phần:
1. **Dòng Header thẻ:**
   - Badge Cấp độ: `A1` (chuẩn `bg-primary-subtle text-primary border border-primary-subtle`).
   - Badge Giọng đọc: `🇺🇸 US` hoặc `🇬🇧 UK` (chuẩn `bg-warning-subtle text-dark border border-warning-subtle`).
   - Nút Yêu thích: Icon tim `ph-bold ph-heart`.
2. **Cụm Phát Âm Thanh & Tiêu đề:**
   - **Nút tròn Quick Play** nhỏ gọn (`38px`, màu xanh thương hiệu `--primary`): Bấm vào đổi thành icon pause `ph-fill ph-pause` và phát audio ngay tại trang.
   - Bên cạnh: Tiêu đề bài học (đậm, tối đa 1 dòng) + Thời lượng `⏱️ 02:45` màu chữ muted.
3. **Mô tả ngắn:**
   - 1 đến 2 dòng vắn tắt (CSS `-webkit-line-clamp: 2`), không dài dòng.
4. **Chân thẻ:**
   - Trạng thái: Badge nhỏ `✓ Đã hoàn thành` hoặc `Chưa học`.
   - Nút hành động duy nhất: **"Vào học"** hoặc **"Ôn tập"** kèm icon `ph-bold ph-arrow-right`.

---

### 4. Zone 4: Thanh phát nổi ở chân trang (Floating Mini-Dock)
- **Chỉ xuất hiện khi người dùng bấm nút Play trên một bài học bất kỳ.**
- Thiết kế thanh mảnh (`height: 60px`), bo góc lớn (`rounded-pill`), nền kính mờ trắng:
  - **Trái:** Nút Play/Pause (`ph-fill ph-play`) + Tên bài nghe (chữ đậm, tối đa 20 ký tự) + Thời gian hiện tại.
  - **Giữa:** Thanh kéo tua mỏng (Seekbar) kèm 2 nút tua nhanh: lùi 5s (`ph-arrow-counter-clockwise`) và tiến 5s (`ph-arrow-clockwise`).
  - **Phải:** Nút chỉnh tốc độ (`1.0x` / `0.75x` / `1.25x`) + Nút tắt thanh phát (`ph-bold ph-x`).

---

## IV. ĐẶC TẢ TÍNH NĂNG KỸ THUẬT (CỐT LÕI)

### 1. Cơ chế phát âm thanh (Dual Audio Engine)
- **Ưu tiên 1:** Nếu bài học có trường link âm thanh (`audio_url`), phát trực tiếp bằng thẻ Audio HTML5.
- **Ưu tiên 2 (Tự động):** Nếu bài chưa có file mp3 thu sẵn, JavaScript tự động kích hoạt **Web Speech Synthesis API** đọc văn bản bài học bằng giọng chuẩn bản ngữ (`en-US` hoặc `en-GB`).
- Người học luôn nghe được ngay lập tức 100% các bài học.

### 2. Ghi nhận thời lượng nghe thực tế
- Khi audio đang phát, hệ thống tự động đếm giây người học thực nghe và cộng dồn vào thời lượng nghe trong ngày, đồng bộ với thống kê tiến độ trên Dashboard (`main.dashboard`).

---

## V. MÃ NGUỒN MẪU MINH HỌA (GỌN GÀNG - CHUẨN DESIGN SYSTEM)

### 1. Template Thẻ Bài Học Mới (`lessons.html`)
```html
<!-- Thẻ bài nghe tinh gọn: Thoáng đãng, ít chữ, tập trung thao tác -->
<article class="card-modern p-3.5 h-100 d-flex flex-column justify-content-between position-relative transition-hover">
  <div>
    <!-- Hàng trên: Cấp độ, Giọng đọc, Nút yêu thích -->
    <div class="d-flex justify-content-between align-items-center mb-2.5">
      <div class="d-flex align-items-center gap-1.5">
        <span class="badge bg-primary-subtle text-primary border border-primary-subtle rounded-pill px-2.5 py-0.5 fw-bold" style="font-size: 0.74rem;">
          {{ lesson.level }}
        </span>
        <span class="badge bg-warning-subtle text-dark border border-warning-subtle rounded-pill px-2 py-0.5 fw-semibold" style="font-size: 0.72rem;">
          <i class="ph-bold ph-waveform text-warning me-0.5"></i>{{ 'US' if loop.index % 2 == 1 else 'UK' }}
        </span>
      </div>

      <button type="button" class="btn btn-link p-0 text-decoration-none shadow-none btn-fav-toggle" data-lesson-id="{{ lesson.id }}" title="Yêu thích">
        <i class="ph-bold ph-heart fs-5 {{ 'text-danger' if lesson.id in favorite_ids else 'text-muted opacity-50' }}"></i>
      </button>
    </div>

    <!-- Cụm Phát Nhanh & Tiêu đề -->
    <div class="d-flex align-items-start gap-2.5 mb-2">
      <button type="button" 
              class="btn-audio-quick-play rounded-circle d-flex align-items-center justify-content-center flex-shrink-0 shadow-xs"
              data-lesson-id="{{ lesson.id }}"
              data-lesson-title="{{ lesson.title }}"
              data-lesson-text="{{ lesson.examples or lesson.content }}"
              title="Nghe nhanh bài này">
        <i class="ph-fill ph-play text-white fs-6"></i>
      </button>

      <div class="overflow-hidden">
        <h6 class="fw-bold text-dark mb-0.5 text-truncate" style="font-size: 1rem;">
          <a href="{{ url_for('learning.lesson_detail', lesson_id=lesson.id) }}" class="text-dark text-decoration-none hover-primary">
            {{ lesson.title }}
          </a>
        </h6>
        <span class="text-muted d-inline-flex align-items-center gap-1" style="font-size: 0.76rem;">
          <i class="ph-bold ph-clock"></i> 02:45
        </span>
      </div>
    </div>

    <!-- Mô tả vắn tắt 2 dòng -->
    <p class="text-secondary small mb-3" style="font-size: 0.84rem; line-height: 1.5; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;">
      {{ lesson.short_description }}
    </p>
  </div>

  <!-- Chân thẻ: Trạng thái & Nút Vào học -->
  <div class="pt-2.5 border-top border-light d-flex align-items-center justify-content-between mt-auto">
    {% if lesson.id in done %}
    <span class="badge bg-success-subtle text-success rounded-pill px-2 py-0.5 fw-bold" style="font-size: 0.72rem;">
      ✓ Đã học
    </span>
    {% else %}
    <span class="text-muted" style="font-size: 0.74rem;">Chưa học</span>
    {% endif %}

    <a href="{{ url_for('learning.lesson_detail', lesson_id=lesson.id) }}" 
       class="btn btn-primary btn-sm rounded-pill px-3 py-1 fw-bold shadow-xs d-inline-flex align-items-center gap-1"
       style="font-size: 0.8rem;">
      <span>{{ 'Ôn tập' if lesson.id in done else 'Vào học' }}</span>
      <i class="ph-bold ph-arrow-right"></i>
    </a>
  </div>
</article>
```

### 2. CSS Bổ Sung Tối Giản (`app.css`)
```css
/* Nút Quick Play hình tròn nhỏ gọn */
.btn-audio-quick-play {
  width: 38px;
  height: 38px;
  background-color: var(--primary);
  border: none;
  cursor: pointer;
  transition: transform 0.15s ease, background-color 0.15s ease;
}

.btn-audio-quick-play:hover {
  background-color: var(--primary-hover);
  transform: scale(1.05);
}

/* Thanh Mini Player Dock tinh gọn cố định ở chân trang */
.listening-mini-dock {
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  width: calc(100% - 32px);
  max-width: 820px;
  height: 58px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-full);
  box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.12);
  z-index: 1040;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
}
```

---

## VI. BẢNG KIỂM TRA ĐỒNG BỘ TRƯỚC KHI TRIỂN KHAI (CHECKLIST)

- [x] **Giao diện thoáng & ít chữ:** Không hiển thị văn bản dài dòng, mô tả rút gọn 2 dòng, thẻ bài học ngăn nắp.
- [x] **Icon đồng bộ 100%:** Chỉ dùng `ph-headphones`, `ph-play`, `ph-clock`, `ph-arrow-right`, `ph-heart`, `ph-magnifying-glass`, v.v. từ Phosphor Icons.
- [x] **Màu sắc chuẩn hệ thống:** Sử dụng Deep Emerald cho Hero, Warning/Amber cho thông số Nghe, Emerald cho nút CTA chính.
- [x] **Trải nghiệm âm thanh tức thì:** Nút Play ngay trên danh sách bài + Trình phát nổi thanh mảnh ở chân trang.
