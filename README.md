# 🇬🇧 EnglishMate — Nền Tảng Học Tiếng Anh Thông Minh

**EnglishMate** là nền tảng học tiếng Anh trực tuyến hiện đại, kết hợp phương pháp lặp lại ngắt quãng (**SRS Flashcard**), trò chơi hóa (**Gamification**), hệ thống đề thi chuẩn quốc tế (**TOEIC, IELTS, THPT**) và bảng phân tích tiến độ cá nhân hóa.

---

## ⚡ Cài Đặt & Chạy Nhanh (Quick Start)

```powershell
# 1. Tạo và kích hoạt môi trường ảo
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Cài đặt các gói phụ thuộc
pip install -r requirements.txt

# 3. Khởi chạy ứng dụng
python run.py
```

Truy cập website tại: **`http://127.0.0.1:5000`**

---

## 👥 Tài Khoản Dùng Thử (Demo Accounts)

| Vai trò | Email | Mật khẩu | Ghi chú |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin@example.com` | `admin123` | Quản trị hệ thống, thêm bài học, import dữ liệu |
| **Học viên** | `user1@example.com` | `user123` | Trải nghiệm học tập, làm quiz, chơi game |

---

## 🌟 Tính Năng Nổi Bật

- 📚 **Hệ thống Bài học & Ngữ pháp:** Phân loại từ A1 đến C2 kèm ví dụ và ghi chú cá nhân.
- 🗂️ **Flashcard SRS Thông minh:** Ôn tập từ vựng dựa trên thuật toán lặp lại ngắt quãng (Spaced Repetition).
- 🎮 **Gamification & Trò chơi:** Điểm kinh nghiệm (XP), cấp độ, huy hiệu, nhiệm vụ hàng ngày và chuỗi học tập (Streak).
- 📝 **Luyện thi & Đề thi:** Hệ thống thi TOEIC, IELTS, THPT có đồng hồ bấm giờ, chấm điểm tự động và giải thích chi tiết.
- 📊 **Thống kê & Heatmap:** Bản đồ nhiệt hoạt động học tập, biểu đồ tăng trưởng từ vựng và phân tích độ cân bằng kỹ năng.
- 🛠️ **Admin & Import Dữ liệu:** Nhập câu hỏi, từ vựng và bài học hàng loạt qua file CSV / Excel.

---

## 🧪 Kiểm Thử (Run Tests)

```powershell
pytest
```
*(Toàn bộ 147 test cases đều tự động kiểm tra tính đúng đắn của chức năng).*

---

## 📚 Tài Liệu Hướng Dẫn Chi Tiết

- 📖 **Chi tiết Kỹ thuật & Kiến trúc:** [`docs/ARCHITECTURE_AND_DECISIONS.md`](docs/ARCHITECTURE_AND_DECISIONS.md)
- 🧭 **Hướng dẫn Tạo & Tìm Dữ liệu học tập:** [`sample_csv_templates/DATA_SOURCING_GUIDE.md`](sample_csv_templates/DATA_SOURCING_GUIDE.md)
- 📁 **File CSV Mẫu để Import:** [`sample_csv_templates/`](sample_csv_templates/)
- 🛠️ **Công cụ Tự động Bóc tách File Drive/Word/PDF:** [`scripts/`](scripts/)
- 📑 **Danh sách Tính năng Đầy đủ:** [`docs/DETAILED_FEATURE_SPECIFICATION.md`](docs/DETAILED_FEATURE_SPECIFICATION.md)
