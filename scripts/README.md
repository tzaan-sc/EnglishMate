# 🛠️ TỔNG HỢP CÁC BỘ SCRIPT HỆ THỐNG (SCRIPTS DIRECTORY)

Thư mục `scripts/` được phân chia thành **4 nhóm chức năng chuyên biệt**, rõ ràng và dễ tra cứu:

---

## 📂 Sơ Đồ Cấu Trúc Thư Mục

```text
scripts/
│
├── data_extractor/            <-- [Nhóm 1] Bóc tách tài liệu từ Google Drive (Word / PDF / Text)
│   ├── input_files/           <-- Thả file .docx, .pdf, .txt từ Drive vào đây
│   ├── output_csv/            <-- Nơi xuất file CSV sau khi bóc tách
│   ├── document_parser.py     <-- Thuật toán phân tích câu hỏi & từ vựng
│   └── extract_data.py        <-- File chạy trích xuất chính
│
├── data_validator/            <-- [Nhóm 2] Kiểm tra & đánh giá độ chính xác Dataset
│   ├── validate_vocabulary.py <-- Quét từng dòng từ vựng, check trùng lặp, IPA, online dict, auto-fix
│   └── validate_questions.py  <-- Kiểm tra ngân hàng câu hỏi, đủ 4 lựa chọn A/B/C/D, đáp án đúng
│
├── api_enricher/              <-- [Nhóm 3] Tự động gọi API Từ điển & Dịch thuật
│   └── fetch_vocabulary_api.py <-- Nhập danh sách từ -> Tự lấy IPA, ví dụ & dịch tiếng Việt
│
├── database_tools/            <-- [Nhóm 4] Công cụ quản trị & vá cấu trúc Database
│   ├── patch_database.py      <-- Vá và cập nhật bảng/cột cơ sở dữ liệu
│   └── setup_sample_exams.py  <-- Khởi tạo cấu trúc các bảng đề thi
│
└── README.md                  <-- Tài liệu này
```

---

## 🚀 Hướng Dẫn Sử Dụng Nhanh Từng Nhóm

### 1️⃣ Nhóm 1: Bóc tách tài liệu từ Drive (Word, PDF, TXT)
- **Cách dùng:**
  1. Thả file vào: `scripts/data_extractor/input_files/`
  2. Chạy lệnh:
     ```powershell
     python scripts/data_extractor/extract_data.py
     ```
  3. Chọn `1` để bóc tách **Câu hỏi trắc nghiệm** hoặc `2` để bóc tách **Từ vựng**.

---

### 2️⃣ Nhóm 2: Kiểm tra độ chính xác Dataset (Validator)
- **Kiểm tra file Từ vựng (Vocabulary):**
  ```powershell
  python scripts/data_validator/validate_vocabulary.py csv_templates/vocabulary_template.csv
  ```
  *(Thêm cờ `--online` để check với từ điển trực tuyến, `--auto-fix` để tự sửa lỗi và xuất file sạch).*

- **Kiểm tra file Câu hỏi trắc nghiệm (Questions):**
  ```powershell
  python scripts/data_validator/validate_questions.py csv_templates/questions_template.csv
  ```

---

### 3️⃣ Nhóm 3: Gọi API làm giàu từ vựng trực tuyến (API Enricher)
- **Cách dùng:**
  ```powershell
  python scripts/api_enricher/fetch_vocabulary_api.py
  ```
  Nhập danh sách từ tiếng Anh (ví dụ: `accomplish, resilient, innovate`) ➔ Script sẽ tự động tra IPA, ví dụ, nghĩa tiếng Việt và cho phép lưu thẳng vào PostgreSQL.

---

### 4️⃣ Nhóm 4: Công cụ Database (Database Tools)
- **Đồng bộ và vá bảng Database:**
  ```powershell
  python scripts/database_tools/patch_database.py
  ```
