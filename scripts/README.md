# 🛠️ TỔNG HỢP CÁC SCRIPT HỆ THỐNG (SCRIPTS)

Tất cả các script công cụ được đặt trực tiếp trong thư mục `scripts/` với tên gọi ngắn gọn, rõ ràng theo đúng chức năng:

---

## 📂 Danh Sách Các File Script

| File Script | Chức năng chính | Lệnh chạy mẫu |
| :--- | :--- | :--- |
| **`extract_data.py`** | Bóc tách câu hỏi & từ vựng từ file Word (`.docx`), PDF (`.pdf`), Text (`.txt`) | `python scripts/extract_data.py` |
| **`validate_vocab.py`** | Kiểm tra lỗi, trùng lặp, IPA & tự động sửa lỗi file CSV Từ vựng | `python scripts/validate_vocab.py csv_templates/vocabulary_template.csv --online --auto-fix` |
| **`validate_questions.py`** | Kiểm tra tính hợp lệ của file CSV Ngân hàng Câu hỏi trắc nghiệm | `python scripts/validate_questions.py csv_templates/questions_template.csv` |
| **`fetch_vocab.py`** | Tự động gọi API tra cứu IPA, nghĩa tiếng Việt và nạp từ vựng vào Database | `python scripts/fetch_vocab.py` |
| **`patch_db.py`** | Đồng bộ & cập nhật cấu trúc bảng cơ sở dữ liệu (PostgreSQL / SQLite) | `python scripts/patch_db.py` |
| **`setup_exams.py`** | Khởi tạo cấu trúc các bảng đề thi trong cơ sở dữ liệu | `python scripts/setup_exams.py` |
| `document_parser.py` | *(Module phụ trợ)* Thuật toán bóc tách regex cho `extract_data.py` | Tự động gọi bởi `extract_data.py` |

---

## 🗄️ Hướng Dẫn Khởi Tạo & Seed Database

### Cơ chế Database (Fallback tự động)

App hỗ trợ **tự động fallback** từ PostgreSQL sang SQLite:

- Khi khởi động, app **thử kết nối PostgreSQL** (timeout 3 giây).
- Nếu **thành công** → dùng PostgreSQL.
- Nếu **thất bại** (server down, sai mật khẩu...) → tự chuyển sang SQLite local, in cảnh báo ra console.

> **Lưu ý quan trọng:** PostgreSQL và SQLite là **2 file riêng biệt**, KHÔNG tự đồng bộ với nhau. Phải seed data riêng cho từng DB nếu cần.

---

### Cách 1: Seed data vào PostgreSQL

> Dùng khi `DATABASE_URL` trong `.env` đang trỏ đến PostgreSQL.

```powershell
# Bước 1: Đảm bảo PostgreSQL đang chạy và DATABASE_URL trong .env đúng
# (ví dụ: DATABASE_URL=postgresql://postgres:123@localhost:5433/englishmate)

# Bước 2: Tạo bảng + nạp data mẫu (users, lessons, vocabulary, questions)
python -m app.seed

# Bước 3: Nạp thêm bộ đề TOEIC mẫu (100 câu hỏi TOEIC Part 5-7)
python -m app.seed_toeic
```

**Kết quả sau khi seed PostgreSQL:**

| Bảng | Số bản ghi |
|---|---|
| `user` | 3 (admin / user1 / user2) |
| `lesson` | 12 bài học (A1 đến B2) |
| `vocabulary` | 60 từ vựng |
| `question` | 40 câu hỏi trắc nghiệm |
| `toeic_test` | 1 đề thi TOEIC |
| `toeic_question` | 100 câu hỏi TOEIC |

**Tài khoản mẫu:**

| Username | Password | Quyền |
|---|---|---|
| `admin` | `admin123` | Admin |
| `user1` | `user123` | User |
| `user2` | `user123` | User |

---

### Cách 2: Seed data vào SQLite (để test offline / không cần PostgreSQL)

> Dùng khi muốn chạy app **không cần PostgreSQL**.

```powershell
# Bước 1: Mở file .env, comment out dòng DATABASE_URL postgresql
#   Trước:   DATABASE_URL=postgresql://postgres:123@localhost:5433/englishmate
#   Sau:   # DATABASE_URL=postgresql://postgres:123@localhost:5433/englishmate
# (Khi DATABASE_URL bị comment, app tự dùng SQLite tại instance/englishmate.db)

# Bước 2: Nạp data mẫu vào SQLite
python -m app.seed

# Bước 3: (Tùy chọn) Nạp thêm bộ đề TOEIC
python -m app.seed_toeic

# Bước 4: Khởi động app bình thường
python run.py
```

File SQLite sẽ được lưu tại: `instance/englishmate.db`
Có thể mở bằng DB Browser for SQLite hoặc extension SQLite Viewer trong VS Code để xem data.

---

### Cách 3: Seed data cho cả 2 DB (PostgreSQL + SQLite)

> Dùng khi muốn cả 2 DB cùng có đầy đủ data mẫu để test linh hoạt.

```powershell
# Bước 1: Seed PostgreSQL trước
#   (Đảm bảo DATABASE_URL=postgresql://... đang bật trong .env)
python -m app.seed
python -m app.seed_toeic

# Bước 2: Comment out dòng postgresql trong .env
#   DATABASE_URL=postgresql://postgres:123@localhost:5433/englishmate
# đổi thành:
#   # DATABASE_URL=postgresql://postgres:123@localhost:5433/englishmate

# Bước 3: Seed SQLite
python -m app.seed
python -m app.seed_toeic

# Bước 4: Bỏ comment dòng postgresql trong .env để dùng lại PostgreSQL
#   DATABASE_URL=postgresql://postgres:123@localhost:5433/englishmate
```

Sau bước này, cả PostgreSQL lẫn SQLite đều có cùng data mẫu.

> Nếu cần đồng bộ **data thực tế** (không phải data mẫu), hãy dùng `pg_dump` / pgAdmin để export-import giữa 2 DB.

---

## 🚀 Hướng Dẫn Sử Dụng Nhanh Các Script

### 1. Bóc tách tài liệu Word / PDF / TXT (`extract_data.py`)

- Thả file tài liệu vào `scripts/input_files/`.
- Chạy:
  ```powershell
  python scripts/extract_data.py
  ```
- Chọn **1** để bóc tách Câu hỏi trắc nghiệm hoặc **2** để bóc tách Từ vựng.

### 2. Kiểm tra dữ liệu Từ vựng (`validate_vocab.py`)

```powershell
# Kiểm tra cơ bản
python scripts/validate_vocab.py

# Đối chiếu Online Dictionary và tự sửa lỗi
python scripts/validate_vocab.py csv_templates/vocabulary_template.csv --online --auto-fix
```

### 3. Kiểm tra dữ liệu Câu hỏi (`validate_questions.py`)

```powershell
python scripts/validate_questions.py
```

### 4. Tra cứu tự động qua API (`fetch_vocab.py`)

```powershell
python scripts/fetch_vocab.py
# Nhập danh sách từ, ví dụ: accomplish, resilient, innovate
```

### 5. Đồng bộ cấu trúc Database (`patch_db.py`)

```powershell
# Chạy sau khi thêm model mới hoặc thay đổi cột trong models
python scripts/patch_db.py
```
