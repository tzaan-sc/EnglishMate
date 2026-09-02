"""
validate_questions.py
=====================
Script chuyên dụng để kiểm tra tính chính xác của file CSV Ngân hàng Câu hỏi Trắc nghiệm:
1. Đảm bảo có đủ 4 lựa chọn A, B, C, D.
2. Kiểm tra đáp án đúng (correct_option) có khớp với A, B, C, D không.
3. Kiểm tra câu hỏi trùng lặp.
4. Kiểm tra cấp độ (A1-C2) và giải thích (explanation).

Cách dùng:
    python scripts/2_data_validator/validate_questions.py
"""

import os
import sys
import csv
import re
from pathlib import Path

# Đảm bảo UTF-8 trên console Windows
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

VALID_LEVELS = {"A1", "A2", "B1", "B2", "C1", "C2"}
VALID_OPTIONS = {"A", "B", "C", "D"}


def validate_questions_dataset(file_path: str):
    print(f"\n========================================================")
    print(f" 🔍 ĐANG KIỂM TRA ĐỘ CHÍNH XÁC NGÂN HÀNG CÂU HỎI")
    print(f" 📄 File: {file_path}")
    print(f"========================================================")

    if not os.path.exists(file_path):
        print(f"[LỖI] File không tồn tại: {file_path}")
        return

    raw_bytes = open(file_path, "rb").read()
    text = None
    for enc in ["utf-8-sig", "utf-8", "cp1258", "latin-1"]:
        try:
            text = raw_bytes.decode(enc)
            break
        except Exception:
            continue

    if not text:
        print("[LỖI] Không thể giải mã file CSV UTF-8.")
        return

    sample_line = text.splitlines()[0] if text.splitlines() else ""
    delimiter = ";" if sample_line.count(";") > sample_line.count(",") else ","
    reader = csv.DictReader(text.splitlines(), delimiter=delimiter)

    rows = []
    for r in reader:
        rows.append({str(k).strip().lower(): str(v).strip() if v is not None else "" for k, v in r.items()})

    total_rows = len(rows)
    print(f"📊 Tổng số câu hỏi cần kiểm tra: {total_rows}\n")

    seen_questions = {}
    row_reports = []
    total_errors = 0
    total_warnings = 0
    clean_count = 0

    for idx, row in enumerate(rows, start=2):
        errors = []
        warnings = []

        q_text = row.get("question_text", "").strip()
        opt_a = row.get("option_a", "").strip()
        opt_b = row.get("option_b", "").strip()
        opt_c = row.get("option_c", "").strip()
        opt_d = row.get("option_d", "").strip()
        correct_opt = row.get("correct_option", "").strip().upper()
        explanation = row.get("explanation", "").strip()
        level = row.get("level", "").strip().upper()

        if not q_text:
            errors.append("Nội dung câu hỏi 'question_text' bị để trống")
        else:
            q_clean = q_text.lower()
            if q_clean in seen_questions:
                errors.append(f"Câu hỏi bị TRÙNG LẶP với dòng {seen_questions[q_clean]}")
            else:
                seen_questions[q_clean] = idx

        # Kiểm tra Options
        if not opt_a: errors.append("Phương án 'option_a' bị trống")
        if not opt_b: errors.append("Phương án 'option_b' bị trống")
        if not opt_c: errors.append("Phương án 'option_c' bị trống")
        if not opt_d: errors.append("Phương án 'option_d' bị trống")

        # Kiểm tra trùng options trong cùng 1 câu
        opts_list = [opt_a, opt_b, opt_c, opt_d]
        opts_non_empty = [o for o in opts_list if o]
        if len(opts_non_empty) != len(set(opts_non_empty)):
            warnings.append("Có các phương án lựa chọn trùng lặp nội dung với nhau")

        # Kiểm tra Đáp án đúng
        if not correct_opt:
            errors.append("Đáp án đúng 'correct_option' bị để trống")
        elif correct_opt not in VALID_OPTIONS:
            errors.append(f"Đáp án đúng '{correct_opt}' không hợp lệ. Phải là A, B, C, hoặc D")

        # Kiểm tra Level
        if level and level not in VALID_LEVELS:
            errors.append(f"Level '{level}' không hợp lệ. Phải là A1-C2")

        # Kiểm tra Giải thích
        if not explanation:
            warnings.append("Thiếu phần giải thích đáp án 'explanation'")

        if errors: total_errors += len(errors)
        if warnings: total_warnings += len(warnings)
        if not errors and not warnings: clean_count += 1

        if errors or warnings:
            row_reports.append({
                "row": idx,
                "q_text": q_text[:50] + "..." if len(q_text) > 50 else q_text,
                "errors": errors,
                "warnings": warnings
            })

    print("=" * 56)
    print(" 📋 BÁO CÁO CHI TIẾT TỪNG CÂU HỎI LỖI / CẢNH BÁO:")
    print("=" * 56)

    if not row_reports:
        print(" 🎉 CHÚC MỪNG: 100% CÂU HỎI ĐỀU HỢP LỆ VÀ CHÍNH XÁC!")
    else:
        for rep in row_reports:
            print(f"\n📍 [Dòng {rep['row']}] Câu hỏi: '{rep['q_text']}':")
            for err in rep["errors"]:
                print(f"   ❌ LỖI: {err}")
            for warn in rep["warnings"]:
                print(f"   ⚠️  CẢNH BÁO: {warn}")

    print("\n" + "=" * 56)
    print(" 📊 TỔNG KẾT CHẤT LƯỢNG:")
    print("=" * 56)
    print(f" - Tổng số câu hỏi:        {total_rows}")
    print(f" - Số câu hoàn hảo (100%): {clean_count} / {total_rows} ({clean_count/total_rows*100:.1f}%)")
    print(f" - Tổng số Lỗi:            {total_errors}")
    print(f" - Tổng số Cảnh báo:       {total_warnings}")
    
    score = max(0, 100 - (total_errors * 10) - (total_warnings * 2))
    print(f" 🏆 ĐIỂM CHẤT LƯỢNG: {score}/100")
    print("=" * 56)


def main():
    root_dir = Path(__file__).resolve().parent.parent.parent
    default_path = os.path.join(root_dir, "csv_templates", "questions_template.csv")
    
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
    else:
        print(f"File mặc định: {default_path}")
        user_input = input("Nhập đường dẫn file CSV câu hỏi (nhấn Enter để dùng file mẫu): ").strip()
        csv_file = user_input if user_input else default_path

    validate_questions_dataset(csv_file)


if __name__ == "__main__":
    main()
