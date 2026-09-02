"""
validate_vocab.py
=================
Script kiểm tra & đánh giá độ chuẩn xác của file CSV Từ vựng:
1. Đầy đủ các trường bắt buộc (Word, Meaning, IPA, Level, POS...).
2. Phát hiện từ vựng bị trùng lặp (Duplicate check).
3. Kiểm tra tính hợp lệ của Level (A1-C2) và Part of speech (noun, verb, adj, adv...).
4. Kiểm tra logic câu ví dụ tiếng Anh.
5. [Tùy chọn] Đối chiếu từ điển Free Dictionary API.
6. [Tùy chọn] Tự động sửa lỗi / điền giá trị chuẩn và xuất file CSV sạch.

Cách dùng:
    python scripts/validate_vocab.py
    hoặc:
    python scripts/validate_vocab.py csv_templates/vocabulary_template.csv --online --auto-fix
"""

import os
import sys
import csv
import re
import urllib.request
import urllib.parse
import json
import time
from pathlib import Path

# Đảm bảo UTF-8 trên console Windows
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

VALID_LEVELS = {"A1", "A2", "B1", "B2", "C1", "C2"}
VALID_POS = {
    "noun", "verb", "adjective", "adverb", 
    "preposition", "conjunction", "pronoun", 
    "phrase", "idiom", "interjection"
}

POS_MAPPING = {
    "n": "noun", "n.": "noun", "danh từ": "noun",
    "v": "verb", "v.": "verb", "động từ": "verb",
    "adj": "adjective", "adj.": "adjective", "a.": "adjective", "tính từ": "adjective",
    "adv": "adverb", "adv.": "adverb", "phó từ": "adverb", "trạng từ": "adverb",
    "prep": "preposition", "prep.": "preposition", "giới từ": "preposition",
    "conj": "conjunction", "liên từ": "conjunction",
    "pron": "pronoun", "đại từ": "pronoun",
    "phrase": "phrase", "cụm từ": "phrase", "idiom": "idiom"
}


def read_csv_file(file_path: str):
    raw_bytes = open(file_path, "rb").read()
    text = None
    for enc in ["utf-8-sig", "utf-8", "cp1258", "latin-1"]:
        try:
            text = raw_bytes.decode(enc)
            break
        except Exception:
            continue

    if not text:
        raise ValueError("Không thể giải mã file CSV. Vui lòng lưu file ở định dạng UTF-8.")

    sample_line = text.splitlines()[0] if text.splitlines() else ""
    delimiter = ";" if sample_line.count(";") > sample_line.count(",") else ","
    
    reader = csv.DictReader(text.splitlines(), delimiter=delimiter)
    headers = [h.strip().lower() for h in reader.fieldnames or []]
    
    rows = []
    for r in reader:
        clean_row = {str(k).strip().lower(): str(v).strip() if v is not None else "" for k, v in r.items()}
        rows.append(clean_row)

    return headers, rows


def check_word_online_dict(word: str):
    clean_word = word.strip().lower()
    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{urllib.parse.quote(clean_word)}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
            if isinstance(data, list) and len(data) > 0:
                entry = data[0]
                ipa = entry.get("phonetic", "")
                if not ipa and entry.get("phonetics"):
                    for ph in entry["phonetics"]:
                        if ph.get("text"):
                            ipa = ph["text"]
                            break
                pos_list = []
                for m in entry.get("meanings", []):
                    if m.get("partOfSpeech"):
                        pos_list.append(m["partOfSpeech"].lower())
                return {"valid": True, "ipa": ipa, "valid_pos": pos_list}
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {"valid": False, "reason": "Không tìm thấy trong từ điển (Có thể sai chính tả)"}
    except Exception:
        pass
    return {"valid": None, "reason": "Không thể kết nối API (Bỏ qua)"}


def validate_vocabulary_dataset(file_path: str, check_online=False, auto_fix=False):
    print(f"\n========================================================")
    print(f" 🔍 ĐANG KIỂM TRA ĐỘ CHÍNH XÁC DATASET TỪ VỰNG")
    print(f" 📄 File: {file_path}")
    print(f"========================================================")

    if not os.path.exists(file_path):
        print(f"[LỖI] File không tồn tại: {file_path}")
        return

    headers, rows = read_csv_file(file_path)
    total_rows = len(rows)

    if total_rows == 0:
        print("[!] File CSV trống, không có dòng dữ liệu nào.")
        return

    print(f"📊 Tổng số dòng cần kiểm tra: {total_rows}")
    print(f"⚙️  Chế độ Online Dictionary: {'BẬT (Kiểm tra từng từ)' if check_online else 'TẮT (Kiểm tra cấu trúc)'}")
    print(f"⚙️  Chế độ Tự động sửa lỗi: {'BẬT' if auto_fix else 'TẮT'}\n")

    seen_words = {}
    row_reports = []
    fixed_rows = []
    
    total_errors = 0
    total_warnings = 0
    clean_rows_count = 0

    for idx, row in enumerate(rows, start=2):
        errors = []
        warnings = []
        fixed_row = dict(row)

        word = row.get("word", "").strip()
        pronunciation = row.get("pronunciation", "").strip()
        pos = row.get("part_of_speech", "").strip().lower()
        meaning_vi = row.get("meaning_vi", "").strip()
        example_en = row.get("example_en", "").strip()
        example_vi = row.get("example_vi", "").strip()
        level = row.get("level", "").strip().upper()

        if not word:
            errors.append("Cột 'word' bị để trống")
        else:
            word_lower = word.lower()
            if word_lower in seen_words:
                errors.append(f"Từ bị TRÙNG LẶP với dòng {seen_words[word_lower]}")
            else:
                seen_words[word_lower] = idx

            if re.search(r"[0-9_@#$%^&*+=<>{}\[\]|\\]", word):
                warnings.append("Từ vựng chứa ký tự số hoặc ký tự đặc biệt lạ")

        if not meaning_vi:
            errors.append("Cột 'meaning_vi' bị để trống")

        if not pronunciation:
            warnings.append("Cột 'pronunciation' (IPA) đang để trống")
            if auto_fix and word:
                fixed_row["pronunciation"] = f"/{word.lower()}/"

        if not level:
            warnings.append("Cột 'level' để trống (Khuyên dùng: A1, A2, B1, B2, C1, C2)")
            if auto_fix:
                fixed_row["level"] = "B1"
        elif level not in VALID_LEVELS:
            errors.append(f"Level '{level}' không hợp lệ. Phải là một trong: {', '.join(sorted(VALID_LEVELS))}")

        if not pos:
            warnings.append("Cột 'part_of_speech' để trống")
            if auto_fix:
                fixed_row["part_of_speech"] = "noun"
        else:
            if pos in POS_MAPPING:
                pos_normalized = POS_MAPPING[pos]
                if auto_fix:
                    fixed_row["part_of_speech"] = pos_normalized
                pos = pos_normalized
            elif pos not in VALID_POS:
                warnings.append(f"Loại từ '{pos}' chưa chuẩn (Khuyên dùng: noun, verb, adjective, adverb, phrase)")

        if not example_en:
            warnings.append("Cột 'example_en' để trống câu ví dụ")
            if auto_fix and word:
                fixed_row["example_en"] = f"She wants to learn the word '{word}'."
                fixed_row["example_vi"] = f"Cô ấy muốn học từ '{word}'."
        else:
            word_base = word.lower().split()[0] if word else ""
            if word_base and len(word_base) >= 3:
                stem = word_base[:min(len(word_base), 4)]
                if stem not in example_en.lower():
                    warnings.append(f"Câu ví dụ 'example_en' dường như KHÔNG chứa từ '{word}'")

        if example_en and not example_vi:
            warnings.append("Có câu ví dụ tiếng Anh nhưng thiếu bản dịch 'example_vi'")

        if check_online and word and not errors:
            print(f" -> Đang kiểm tra từ '{word}' trên Dictionary API...", end="\r")
            dict_res = check_word_online_dict(word)
            if dict_res.get("valid") is False:
                errors.append(f"Từ điển báo lỗi: {dict_res.get('reason')}")
            elif dict_res.get("valid") is True:
                if not pronunciation and dict_res.get("ipa"):
                    fixed_row["pronunciation"] = dict_res["ipa"]
                online_pos = dict_res.get("valid_pos", [])
                if online_pos and pos and pos not in online_pos:
                    warnings.append(f"Loại từ '{pos}' có thể chưa đúng (Từ điển gợi ý: {', '.join(online_pos)})")
            time.sleep(0.2)

        if errors:
            total_errors += len(errors)
        if warnings:
            total_warnings += len(warnings)

        if not errors and not warnings:
            clean_rows_count += 1

        if errors or warnings:
            row_reports.append({
                "row": idx,
                "word": word or "(Trống)",
                "errors": errors,
                "warnings": warnings
            })

        fixed_rows.append(fixed_row)

    print("\n" + "=" * 56)
    print(" 📋 BÁO CÁO CHI TIẾT TỪNG DÒNG LỖI / CẢNH BÁO:")
    print("=" * 56)

    if not row_reports:
        print(" 🎉 CHÚC MỪNG: 100% DÒNG DỮ LIỆU ĐỀU HỢP LỆ VÀ CHÍNH XÁC!")
    else:
        for rep in row_reports:
            print(f"\n📍 [Dòng {rep['row']}] Từ vựng: '{rep['word']}':")
            for err in rep["errors"]:
                print(f"   ❌ LỖI: {err}")
            for warn in rep["warnings"]:
                print(f"   ⚠️  CẢNH BÁO: {warn}")

    print("\n" + "=" * 56)
    print(" 📊 TỔNG KẾT CHẤT LƯỢNG DATASET:")
    print("=" * 56)
    print(f" - Tổng số dòng:           {total_rows}")
    print(f" - Số dòng hoàn hảo (100%): {clean_rows_count} / {total_rows} ({clean_rows_count/total_rows*100:.1f}%)")
    print(f" - Tổng số Lỗi nghiêm trọng: {total_errors}")
    print(f" - Tổng số Cảnh báo:        {total_warnings}")

    quality_score = max(0, 100 - (total_errors * 10) - (total_warnings * 2))
    print(f" 🏆 ĐIỂM CHẤT LƯỢNG DATASET: {quality_score}/100")
    print("=" * 56)

    if auto_fix:
        dir_name = os.path.dirname(file_path)
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        out_fixed_path = os.path.join(dir_name, f"{base_name}_fixed.csv")
        
        fieldnames = headers if headers else ["word", "pronunciation", "part_of_speech", "meaning_vi", "example_en", "example_vi", "topic", "level", "image_url", "collocations", "synonyms", "antonyms"]
        with open(out_fixed_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(fixed_rows)
        print(f"\n[OK] Đã xuất file dữ liệu đã tự động sửa lỗi ra: {out_fixed_path}")


def main():
    default_path = os.path.join(BASE_DIR, "csv_templates", "vocabulary_template.csv")
    
    if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
        csv_file = sys.argv[1]
    else:
        print(f"File mặc định: {default_path}")
        user_input = input("Nhập đường dẫn file CSV từ vựng cần kiểm tra (nhấn Enter để dùng file mẫu): ").strip()
        csv_file = user_input if user_input else default_path

    check_online = "--online" in sys.argv
    if not check_online and "--no-online" not in sys.argv:
        ans = input("\nBạn có muốn kiểm tra chính tả trực tuyến qua Free Dictionary API không? (y/n) [Mặc định: n]: ").strip().lower()
        check_online = ans in ["y", "yes"]

    auto_fix = "--auto-fix" in sys.argv
    if not auto_fix:
        ans = input("Bạn có muốn bật chế độ tự động chuẩn hóa/sửa lỗi và xuất file *_fixed.csv không? (y/n) [Mặc định: y]: ").strip().lower()
        auto_fix = ans in ["", "y", "yes"]

    validate_vocabulary_dataset(csv_file, check_online=check_online, auto_fix=auto_fix)


if __name__ == "__main__":
    main()
