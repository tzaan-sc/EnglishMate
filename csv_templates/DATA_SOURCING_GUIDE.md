# 🧭 HƯỚNG DẪN TÌM KIẾM VÀ TẠO DỮ LIỆU HỌC TẬP (DATA SOURCING GUIDE)

Tài liệu này cung cấp các nguồn tài nguyên miễn phí, chất lượng cao và các **mẫu Prompt AI (ChatGPT/Claude/Gemini)** để bạn tạo hàng trăm đến hàng nghìn bản ghi dữ liệu chỉ trong vài phút.

---

## 🌐 1. CÁC NGUỒN TÀI NGUYÊN MIỄN PHÍ VÀ CHUẨN QUỐC TẾ

### 📚 A. Từ Vựng (Vocabulary) & Flashcards
1. **Oxford 3000™ & 5000™ / CEFR Wordlists:**
   - Danh sách từ vựng chuẩn từ A1 đến C2 phân loại khoa học nhất thế giới.
   - Link tra cứu: [oxfordlearnersdictionaries.com/wordlists](https://www.oxfordlearnersdictionaries.com/wordlists/)
2. **AnkiWeb Shared Decks (Kho Flashcard khổng lồ):**
   - Truy cập [ankiweb.net/shared/decks](https://ankiweb.net/shared/decks/) và tìm từ khóa: `TOEIC 600`, `IELTS 4000 Essential English Words`, `Oxford 3000`.
   - Có thể tải về và dùng phần mềm Anki xuất ra file `.txt` / `.csv` rất nhanh.
3. **Cambridge Dictionary Online:**
   - Tra cứu phát âm IPA, từ loại, câu ví dụ chuẩn Anh - Mỹ: [dictionary.cambridge.org](https://dictionary.cambridge.org/)

---

### 📝 B. Đề Thi & Ngân Hàng Câu Hỏi (TOEIC, IELTS, THPT)
1. **Đề thi TOEIC:**
   - Các bộ đề chuẩn ETS TOEIC (Part 5: Hoàn thành câu, Part 6: Điền đoạn văn, Part 7: Đọc hiểu).
   - Nguồn tham khảo: Sách ETS TOEIC RC 1000, Hacker TOEIC.
2. **Đề thi THPT Quốc Gia:**
   - Đề thi chính thức của Bộ GD&ĐT qua các năm và đề thi thử của các trường THPT Chuyên (Hà Nội - Amsterdam, Lê Hồng Phong, v.v.).
3. **Cambridge IELTS Academic & General Training:**
   - Các bài đọc Passage 1, 2, 3 và câu hỏi trắc nghiệm Multiple Choice.

---

### 📖 C. Ngữ Pháp (Grammar) & Bài Học (Lessons)
1. **BBC Learning English:** [bbc.co.uk/learningenglish](https://www.bbc.co.uk/learningenglish/) (Rất nhiều bài học theo cấp độ từ Basic đến Advanced).
2. **British Council LearnEnglish:** [learnenglish.britishcouncil.org](https://learnenglish.britishcouncil.org/) (Ngữ pháp, từ vựng và bài tập trực tuyến).
3. **English Grammar in Use (Raymond Murphy):** Giáo trình ngữ pháp kinh điển, giải thích ngắn gọn, dễ hiểu.

---

### 🖼️ D. Hình Ảnh & Âm Thanh
1. **Hình ảnh minh họa:** Dùng link ảnh trực tiếp từ [Unsplash](https://unsplash.com) hoặc [Pexels](https://pexels.com) (miễn phí bản quyền).
2. **Âm thanh phát âm:** Hệ thống EnglishMate đã tích hợp sẵn **Web Speech API** chuẩn quốc tế (giọng đọc US/UK tự nhiên), nên bạn chỉ cần điền từ tiếng Anh và phiên âm IPA là hệ thống tự phát âm chuẩn.

---

## 🤖 2. DÙNG AI (CHATGPT / CLAUDE / GEMINI) ĐỂ TẠO DỮ LIỆU TỰ ĐỘNG

Dưới đây là các **mẫu Prompt (Câu lệnh)** bạn chỉ cần copy, dán vào ChatGPT hoặc Gemini để tạo ra dữ liệu chuẩn định dạng CSV của hệ thống:

---

### 🎯 Prompt 1: Tạo Danh Sách Từ Vựng (Vocabulary)
```text
Bạn là một chuyên gia ngôn ngữ tiếng Anh. Hãy tạo cho tôi [20] từ vựng tiếng Anh chủ đề [Công sở / Business / Du lịch / Công nghệ] ở trình độ [B1 / B2].

Hãy xuất kết quả dưới dạng bảng dữ liệu CSV (ngăn cách bởi dấu phẩy, các cột có chứa dấu phẩy thì đặt trong dấu ngoặc kép ""), với đúng thứ tự các cột như sau:
word,pronunciation,part_of_speech,meaning_vi,example_en,example_vi,topic,level,image_url,collocations,synonyms,antonyms

Yêu cầu:
- level: chọn 1 trong các giá trị [A1, A2, B1, B2, C1, C2]
- part_of_speech: noun, verb, adjective, adverb
- meaning_vi: nghĩa tiếng Việt súc tích
- collocations: 2-3 cụm từ hay đi kèm (ngăn cách bởi dấu chấm phẩy ;)
- synonyms: các từ đồng nghĩa (ngăn cách bởi dấu chấm phẩy ;)
- antonyms: các từ trái nghĩa (ngăn cách bởi dấu chấm phẩy ;)
- Chỉ in ra nội dung mã CSV trong khối code block để tôi copy thẳng vào file vocabulary_template.csv.
```

---

### 🎯 Prompt 2: Tạo Ngân Hàng Câu Hỏi Trắc Nghiệm (Questions Bank)
```text
Hãy tạo cho tôi [15] câu hỏi trắc nghiệm tiếng Anh 4 lựa chọn (A, B, C, D) kiểm tra về [Ngữ pháp Thì / Mệnh đề quan hệ / Từ vựng TOEIC] ở trình độ [B1].

Hãy xuất kết quả dưới dạng CSV đúng định dạng sau:
question_text,option_a,option_b,option_c,option_d,correct_option,explanation,topic,level,skill

Yêu cầu:
- correct_option: Chỉ ghi 1 chữ cái in hoa [A, B, C, hoặc D]
- explanation: Giải thích chi tiết bằng tiếng Việt tại sao chọn đáp án đó và tại sao các đáp án khác sai
- topic: Tên chủ đề ngắn gọn (ví dụ: Tenses, Vocabulary, Prepositions)
- level: A1, A2, B1, B2, C1 hoặc C2
- skill: Grammar hoặc Vocabulary
- Bọc nội dung các cột có dấu phẩy trong dấu ngoặc kép "".
```

---

### 🎯 Prompt 3: Tạo Chủ Đề Ngữ Pháp (Grammar Topics)
```text
Hãy soạn cho tôi nội dung [5] bài ngữ pháp tiếng Anh quan trọng trình độ [B1] (Ví dụ: Present Perfect, Passive Voice, Conditionals, Relative Clauses, Reported Speech).

Xuất ra dưới dạng CSV chuẩn theo định dạng sau:
title,category,level,difficulty,summary,rule_explanation,examples_json,common_mistakes,tips_tricks

Yêu cầu:
- difficulty: Easy, Medium, hoặc Hard
- examples_json: Phải là chuỗi JSON hợp lệ gồm mảng các ví dụ Anh - Việt, ví dụ: "[{\"en\": \"I have seen him.\", \"vi\": \"Tôi đã gặp anh ấy.\"}]"
- common_mistakes: Lỗi học viên hay mắc phải kèm ví dụ sai và cách sửa
- tips_tricks: Mẹo nhớ nhanh hoặc câu thần chú làm bài
```

---

### 🎯 Prompt 4: Tạo Đề Thi Trắc Nghiệm (Exams)
```text
Hãy tạo cho tôi [10] câu hỏi trắc nghiệm chuẩn format đề thi [TOEIC Reading Part 5 / THPT Quốc Gia] ở mức độ [Medium].

Xuất ra dưới dạng CSV với các cột:
category,title,duration_minutes,difficulty,skill,part,question_text,option_a,option_b,option_c,option_d,correct_answer,explanation,transcript,media_url

Yêu cầu:
- category: TOEIC, IELTS, THPT, hoặc Custom
- correct_answer: Ghi chính xác nội dung chữ của đáp án đúng (ví dụ: "were", "despite", "substantially")
- explanation: Giải thích chi tiết bằng tiếng Việt.
```

---

## ⚡ 3. CÁC BƯỚC NHANH ĐỂ NẠP DỮ LIỆU HÀNG LOẠT:
1. Mở ChatGPT/Gemini, copy một trong các Prompt ở trên và thay đổi chủ đề / số lượng câu bạn muốn.
2. Copy kết quả CSV mà AI trả về.
3. Mở file CSV tương ứng trong thư mục `sample_csv_templates/` bằng Notepad, VS Code hoặc Excel và dán thêm vào bên dưới dòng tiêu đề (Header).
4. Vào trang web **Admin** ➔ **Trung tâm Nhập Dữ Liệu (`/admin/import`)** ➔ Chọn file và nhấn Upload!
