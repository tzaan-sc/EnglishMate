"""
run_extract.py
==============
Công cụ chạy trích xuất tự động tài liệu Word (.docx), PDF (.pdf), Text (.txt) từ Google Drive
hoặc gọi API từ vựng tự động nạp thẳng vào PostgreSQL / xuất file CSV.

Sử dụng:
    python scripts/run_extract.py
"""

import os
import sys
import csv
from pathlib import Path

# Ensure UTF-8 stdout on Windows console
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Thêm đường dẫn root vào sys.path để gọi Flask app
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from scripts.document_parser import extract_text_from_file, parse_questions_from_text, parse_vocabulary_from_text
from scripts.auto_fetch_vocabulary import process_word_list

INPUT_DIR = os.path.join(os.path.dirname(__file__), "input_files")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output_csv")

os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


def save_to_csv(filename: str, fieldnames: list, rows: list):
    out_path = os.path.join(OUTPUT_DIR, filename)
    with open(out_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"\n[OK] Đã xuất {len(rows)} bản ghi thành công ra file: {out_path}")
    return out_path


def import_questions_to_db(questions: list):
    try:
        from app import create_app, db
        from app.modules.learning.models import Question
        app = create_app()
        with app.app_context():
            added = 0
            for q in questions:
                # Kiểm tra trùng lặp
                existing = Question.query.filter_by(question_text=q["question_text"]).first()
                if not existing:
                    new_q = Question(
                        question_text=q["question_text"],
                        option_a=q["option_a"],
                        option_b=q["option_b"],
                        option_c=q["option_c"],
                        option_d=q["option_d"],
                        correct_option=q["correct_option"],
                        explanation=q["explanation"],
                        topic=q.get("topic", "General"),
                        level=q.get("level", "B1")
                    )
                    db.session.add(new_q)
                    added += 1
            db.session.commit()
            print(f"[THÀNH CÔNG] Đã lưu {added} câu hỏi mới trực tiếp vào PostgreSQL!")
    except Exception as e:
        print(f"[Lỗi Database] {e}")


def import_vocabulary_to_db(vocab_list: list):
    try:
        from app import create_app, db
        from app.modules.learning.models import Vocabulary
        app = create_app()
        with app.app_context():
            added = 0
            updated = 0
            for v in vocab_list:
                word_clean = v["word"].strip()
                existing = Vocabulary.query.filter(Vocabulary.word.ilike(word_clean)).first()
                if existing:
                    existing.meaning_vi = v.get("meaning_vi", existing.meaning_vi)
                    existing.pronunciation = v.get("pronunciation", existing.pronunciation)
                    existing.example_en = v.get("example_en", existing.example_en)
                    existing.example_vi = v.get("example_vi", existing.example_vi)
                    updated += 1
                else:
                    new_v = Vocabulary(
                        word=word_clean,
                        pronunciation=v.get("pronunciation", f"/{word_clean}/"),
                        part_of_speech=v.get("part_of_speech", "noun"),
                        meaning_vi=v.get("meaning_vi", ""),
                        example_en=v.get("example_en", ""),
                        example_vi=v.get("example_vi", ""),
                        topic=v.get("topic", "General"),
                        level=v.get("level", "B1"),
                        synonyms=v.get("synonyms") or None,
                        antonyms=v.get("antonyms") or None,
                        collocations=v.get("collocations") or None
                    )
                    db.session.add(new_v)
                    added += 1
            db.session.commit()
            print(f"[THÀNH CÔNG] Đã nạp {added} từ mới và cập nhật {updated} từ vào PostgreSQL!")
    except Exception as e:
        print(f"[Lỗi Database] {e}")


def process_all_input_files():
    files = [f for f in os.listdir(INPUT_DIR) if os.path.isfile(os.path.join(INPUT_DIR, f)) and not f.startswith(".")]
    if not files:
        print(f"\n[!] Thư mục 'scripts/input_files/' hiện chưa có file tài liệu nào.")
        print(f"    👉 Hãy chép các file Word (.docx), PDF (.pdf) hoặc Text (.txt) từ Google Drive vào thư mục đó trước rồi chạy lại nhé!")
        return

    print(f"\n=======================================================")
    print(f" Tìm thấy {len(files)} file tài liệu trong 'scripts/input_files/':")
    for idx, f in enumerate(files, 1):
        print(f"   [{idx}] {f}")
    print(f"=======================================================\n")

    print("Chọn hành động bạn muốn thực hiện:")
    print(" 1. Bóc tách CÂU HỎI TRẮC NGHIỆM (Multiple Choice Questions)")
    print(" 2. Bóc tách DANH SÁCH TỪ VỰNG (Vocabulary List)")
    print(" 3. Nhập trực tiếp danh sách từ vựng tiếng Anh -> Tự gọi API làm giàu dữ liệu")
    
    choice = input("\nNhập lựa chọn (1/2/3) [Mặc định: 1]: ").strip() or "1"

    all_raw_text = []
    for f in files:
        file_path = os.path.join(INPUT_DIR, f)
        print(f" -> Đang đọc file: {f}...")
        txt = extract_text_from_file(file_path)
        if txt:
            all_raw_text.append(txt)

    combined_text = "\n\n".join(all_raw_text)

    if choice == "1":
        topic = input("Nhập chủ đề cho câu hỏi (ví dụ: TOEIC, Grammar, Tenses) [Mặc định: General]: ").strip() or "General"
        level = input("Nhập trình độ (A1, A2, B1, B2, C1, C2) [Mặc định: B1]: ").strip() or "B1"
        
        print("\n[*] Đang phân tích và bóc tách câu hỏi...")
        questions = parse_questions_from_text(combined_text, default_topic=topic, default_level=level)
        print(f"[OK] Đã tìm thấy và bóc tách thành công {len(questions)} câu hỏi trắc nghiệm!")

        if questions:
            # Lưu CSV
            fields = ["question_text", "option_a", "option_b", "option_c", "option_d", "correct_option", "explanation", "topic", "level", "skill"]
            csv_path = save_to_csv("questions_extracted.csv", fields, questions)

            # Hỏi nạp vào DB
            save_db = input("\nBạn có muốn nạp trực tiếp toàn bộ câu hỏi này vào Database PostgreSQL luôn không? (y/n) [Mặc định: y]: ").strip().lower()
            if save_db in ["", "y", "yes"]:
                import_questions_to_db(questions)

    elif choice == "2":
        topic = input("Nhập chủ đề từ vựng (ví dụ: Workplace, Business, Daily) [Mặc định: General]: ").strip() or "General"
        level = input("Nhập trình độ (A1, A2, B1, B2, C1, C2) [Mặc định: B1]: ").strip() or "B1"

        print("\n[*] Đang phân tích và bóc tách từ vựng...")
        vocab_list = parse_vocabulary_from_text(combined_text, default_topic=topic, default_level=level)
        print(f"[OK] Đã bóc tách thành công {len(vocab_list)} từ vựng!")

        if vocab_list:
            fields = ["word", "pronunciation", "part_of_speech", "meaning_vi", "example_en", "example_vi", "topic", "level", "image_url", "collocations", "synonyms", "antonyms"]
            save_to_csv("vocabulary_extracted.csv", fields, vocab_list)

            save_db = input("\nBạn có muốn nạp trực tiếp danh sách từ này vào Database PostgreSQL luôn không? (y/n) [Mặc định: y]: ").strip().lower()
            if save_db in ["", "y", "yes"]:
                import_vocabulary_to_db(vocab_list)

    elif choice == "3":
        words_input = input("\nNhập các từ tiếng Anh cần tra (ngăn cách bởi dấu phẩy hoặc khoảng trắng): ").strip()
        if words_input:
            word_tokens = [w.strip() for w in words_input.replace(",", " ").split() if w.strip()]
            topic = input("Nhập chủ đề [Mặc định: General]: ").strip() or "General"
            level = input("Nhập trình độ (A1-C2) [Mặc định: B1]: ").strip() or "B1"

            enriched_vocab = process_word_list(word_tokens, topic=topic, level=level)
            fields = ["word", "pronunciation", "part_of_speech", "meaning_vi", "example_en", "example_vi", "topic", "level", "image_url", "collocations", "synonyms", "antonyms"]
            save_to_csv("api_vocabulary_generated.csv", fields, enriched_vocab)

            save_db = input("\nBạn có muốn nạp trực tiếp danh sách từ này vào Database PostgreSQL luôn không? (y/n) [Mặc định: y]: ").strip().lower()
            if save_db in ["", "y", "yes"]:
                import_vocabulary_to_db(enriched_vocab)


if __name__ == "__main__":
    process_all_input_files()
