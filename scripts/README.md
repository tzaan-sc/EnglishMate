# 🛠️ BỘ CÔNG CỤ TỰ ĐỘNG BÓC TÁCH & NẠP DỮ LIỆU (AUTO EXTRACT & IMPORT TOOL)

Bộ công cụ này giúp bạn:
1. **Tự động đọc các file từ Google Drive:** Hỗ trợ file Word (`.docx`), PDF (`.pdf`), Text (`.txt`, `.md`).
2. **Nhận diện thông minh:** Tự bóc tách các câu hỏi trắc nghiệm, các lựa chọn A/B/C/D, đáp án đúng, giải thích và từ vựng.
3. **Nạp trực tiếp vào PostgreSQL** hoặc xuất ra file CSV chuẩn để kiểm tra.
4. **Gọi API từ vựng trực tuyến:** Tự động lấy IPA, loại từ, câu ví dụ, từ đồng nghĩa và tự dịch sang tiếng Việt.

---

## 📁 Cấu Trúc Thư Mục `scripts/`

```text
scripts/
├── input_files/           <-- Nơi bạn thả các file .docx, .pdf, .txt tải từ Google Drive vào
├── output_csv/            <-- Nơi lưu các file CSV sau khi bóc tách
├── document_parser.py     <-- Thuật toán phân tích cấu trúc văn bản
├── auto_fetch_vocabulary.py <-- Script gọi API từ vựng & dịch nghĩa tự động
├── run_extract.py         <-- Giao diện dòng lệnh chạy trích xuất
└── README.md              <-- Hướng dẫn này
```

---

## 🚀 HƯỚNG DẪN SỬ DỤNG:

### Bước 1: Thả file từ Google Drive vào thư mục `input_files`
- Tải các file Word, PDF hoặc TXT chứa đề thi hoặc danh sách từ vựng trên Drive của bạn về.
- Copy/Paste vào thư mục: [`scripts/input_files/`](file:///d:/GITHUB/web-english/scripts/input_files/).

---

### Bước 2: Chạy lệnh bóc tách dữ liệu
Mở Terminal tại thư mục dự án và chạy:

```powershell
python scripts/run_extract.py
```

---

### Bước 3: Chọn tính năng bạn muốn thực hiện
Hệ thống sẽ hiện menu:
1. **Chọn `1`**: Bóc tách **Câu hỏi trắc nghiệm** (Multiple Choice Questions) ➔ Hệ thống tự nhận diện các câu hỏi, các phương án A/B/C/D, đáp án đúng và phần giải thích.
2. **Chọn `2`**: Bóc tách **Danh sách từ vựng** (Vocabulary).
3. **Chọn `3`**: Nhập danh sách từ tiếng Anh ➔ Tự động gọi API lấy phát âm IPA, nghĩa tiếng Việt, câu ví dụ và nạp vào hệ thống.

Sau khi bóc tách, công cụ sẽ hỏi:
> *"Bạn có muốn nạp trực tiếp vào Database PostgreSQL luôn không? (y/n)"*
- Gõ **`y`** (hoặc Enter): Dữ liệu sẽ được lưu thẳng vào database PostgreSQL của website!
- File CSV cũng được tự động xuất ra thư mục `scripts/output_csv/` để bạn lưu trữ.
