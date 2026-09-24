# ✍️ KỊCH BẢN TRIỂN KHAI GIAO DIỆN & TÍNH NĂNG
## CHUYÊN TRANG: LUYỆN VIẾT (WRITING) · ENGLISHMATE

> **Đường dẫn chuẩn danh mục:** `http://127.0.0.1:5000/writing`  
> **Đường dẫn chuẩn bài viết:** `http://127.0.0.1:5000/writing/<id>` (Ví dụ: `http://127.0.0.1:5000/writing/29`)  
> **Nguyên tắc thiết kế:** Giao diện tinh gọn · Ít chữ, trực quan · Soạn thảo thực chiến (Writer-Centric) · Đồng bộ 100% Hệ thống EnglishMate.

---

## I. NGUYÊN TẮC THIẾT KẾ & ĐỒNG BỘ HỆ THỐNG

### 1. Tối giản nội dung – Tránh rối mắt (Clean & Minimal UI)
- **Thẻ bài viết ở danh mục:** Chỉ hiển thị Cấp độ CEFR (`A1`-`C1`), Thể loại văn bản (Ghi chú, Email, Tin nhắn, Thư trang trọng, Luận), Mục tiêu độ dài (`50 - 150 từ`), mô tả ngắn gọn 2 dòng, và nút hành động chính (`Vào viết` hoặc `Viết lại`).
- **Bố cục thoáng đãng:** Giữ khoảng cách đệm chuẩn (`padding`, `gap`), ô soạn thảo rộng rãi, thanh đếm từ trực quan.
- **Tập trung thao tác:** Tránh dàn trải quá nhiều nút bấm phụ gây xao nhãng trong quá trình rèn luyện viết.

### 2. Đồng bộ Màu sắc theo Hệ thống (`app.css` & `dashboard`)
- **Nền Hero Banner Luyện Viết:** Gradient Rose / Crimson chuẩn hệ thống:  
  `linear-gradient(135deg, #881337 0%, #be123c 50%, #e11d48 100%)`.
- **Màu Kỹ năng Viết (Writing Theme):** Rose / Crimson (`#be123c` / text `#9f1239`, nền badge `rgba(190, 18, 60, 0.1)`, viền `#fecdd3`).
- **Nút hành động chính (Primary CTA):** Xanh thương hiệu `--primary` (`#059669` / hover `#047857`).
- **Nền & Viền trung tính:** Nền trang `--bg-canvas` (`#f8fafc`), thẻ trắng `--bg-surface` (`#ffffff`), viền `--border-light` (`#e2e8f0`).

### 3. Đồng bộ Icon chuẩn (Phosphor Icons - Toàn hệ thống)
Chỉ sử dụng icon từ thư viện Phosphor đã tích hợp sẵn:
- `ph-bold ph-pen-nib` / `ph-fill ph-pen-nib`: Biểu tượng Kỹ năng Luyện Viết (Sidebar, Hero, Tabs).
- `ph-bold ph-pencil-line`: Soạn thảo văn bản.
- `ph-bold ph-text-align-left`: Bộ đếm số từ / độ dài bài viết.
- `ph-bold ph-magic-wand` / `ph-bold ph-sparkle`: Kiểm tra & phân tích bài viết.
- `ph-bold ph-lightbulb`: Cấu trúc câu & gợi ý từ vựng.
- `ph-bold ph-copy`: Sao chép hoặc chèn nhanh mẫu câu.
- `ph-bold ph-arrow-counter-clockwise`: Làm lại / xóa ô nhập.
- `ph-bold ph-check-circle`: Hoàn thành bài viết.
- `ph-bold ph-heart` / `ph-fill ph-heart`: Đánh dấu yêu thích.
- `ph-bold ph-arrow-left`: Quay lại danh mục Luyện Viết.

### 4. Chuẩn Hóa Cấu Trúc Đường Dẫn & Điều Hướng (Cực kỳ quan trọng)
- **Tuyệt đối không dùng tiền tố chung `/lessons/`**:
  - Trang danh mục Luyện Viết: `http://127.0.0.1:5000/writing` (tự động đồng bộ với `/lessons?skill=Writing`).
  - Trang bài viết chi tiết: `http://127.0.0.1:5000/writing/<id>` (ví dụ bài 29: `http://127.0.0.1:5000/writing/29`).
- **Cơ chế chuyển tiếp tương thích (Auto-Redirect 302):**
  - Truy cập bất kỳ `/lessons/<writing_id>` sẽ tự động redirect sang `/writing/<writing_id>`.
- **Thanh Breadcrumb bên trong bài viết:**
  - `Trang Chủ` (`/dashboard`) ➔ `Luyện Viết` (`/writing`) ➔ `[Level]` ➔ `[Tên bài]`
- **Nút Quay lại (Back button):**
  - `"Quay lại Luyện Viết"` trỏ chính xác về `http://127.0.0.1:5000/writing`.
- **Menu Sidebar:**
  - Thêm mục `"Luyện Viết"` (`ph-bold ph-pen-nib` màu Rose) dẫn thẳng về `/writing`, sáng active khi `request.path.startswith('/writing')`.

---

## II. BỐ CỤC TỔNG THỂ 2 GIAO DIỆN (UI ARCHITECTURE)

### 1. Bố cục Giao diện Danh mục Luyện Viết (`/writing`)

```
┌────────────────────────────────────────────────────────────────────────┐
│ ZONE 1: HERO BANNER LUYỆN VIẾT (Chuẩn Rose Gradient)                  │
│ ✍️ KỸ NĂNG SOẠN THẢO & VIẾT · WRITING                                  │
│ Nâng Cao Kỹ Năng Viết Từ Câu Đến Đoạn Văn         [✍️ Viết tiếp: A2]   │
│ ┌──────────────┬──────────────┬──────────────┬───────────────────────┐ │
│ │ 📝 5 bài viết│ ✓ 2 đã viết  │ 📈 40% xong  │ ✍️ ~240 từ thực hành  │ │
│ └──────────────┴──────────────┴──────────────┴───────────────────────┘ │
├────────────────────────────────────────────────────────────────────────┤
│ ZONE 2: BỘ LỌC TỐI GIẢN (1 CARD GỌN GÀNG)                              │
│ Kỹ năng: [Tất cả] [🎧 Nghe] [📖 Đọc] [🗣️ Nói] [✍️ Luyện Viết (Active)] │
│ Lọc nhanh: [Cấp độ: A1 A2 B1 B2 C1] [Mục tiêu từ] [Tìm kiếm 🔍]        │
├────────────────────────────────────────────────────────────────────────┤
│ ZONE 3: LƯỚI THẺ BÀI VIẾT (THOÁNG ĐÃNG, TINH TẾ)                       │
│ ┌─────────────────────────┐  ┌─────────────────────────┐               │
│ │ [A2] Tin nhắn mời [♡]   │  │ [B2] Thư trang trọng [♡]│ (Lưới 3 cột)  │
│ │ Writing an Invitation.. │  │ Formal Business Request │               │
│ │ 📝 Mục tiêu: 40-70 từ   │  │ 📝 Mục tiêu: 120-180 từ │               │
│ │ Viết tin nhắn mời bạn...│  │ Viết thư khiếu nại...   │               │
│ │ ─────────────────────── │  │ ─────────────────────── │               │
│ │ Chưa viết      [Vào viết│  │ ✓ Đã xong      [Viết lại│               │
│ └─────────────────────────┘  └─────────────────────────┘               │
└────────────────────────────────────────────────────────────────────────┘
```

---

### 2. Bố cục Giao diện Chi tiết Bài Viết (`/writing/<id>`) - Writing Studio

```
┌────────────────────────────────────────────────────────────────────────┐
│ TOP BAR: BREADCRUMB & NÚT QUAY LẠI                                     │
│ Trang Chủ / Luyện Viết / A2 / Writing an Invitation Message            │
│ [← Quay lại Luyện Viết]                          [♡ Yêu thích] [Chia sẻ]│
├────────────────────────────────────────────────────────────────────────┤
│ THÔNG TIN BÀI TẬP: ĐỀ BÀI & YÊU CẦU TRỌNG TÂM                         │
│ [A2] [Tin nhắn mời tiệc sinh nhật] [Mục tiêu: 40-70 từ]                │
├───────────────────────────────────┬────────────────────────────────────┤
│ CỘT TRÁI: KHÔNG GIAN VIẾT (60%)   │ CỘT PHẢI: MẪU CÂU & BÀI MẪU (40%)  │
│ ┌───────────────────────────────┐ │ [💡 Mẫu câu] [📖 Bài mẫu] [📝 Ghi chú]│
│ │ ĐỀ BÀI: Viết tin nhắn mời...  │ │ ┌────────────────────────────────┐ │
│ │ ┌───────────────────────────┐ │ │ • I would like to invite you...  │ │
│ │ │ Ô soạn thảo bài viết...   │ │ │ • The party takes place at...    │ │
│ │ │                           │ │ │ • Please let me know by...       │ │
│ │ └───────────────────────────┘ │ ├────────────────────────────────┤ │
│ │ 📝 42 / 60 từ  [✨ Phân tích]  │ │ [📖 Xem bài viết mẫu hoàn chỉnh] │ │
│ │ ┌───────────────────────────┐ │ ├────────────────────────────────┤ │
│ │ │ ✨ Đánh giá tự động: Tốt! │ │ │ [✓ Nộp & Hoàn thành (+20 XP)]    │ │
│ │ └───────────────────────────┘ │ └────────────────────────────────┘ │
│ └───────────────────────────────┘ │                                    │
└───────────────────────────────────┴────────────────────────────────────┘
```

---

## III. CHI TIẾT TỪNG KHU VỰC TRÊN GIAO DIỆN

### 1. Trang Danh mục Luyện Viết (`/writing`)

#### A. Zone 1: Hero Banner (Rose Gradient)
- **Tiêu đề:** `Luyện Viết` kèm huy hiệu `KỸ NĂNG SOẠN THẢO & VIẾT · WRITING`.
- **Mô tả:** 1 dòng súc tích: *"Rèn luyện khả năng viết câu, đoạn văn, email và các nội dung tiếng Anh theo chủ đề."*
- **4 Thẻ thống kê tinh gọn:**
  1. `ph-bold ph-pen-nib`: Tổng bài viết (`5 bài`).
  2. `ph-bold ph-check-circle`: Đã hoàn thành (`2 bài`).
  3. `ph-bold ph-chart-line-up`: Tỷ lệ hoàn thành (`40%`).
  4. `ph-bold ph-pencil-line`: Số từ đã thực hành (`240 từ`).

#### B. Zone 2: Bộ lọc tối giản
- Dải chọn Kỹ năng đồng bộ 5 nút: `Tất cả`, `Luyện Nghe`, `Đọc Hiểu`, `Luyện Nói`, `Luyện Viết` (Active).
- Ô tìm kiếm từ khóa với icon `ph-bold ph-magnifying-glass`.
- Lọc theo Cấp độ CEFR: `A1`, `A2`, `B1`, `B2`, `C1`.

#### C. Zone 3: Thẻ bài viết (Writing Cards)
- **Header thẻ:** Badge Cấp độ (`A2`), Badge Thể loại (`Tin nhắn` / `Email` / `Bài luận`), Nút tim yêu thích.
- **Tiêu đề & Mục tiêu:** Tiêu đề đậm dẫn trực tiếp đến `/writing/<id>`, thông số mục tiêu: `📝 Mục tiêu: 40-70 từ`.
- **Mô tả ngắn:** Tối đa 2 dòng (`-webkit-line-clamp: 2`).
- **Footer thẻ:** Trạng thái (`✓ Đã viết` / `Chưa viết`), nút CTA `[Vào viết ->]` dẫn trực tiếp đến `{{ lesson.url }}`.

---

### 2. Trang Chi Tiết Bài Viết (`/writing/<id>`) – Writing Studio

#### A. Thanh điều hướng & Breadcrumb
- Đường dẫn chính xác: `Trang Chủ` (`/dashboard`) ➔ `Luyện Viết` (`/writing`) ➔ `[Level]` ➔ `[Tên bài]`
- Nút quay lại: `<a href="/writing" class="btn btn-light rounded-pill"> <i class="ph-bold ph-arrow-left"></i> Quay lại Luyện Viết </a>`

#### B. Cột trái (60%) – Không gian Soạn thảo (Writing Canvas)
1. **Khung Đề bài & Tiêu chuẩn:** Hộp màu xám nhạt tinh gọn nêu rõ tình huống giả định và các ý cần trả lời.
2. **Khung soạn thảo văn bản (`#writingTextarea`):**
   - Ô nhập văn bản rộng thoáng, viền mềm mại, font chữ thanh lịch, chiều cao tối thiểu `240px`.
   - Lưu trữ bản nháp cục bộ (Auto-save Draft) để người học không bị mất bài viết nếu tải lại trang.
3. **Thanh trạng thái & Đếm từ thời gian thực (Live Word Counter):**
   - Đếm số từ thực tế: `45 / 60 từ`.
   - Vạch tiến độ trực quan: đổi màu xanh lá khi đạt đủ số từ yêu cầu.
   - Nút **"Kiểm tra & Đánh giá"** (`ph-bold ph-magic-wand`).
4. **Hộp Đánh giá & Phản hồi Tức thì (Writing Feedback Box):**
   - Phân tích số câu, độ dài trung bình, từ chuyển tiếp được sử dụng (Connecting Words: *First, Then, Because, However...*).
   - Đưa ra lời khen ngợi hoặc gợi ý bổ sung chi tiết giúp bài viết tự nhiên hơn.

#### C. Cột phải (40%) – Cấu trúc Mẫu & Bài Viết Chuẩn
1. **Tab 1: 💡 Cấu trúc & Mẫu câu (Key Structures):**
   - Danh sách 4-6 mẫu câu hữu ích nhất cho đề bài (kèm nghĩa tiếng Việt).
   - Mỗi câu có nút **"Chèn"** (`+ Chèn`) để dán ngay câu đó vào ô soạn thảo, giúp người mới bắt đầu dễ dàng thực hành.
2. **Tab 2: 📖 Bài viết mẫu chuẩn (Model Answer):**
   - Đoạn văn mẫu tiêu chuẩn CEFR (từ `lesson.examples`), có dịch nghĩa tiếng Việt và phân tích cấu trúc từng câu.
3. **Tab 3: 📝 Ghi chú & Nộp bài hoàn thành:**
   - Ô ghi chú cá nhân tự động lưu.
   - Nút **"Nộp & Đánh dấu hoàn thành"** (`+20 XP`, cập nhật chuỗi Streak).

---

## IV. BẢNG KIỂM TRA ĐỒNG BỘ TRƯỚC KHI TRIỂN KHAI (CHECKLIST)

- [x] **URL & Breadcrumb chuẩn xác:**
  - Danh mục: `http://127.0.0.1:5000/writing`
  - Chi tiết bài viết: `http://127.0.0.1:5000/writing/<id>` (tuyệt đối không dùng `/lessons/<id>`).
  - Breadcrumb: `Trang Chủ` ➔ `Luyện Viết` (`/writing`) ➔ `[Level]` ➔ `[Tên bài]`.
  - Nút quay lại: `"Quay lại Luyện Viết"` dẫn về `/writing`.
- [x] **Giao diện tinh gọn & ít chữ:** Thẻ danh mục súc tích, mô tả 2 dòng, ô soạn thảo thông thoáng.
- [x] **Màu sắc chuẩn hệ thống:** Rose / Crimson gradient cho Hero, tông màu Rose (`#be123c`) cho điểm nhấn Luyện Viết, nút CTA xanh `--primary`.
- [x] **Icon Phosphor đồng bộ:** 100% icon từ Phosphor (`ph-pen-nib`, `ph-pencil-line`, `ph-magic-wand`, `ph-lightbulb`, `ph-copy`, `ph-check-circle`, `ph-arrow-right`).
- [x] **Menu Sidebar:** Tích hợp mục "Luyện Viết" dẫn về `/writing` với trạng thái active chuẩn xác.
