"""
fetch_vocab.py
==============
Tự động gọi Free Dictionary API và MyMemory Translation API
để lấy phiên âm IPA, định nghĩa, ví dụ, từ đồng nghĩa và tự động dịch sang tiếng Việt.

Sử dụng:
    python scripts/fetch_vocab.py
"""

import os
import sys
import csv
import json
import time
import urllib.request
import urllib.parse
from pathlib import Path

# Đảm bảo UTF-8 trên console Windows
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Thêm đường dẫn root vào sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))


def fetch_word_details(word: str) -> dict:
    clean_word = word.strip().lower()
    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{urllib.parse.quote(clean_word)}"
    
    data = {
        "word": clean_word,
        "pronunciation": f"/{clean_word}/",
        "part_of_speech": "noun",
        "meaning_vi": "",
        "example_en": f"She used the word '{clean_word}' in her speech.",
        "example_vi": f"Cô ấy đã dùng từ '{clean_word}' trong bài phát biểu.",
        "synonyms": "",
        "antonyms": "",
        "collocations": "",
        "topic": "General",
        "level": "B1",
        "image_url": ""
    }

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as response:
            res_json = json.loads(response.read().decode("utf-8"))
            
            if isinstance(res_json, list) and len(res_json) > 0:
                entry = res_json[0]
                
                # Phonetic
                phonetic = entry.get("phonetic", "")
                if not phonetic and entry.get("phonetics"):
                    for ph in entry["phonetics"]:
                        if ph.get("text"):
                            phonetic = ph["text"]
                            break
                if phonetic:
                    data["pronunciation"] = phonetic

                # Meanings
                if entry.get("meanings"):
                    first_meaning = entry["meanings"][0]
                    data["part_of_speech"] = first_meaning.get("partOfSpeech", "noun")
                    
                    syns = first_meaning.get("synonyms", [])
                    if syns:
                        data["synonyms"] = "; ".join(syns[:4])
                    ants = first_meaning.get("antonyms", [])
                    if ants:
                        data["antonyms"] = "; ".join(ants[:3])

                    if first_meaning.get("definitions"):
                        first_def = first_meaning["definitions"][0]
                        en_def = first_def.get("definition", "")
                        en_ex = first_def.get("example", "")
                        if en_ex:
                            data["example_en"] = en_ex
                        
                        vi_trans = translate_to_vietnamese(en_def)
                        if vi_trans:
                            data["meaning_vi"] = vi_trans
                        else:
                            data["meaning_vi"] = en_def
    except Exception:
        data["meaning_vi"] = translate_to_vietnamese(clean_word) or "Nghĩa đang cập nhật"

    if data["example_en"] and not data["example_vi"].startswith("Cô ấy"):
        data["example_vi"] = translate_to_vietnamese(data["example_en"]) or f"Ví dụ cho: {data['example_en']}"

    return data


def translate_to_vietnamese(text: str) -> str:
    if not text:
        return ""
    try:
        query = urllib.parse.quote(text[:300])
        url = f"https://api.mymemory.translated.net/get?q={query}&langpair=en|vi"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("responseData") and data["responseData"].get("translatedText"):
                res = data["responseData"]["translatedText"]
                if "MYMEMORY WARNING" not in res.upper():
                    return res
    except Exception:
        pass
    return ""


def main():
    print("\n========================================================")
    print(" 🌐 TỰ ĐỘNG GỌI API LÀM GIÀU TỪ VỰNG TIẾNG ANH")
    print("========================================================\n")

    words_input = input("Nhập danh sách từ tiếng Anh (ngăn cách bởi dấu phẩy hoặc dấu cách): ").strip()
    if not words_input:
        print("[!] Chưa nhập từ nào.")
        return

    words = [w.strip() for w in words_input.replace(",", " ").split() if w.strip()]
    topic = input("Nhập chủ đề (ví dụ: Business, Travel, Technology) [Mặc định: General]: ").strip() or "General"
    level = input("Nhập cấp độ (A1, A2, B1, B2, C1, C2) [Mặc định: B1]: ").strip() or "B1"

    print(f"\n[*] Đang gọi API xử lý {len(words)} từ vựng...")
    results = []
    for idx, w in enumerate(words, start=1):
        clean_w = w.strip().split()[0]
        print(f" -> [{idx}/{len(words)}] Đang lấy dữ liệu từ: {clean_w}...")
        item = fetch_word_details(clean_w)
        item["topic"] = topic
        item["level"] = level
        results.append(item)
        time.sleep(0.3)

    # Lưu ra CSV
    out_dir = os.path.dirname(__file__)
    out_file = os.path.join(out_dir, "api_enriched_vocabulary.csv")
    fieldnames = ["word", "pronunciation", "part_of_speech", "meaning_vi", "example_en", "example_vi", "topic", "level", "image_url", "collocations", "synonyms", "antonyms"]
    
    with open(out_file, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"\n[OK] Đã xuất {len(results)} từ vựng thành công ra file: {out_file}")

    # Hỏi nạp vào Database PostgreSQL
    save_db = input("\nBạn có muốn nạp thẳng danh sách từ này vào Database PostgreSQL luôn không? (y/n) [Mặc định: y]: ").strip().lower()
    if save_db in ["", "y", "yes"]:
        try:
            from app import create_app, db
            from app.modules.learning.models import Vocabulary
            app = create_app()
            with app.app_context():
                added = 0
                for v in results:
                    word_clean = v["word"].strip()
                    existing = Vocabulary.query.filter(Vocabulary.word.ilike(word_clean)).first()
                    if not existing:
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
                print(f"[THÀNH CÔNG] Đã lưu {added} từ mới trực tiếp vào PostgreSQL!")
        except Exception as e:
            print(f"[Lỗi Database] {e}")


if __name__ == "__main__":
    main()
