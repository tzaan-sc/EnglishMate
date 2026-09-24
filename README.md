# 🇬🇧 EnglishMate — Nền Tảng Học Tiếng Anh Thông Minh

**EnglishMate** là nền tảng học tiếng Anh trực tuyến hiện đại, kết hợp phương pháp lặp lại ngắt quãng (**SRS Flashcard**), trò chơi hóa (**Gamification**), hệ thống đề thi chuẩn quốc tế (**TOEIC, IELTS, THPT**) và bảng phân tích tiến độ cá nhân hóa.

---

## ⚡ Cài Đặt & Chạy Nhanh (Quick Start)

```powershell
# 1. Kích hoạt môi trường ảo
.\.venv\Scripts\Activate.ps1

# 2. Cài đặt các gói phụ thuộc
python -m pip install -r requirements.txt

# 3. Khởi tạo dữ liệu mẫu (nếu cần)
python -m app.seed         # Khởi tạo bài học, từ vựng demo & tài khoản
python -m app.seed_toeic   # Khởi tạo bộ đề thi TOEIC full format

# 4. Khởi chạy ứng dụng
python run.py
```

Truy cập website tại: **`http://127.0.0.1:5000`**

> **💡 Mẹo:** Nếu gặp lỗi `Fatal error in launcher: Unable to create process` khi gõ `pip`, hãy dùng tiền tố `python -m pip ...` để gọi trực tiếp qua Python.

---

## 👥 Tài Khoản Dùng Thử (Demo Accounts)

| Vai trò | Email | Mật khẩu | Ghi chú |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin@example.com` | `admin123` | Quản trị hệ thống, duyệt nội dung, import dữ liệu |
| **Học viên** | `user1@example.com` | `user123` | Trải nghiệm học tập, làm bài thi, flashcard, mini game |

---

## 📂 Cấu Trúc Thư Mục Dự Án (Project Structure)

```text
web-english/
├── app/                        # Mã nguồn chính ứng dụng Flask
│   ├── frontend/               # Giao diện người dùng (UI & Static Assets)
│   │   ├── static/             # Assets: CSS, JavaScript, Web Fonts, Images
│   │   └── templates/          # Giao diện Jinja2 HTML hiện đại
│   ├── backend/                # Xử lý dữ liệu & logic nghiệp vụ (Blueprints)
│   │   ├── admin/              # Quản trị hệ thống, quản lý đề thi & học viên
│   │   ├── auth/               # Đăng nhập, đăng ký, OTP, OAuth Google/Facebook
│   │   ├── exams/              # Thi TOEIC, IELTS, THPT, chấm điểm & review
│   │   ├── learning/           # Học ngữ pháp, Flashcard SRS, mini-game từ vựng
│   │   └── main/               # Trang chủ, dashboard tiến độ học tập
│   ├── seeds/                  # Bộ dữ liệu khởi tạo database (Base & TOEIC)
│   ├── utils/                  # Helper dùng chung (Email SMTP, Template generator)
│   ├── config.py               # Cấu hình môi trường & tự động fallback DB
│   ├── extensions.py           # Khởi tạo SQLAlchemy, LoginManager, CSRF
│   ├── seed.py                 # Forwarder CLI: python -m app.seed
│   └── seed_toeic.py           # Forwarder CLI: python -m app.seed_toeic
│
├── docs/                       # Toàn bộ tài liệu dự án (được phân loại khoa học)
│   ├── architecture/           # Thiết kế CSDL (database_schema) & kiến trúc hệ thống
│   ├── guides/                 # Hướng dẫn đồng bộ dữ liệu, cấu hình OAuth & SMTP
│   ├── plans/                  # 25 file kế hoạch chi tiết từng màn hình (1.1 - 4.7)
│   ├── skills/                 # Đặc tả 4 kỹ năng: Listening, Reading, Speaking, Writing
│   └── specs/                  # Đặc tả chi tiết toàn bộ tính năng & nút bấm hệ thống
│
├── scripts/                    # Các công cụ CLI hỗ trợ dữ liệu & kiểm thử
│   ├── setup_exams.py          # Script khởi tạo bảng đề thi
│   ├── patch_db.py             # Script đồng bộ & bổ sung cột CSDL
│   ├── seed_comprehensive_vocab.py # Tool bóc tách & nạp từ vựng quy mô lớn
│   ├── document_parser.py      # Bộ phân tích văn bản tự động
│   └── test_import.py          # Script test import đề thi từ JSON
│
├── csv_templates/              # Mẫu file Excel / CSV nhập liệu & dữ liệu mẫu
│   ├── data/                   # File dữ liệu chuẩn bị import (TOEIC, Vocab, JSON)
│   └── templates/              # File mẫu trắng để giáo viên / admin điền
│
├── tests/                      # Bộ kiểm thử tự động toàn diện (185+ test cases)
├── instance/                   # File SQLite local & media file tải lên
├── .env.example                # Mẫu khai báo biến môi trường chuẩn
├── requirements.txt            # Danh sách thư viện Python phụ thuộc
└── run.py                      # File khởi động ứng dụng Flask
```

---

## 🌟 Tính Năng Nổi Bật

- 📚 **Hệ thống Bài học & Ngữ pháp:** Phân loại từ A1 đến C2 kèm bài tập thực hành và ghi chú cá nhân.
- 🗂️ **Flashcard SRS Thông minh:** Ôn tập từ vựng ngắt quãng (Spaced Repetition) với thuật toán tối ưu ghi nhớ.
- 🎮 **Gamification & Trò chơi:** Tích lũy XP, thăng cấp, chuỗi ngày học (Streak), bảng xếp hạng và mini-game tương tác.
- 📝 **Luyện thi & Đề thi Chuẩn:** Hỗ trợ TOEIC full 7 Parts, IELTS, THPT Quốc Gia với đồng hồ bấm giờ và giải thích chi tiết.
- 📊 **Thống kê & Heatmap:** Phân tích điểm mạnh/yếu, bản đồ nhiệt học tập và biểu đồ phân bổ thời gian.
- 🛠️ **Quản trị & Import Hàng Loạt:** Admin dễ dàng import câu hỏi, bài đọc, audio và từ vựng qua Excel / CSV.

---

## 🧪 Kiểm Thử Tự Động (Run Tests)

```powershell
python -m pytest -q
```
*(Toàn bộ **185+ test cases** đều pass và đảm bảo chất lượng hệ thống).*

---

## 📚 Tra Cứu Tài Liệu Nhanh

- 📑 [Kế hoạch chi tiết 25 chức năng (1.1 - 4.7)](docs/plans/)
- 🧭 [Hướng dẫn Đồng bộ Dữ liệu PostgreSQL & SQLite](docs/guides/HD_Sync_Data.md)
- 🔑 [Hướng dẫn Cấu hình Google OAuth](docs/guides/HUONG_DAN_TAO_GOOGLE_OAUTH.txt)
- 📧 [Hướng dẫn Cấu hình Gmail SMTP](docs/guides/HUONG_DAN_CAU_HINH_GMAIL_SMTP.txt)
- 🗄️ [Đặc tả Lược đồ CSDL (Database Schema)](docs/architecture/database_schema.md)
- 📋 [Tổng hợp Đặc tả Tính năng Hệ thống](docs/specs/CORE_FEATURES.md)
- 📁 [File CSV / Excel Mẫu để Import](csv_templates/)
