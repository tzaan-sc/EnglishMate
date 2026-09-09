# 🗣️ KỊCH BẢN TRIỂN KHAI GIAO DIỆN & TÍNH NĂNG
## CHUYÊN TRANG: LUYỆN NÓI (SPEAKING) · ENGLISHMATE

> **Đường dẫn chuẩn danh mục:** `http://127.0.0.1:5000/speaking`  
> **Đường dẫn chuẩn bài nói:** `http://127.0.0.1:5000/speaking/<id>` (Ví dụ: `http://127.0.0.1:5000/speaking/23`)  
> **Nguyên tắc thiết kế:** Giao diện tinh gọn · Ít chữ, trực quan · Phản xạ thực chiến (Voice-First) · Đồng bộ 100% Hệ thống EnglishMate.

---

## I. NGUYÊN TẮC THIẾT KẾ & ĐỒNG BỘ HỆ THỐNG

### 1. Tối giản nội dung – Tránh rối mắt (Clean & Minimal UI)
- **Thẻ bài nói ở danh mục:** Chỉ hiển thị Cấp độ CEFR (`A1`-`C1`), Tình huống giao tiếp (Phỏng vấn, Giới thiệu, Hỏi đường, Đàm phán), Thời lượng ước tính (`⏱️ ~3 - 5 phút nói`), mô tả ngắn gọn 2 dòng, và nút hành động chính (`Vào nói` hoặc `Nói lại`).
- **Bố cục thoáng đãng:** Giữ khoảng cách đệm chuẩn (`padding`, `gap`), giao diện micrô thu âm nổi bật, trực quan dễ thao tác.
- **Tập trung thao tác giọng nói:** Mỗi câu luyện tập có nút nghe mẫu và nút bấm thu âm phát âm rõ ràng, không làm rối mắt người học.

### 2. Đồng bộ Màu sắc theo Hệ thống (`app.css` & `dashboard`)
- **Nền Hero Banner Luyện Nói:** Gradient Warm Orange / Amber chuẩn hệ thống:  
  `linear-gradient(135deg, #9a3412 0%, #c2410c 50%, #ea580c 100%)`.
- **Màu Kỹ năng Nói (Speaking Theme):** Warm Orange (`#ea580c` / text `#c2410c`, nền badge `rgba(234, 88, 12, 0.1)`, viền `#fed7aa`).
- **Nút hành động chính (Primary CTA):** Xanh thương hiệu `--primary` (`#059669` / hover `#047857`).
- **Nền & Viền trung tính:** Nền trang `--bg-canvas` (`#f8fafc`), thẻ trắng `--bg-surface` (`#ffffff`), viền `--border-light` (`#e2e8f0`).

### 3. Đồng bộ Icon chuẩn (Phosphor Icons - Toàn hệ thống)
Chỉ sử dụng icon từ thư viện Phosphor đã tích hợp sẵn:
- `ph-bold ph-chats-circle` / `ph-fill ph-chats-circle`: Biểu tượng Kỹ năng Luyện Nói (Sidebar, Hero, Tabs).
- `ph-bold ph-microphone` / `ph-fill ph-microphone`: Thu âm / Nhận diện giọng nói phát âm.
- `ph-bold ph-speaker-high`: Nghe phát âm mẫu chuẩn bản ngữ.
- `ph-bold ph-waveform`: Sóng âm / nhịp điệu phát âm.
- `ph-bold ph-arrow-counter-clockwise`: Nói lại / Thu âm lại.
- `ph-bold ph-check-circle`: Hoàn thành câu / bài nói.
- `ph-bold ph-heart` / `ph-fill ph-heart`: Đánh dấu yêu thích.
- `ph-bold ph-arrow-left`: Quay lại danh mục Luyện Nói.
- `ph-bold ph-arrow-right`: Sang câu tiếp theo.

### 4. Chuẩn Hóa Cấu Trúc Đường Dẫn & Điều Hướng (Cực kỳ quan trọng)
- **Tuyệt đối không dùng tiền tố chung `/lessons/`**:
  - Trang danh mục Luyện Nói: `http://127.0.0.1:5000/speaking` (tự động đồng bộ với `/lessons?skill=Speaking`).
  - Trang bài nói chi tiết: `http://127.0.0.1:5000/speaking/<id>` (ví dụ bài 23: `http://127.0.0.1:5000/speaking/23`).
- **Cơ chế chuyển tiếp tương thích (Auto-Redirect 302):**
  - Truy cập bất kỳ `/lessons/<speaking_id>` sẽ tự động redirect sang `/speaking/<speaking_id>`.
- **Thanh Breadcrumb bên trong bài nói:**
  - `Trang Chủ` (`/dashboard`) ➔ `Luyện Nói` (`/speaking`) ➔ `[Level]` ➔ `[Tên bài]`
- **Nút Quay lại (Back button):**
  - `"Quay lại Luyện Nói"` trỏ chính xác về `http://127.0.0.1:5000/speaking`.
- **Menu Sidebar:**
  - Thêm mục `"Luyện Nói"` (`ph-bold ph-chats-circle` màu Orange) dẫn thẳng về `/speaking`, sáng active khi `request.path.startswith('/speaking')`.

---

## II. BỐ CỤC TỔNG THỂ 2 GIAO DIỆN (UI ARCHITECTURE)

### 1. Bố cục Giao diện Danh mục Luyện Nói (`/speaking`)

```
┌────────────────────────────────────────────────────────────────────────┐
│ ZONE 1: HERO BANNER LUYỆN NÓI (Chuẩn Orange Gradient)                  │
│ 🗣️ KỸ NĂNG GIAO TIẾP & NÓI · SPEAKING                                  │
│ Tự Tin Giao Tiếp & Chuẩn Hóa Phát Âm             [🗣️ Luyện tiếp: A1]   │
│ ┌──────────────┬──────────────┬──────────────┬───────────────────────┐ │
│ │ 💬 7 bài nói │ ✓ 3 đã luyện │ 📈 43% xong  │ ⏱️ ~15 phút thực hành │ │
│ └──────────────┴──────────────┴──────────────┴───────────────────────┘ │
├────────────────────────────────────────────────────────────────────────┤
│ ZONE 2: BỘ LỌC TỐI GIẢN (1 CARD GỌN GÀNG)                              │
│ Kỹ năng: [Tất cả] [🎧 Nghe] [📖 Đọc] [🗣️ Luyện Nói (Active)] [✍️ Viết] │
│ Lọc nhanh: [Cấp độ: A1 A2 B1 B2 C1] [Tìm kiếm 🔍]                      │
├────────────────────────────────────────────────────────────────────────┤
│ ZONE 3: LƯỚI THẺ BÀI NÓI (THOÁNG ĐÃNG, TINH TẾ)                        │
│ ┌─────────────────────────┐  ┌─────────────────────────┐               │
│ │ [A1] Tự giới thiệu [♡]  │  │ [B2] Phỏng vấn [♡]      │ (Lưới 3 cột)  │
│ │ Introducing Yourself..  │  │ Job Interview Mastery   │               │
│ │ ⏱️ ~3 phút nói · 4 mẫu   │  │ ⏱️ ~5 phút nói · 4 mẫu   │               │
│ │ Giới thiệu bản thân...  │  │ Luyện trả lời cấu trúc..│               │
│ │ ─────────────────────── │  │ ─────────────────────── │               │
│ │ Chưa luyện     [Vào nói]│  │ ✓ Đã xong      [Nói lại]│               │
│ └─────────────────────────┘  └─────────────────────────┘               │
└────────────────────────────────────────────────────────────────────────┘
```

---

### 2. Bố cục Giao diện Chi tiết Bài Nói (`/speaking/<id>`) – Speaking Studio

```
┌────────────────────────────────────────────────────────────────────────┐
│ TOP BAR: BREADCRUMB & NÚT QUAY LẠI                                     │
│ Trang Chủ / Luyện Nói / A1 / Introducing Yourself Confidently          │
│ [← Quay lại Luyện Nói]                           [♡ Yêu thích] [Chia sẻ]│
├────────────────────────────────────────────────────────────────────────┤
│ THÔNG TIN BÀI HỌC & CHỈ TIÊU LUYỆN TẬP                                 │
│ [A1] [Tự giới thiệu bản thân] [Tiến độ: Câu 1/4]                       │
├───────────────────────────────────┬────────────────────────────────────┤
│ CỘT TRÁI: PHÒNG THU ÂM (60%)      │ CỘT PHẢI: TÌNH HUỐNG & MẪU (40%)   │
│ ┌───────────────────────────────┐ │ [💬 Mẫu câu] [🎯 Mẹo nói] [📝 Ghi chú]│
│ │ CÂU ĐANG LUYỆN TẬP (1/4):     │ │ ┌────────────────────────────────┐ │
│ │ "Hi everyone, my name is Alex"│ │ │ Danh sách 4 câu trọng tâm:     │ │
│ │ IPA: /haɪ ˈev.ri.wʌn.../      │ │ │ 1. Hi everyone, my name is Alex│ │
│ │ Nghĩa: Xin chào mọi người...  │ │ │ 2. I work as a web developer...│ │
│ │                               │ │ ├────────────────────────────────┤ │
│ │ [🔊 Nghe mẫu]  [🎤 Bấm để nói]│ │ │ Mẹo ngữ điệu: Lên giọng ở...   │ │
│ │                               │ │ ├────────────────────────────────┤ │
│ │ 🌟 Đánh giá: 95% chuẩn xác!   │ │ │ [✓ Hoàn thành bài nói (+20 XP)]│ │
│ │ [← Câu trước]    [Câu tiếp →] │ │ └────────────────────────────────┘ │
│ └───────────────────────────────┘ │                                    │
└───────────────────────────────────┴────────────────────────────────────┘
```

---

## III. CHI TIẾT TỪNG KHU VỰC TRÊN GIAO DIỆN

### 1. Trang Danh mục Luyện Nói (`/speaking`)

#### A. Zone 1: Hero Banner (Warm Orange Gradient)
- **Tiêu đề:** `Luyện Nói` kèm huy hiệu `KỸ NĂNG GIAO TIẾP & NÓI · SPEAKING`.
- **Mô tả:** 1 dòng súc tích: *"Luyện giao tiếp, phát âm, ngữ điệu và phản xạ tiếng Anh thông qua các tình huống thực tế."*
- **4 Thẻ thống kê tinh gọn:**
  1. `ph-bold ph-chats-circle`: Tổng bài nói (`7 bài`).
  2. `ph-bold ph-check-circle`: Đã hoàn thành (`3 bài`).
  3. `ph-bold ph-chart-line-up`: Tỷ lệ hoàn thành (`43%`).
  4. `ph-bold ph-microphone`: Thời lượng luyện nói (`15 phút`).

#### B. Zone 2: Bộ lọc tối giản
- Dải chọn Kỹ năng đồng bộ 5 nút: `Tất cả`, `Luyện Nghe`, `Đọc Hiểu`, `Luyện Nói` (Active), `Luyện Viết`.
- Ô tìm kiếm từ khóa với icon `ph-bold ph-magnifying-glass`.
- Lọc theo Cấp độ CEFR: `A1`, `A2`, `B1`, `B2`, `C1`.

#### C. Zone 3: Thẻ bài nói (Speaking Cards)
- **Header thẻ:** Badge Cấp độ (`A1`), Badge Thể loại (`Giao tiếp` / `Phỏng vấn`), Nút tim yêu thích.
- **Tiêu đề & Mục tiêu:** Tiêu đề đậm dẫn trực tiếp đến `/speaking/<id>`, thông số: `⏱️ ~3 phút nói · 4 mẫu câu`.
- **Mô tả ngắn:** Tối đa 2 dòng (`-webkit-line-clamp: 2`).
- **Footer thẻ:** Trạng thái (`✓ Đã luyện` / `Chưa luyện`), nút CTA `[Vào nói ->]` dẫn trực tiếp đến `{{ lesson.url }}`.

---

### 2. Trang Chi Tiết Bài Nói (`/speaking/<id>`) – Speaking Studio

#### A. Thanh điều hướng & Breadcrumb
- Đường dẫn chính xác: `Trang Chủ` (`/dashboard`) ➔ `Luyện Nói` (`/speaking`) ➔ `[Level]` ➔ `[Tên bài]`
- Nút quay lại: `<a href="/speaking" class="btn btn-light rounded-pill"> <i class="ph-bold ph-arrow-left"></i> Quay lại Luyện Nói </a>`

#### B. Cột trái (60%) – Phòng Thu âm Tương tác (Speaking Practice Canvas)
1. **Thẻ Câu luyện tập hiện tại:**
   - Số thứ tự câu: `Câu 1 / 4`.
   - Câu tiếng Anh in đậm cỡ lớn (`1.35rem`) với phiên âm IPA rõ ràng.
   - Bản dịch tiếng Việt gợi ý ngữ nghĩa.
2. **Cụm Điều khiển Thu âm & Nghe mẫu:**
   - Nút **"Nghe mẫu bản ngữ"** (`ph-bold ph-speaker-high`): Phát giọng đọc chuẩn qua Web Speech API.
   - Nút **"Bấm để nói"** dạng tròn nổi bật (`56px`, màu cam `#ea580c` kèm icon `ph-bold ph-microphone`): Nhấn để bật micrô thu âm; nhấn lại để hoàn tất nhận diện giọng nói.
3. **Hộp Đánh giá Phát âm Tức thì (Speech Feedback):**
   - So khớp văn bản người học vừa nói với câu mẫu.
   - Thống kê tỷ lệ chính xác (% Match): Các từ nói đúng hiển thị màu xanh lá, từ chưa chuẩn hiển thị gợi ý.
4. **Nút Chuyển câu:** Nút Lùi lại và Sang câu tiếp theo.

#### C. Cột phải (40%) – Danh sách Câu & Mẹo Giao tiếp
1. **Tab 1: 💬 Các câu trong bài (Sentences List):**
   - Danh sách tất cả câu thoại trong bài, bấm vào câu nào để nhảy ngay đến câu đó luyện tập.
2. **Tab 2: 🎯 Mẹo phát âm & Ngữ điệu:**
   - Lời khuyên về cách nhấn trọng âm (Stress), nối âm (Linking sounds) và ngữ điệu (Intonation).
3. **Tab 3: 📝 Ghi chú & Hoàn thành:**
   - Ô ghi chú mẹo học tự động lưu.
   - Nút **"Đánh dấu hoàn thành bài nói"** (`+20 XP`, cập nhật chuỗi Streak).

---

## IV. BẢNG KIỂM TRA ĐỒNG BỘ TRƯỚC KHI TRIỂN KHAI (CHECKLIST)

- [x] **URL & Breadcrumb chuẩn xác:**
  - Danh mục: `http://127.0.0.1:5000/speaking`
  - Chi tiết bài nói: `http://127.0.0.1:5000/speaking/<id>` (tuyệt đối không dùng `/lessons/<id>`).
  - Breadcrumb: `Trang Chủ` ➔ `Luyện Nói` (`/speaking`) ➔ `[Level]` ➔ `[Tên bài]`.
  - Nút quay lại: `"Quay lại Luyện Nói"` dẫn về `/speaking`.
- [x] **Giao diện tinh gọn & ít chữ:** Thẻ danh mục súc tích, mô tả 2 dòng, phòng thu âm trực quan.
- [x] **Màu sắc chuẩn hệ thống:** Warm Orange gradient cho Hero, tông màu Orange (`#ea580c`) cho điểm nhấn Luyện Nói, nút CTA xanh `--primary`.
- [x] **Icon Phosphor đồng bộ:** 100% icon từ Phosphor (`ph-chats-circle`, `ph-microphone`, `ph-speaker-high`, `ph-waveform`, `ph-arrow-right`, `ph-check-circle`).
- [x] **Menu Sidebar:** Tích hợp mục "Luyện Nói" dẫn về `/speaking` với trạng thái active chuẩn xác.
