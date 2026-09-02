# 📁 THƯ MỤC CÁC FILE CSV MẪU NHẬP DỮ LIỆU (DATA IMPORT TEMPLATES)

Thư mục này chứa đầy đủ các file CSV mẫu chuẩn hóa cho hệ thống **EnglishMate**, hỗ trợ tiếng Việt có dấu (chuẩn mã hóa UTF-8).

---

## 📑 Danh Sách Các File Mẫu:

| Tên File | Chức Năng | Các Cột Bắt Buộc | Các Cột Tùy Chọn |
| :--- | :--- | :--- | :--- |
| **`vocabulary_template.csv`** | Kho Từ vựng (Vocabulary) | `word`, `pronunciation`, `part_of_speech`, `meaning_vi`, `example_en`, `example_vi`, `topic`, `level` | `image_url`, `collocations`, `synonyms`, `antonyms` |
| **`grammar_template.csv`** | Chủ đề Ngữ pháp (Grammar Topics) | `title`, `category`, `level`, `difficulty`, `summary`, `rule_explanation`, `examples_json` | `common_mistakes`, `tips_tricks` |
| **`lessons_template.csv`** | Bài học (Lessons) | `title`, `level`, `skill`, `short_description`, `content`, `examples` | `thumbnail_url` |
| **`questions_template.csv`** | Ngân hàng Câu hỏi (Questions) | `question_text`, `option_a`, `option_b`, `option_c`, `option_d`, `correct_option`, `explanation`, `topic`, `level` | `skill` |
| **`exams_template.csv`** | Đề thi & Thi thử (Exams) | `category`, `title`, `duration_minutes`, `difficulty`, `skill`, `part`, `question_text`, `option_a`, `option_b`, `option_c`, `option_d`, `correct_answer`, `explanation` | `transcript`, `media_url` |

---

## 📌 Hướng Dẫn Giá Trị Hợp Lệ (Enum / Validation Rules):

- **`level`**: `A1`, `A2`, `B1`, `B2`, `C1`, `C2`
- **`difficulty`**: `Easy`, `Medium`, `Hard`
- **`skill`**: `Grammar`, `Vocabulary`, `Reading`, `Listening`, `Speaking`, `Writing`, `General`
- **`correct_option`** (Questions): `A`, `B`, `C`, `D`
- **`examples_json`** (Grammar): Định dạng chuỗi mảng JSON, ví dụ:
  `[{"en": "I have lived here for 5 years.", "vi": "Tôi đã sống ở đây 5 năm."}]`

---

## 🚀 Cách Thao Tác & Import Vào Hệ Thống:

### Cách 1: Import trực tiếp qua Giao diện Web (Khuyên Dùng)
1. Đăng nhập tài khoản **Admin** trên website.
2. Truy cập vào trang: **`http://127.0.0.1:5000/admin/import`** (Trung tâm Nhập Dữ Liệu).
3. Chọn đúng loại dữ liệu muốn import (Từ vựng, Bài học, Ngữ pháp, Câu hỏi, hoặc Đề thi).
4. Kéo thả hoặc chọn file `.csv` tương ứng từ thư mục này.
5. Hệ thống sẽ **tự động kiểm tra tính hợp lệ (Validation Preview)**, đếm số dòng hợp lệ và cảnh báo dòng lỗi trước khi bạn nhấn nút **Xác nhận Nhập Dữ Liệu**.

---

### Cách 2: Lưu ý khi chỉnh sửa bằng Microsoft Excel
- Khi mở và chỉnh sửa file bằng Excel, lúc lưu lại hãy chọn định dạng: **`CSV UTF-8 (Comma delimited) (*.csv)`** để tránh bị lỗi font tiếng Việt có dấu.
