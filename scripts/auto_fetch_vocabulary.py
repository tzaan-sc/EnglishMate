"""
auto_fetch_vocabulary.py
========================
Tự động gọi Free Dictionary API và Google/MyMemory Translation API
để lấy phiên âm IPA, định nghĩa, ví dụ, từ đồng nghĩa và tự động dịch sang tiếng Việt.
"""

import urllib.request
import urllib.parse
import json
import time
import sys

# Ensure UTF-8 stdout on Windows console
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def fetch_word_details(word: str) -> dict:
    """
    Gọi Free Dictionary API để lấy IPA, part of speech, ví dụ, từ đồng nghĩa.
    """
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
        "level": "B1"
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
                    
                    # Synonyms / Antonyms
                    syns = first_meaning.get("synonyms", [])
                    if syns:
                        data["synonyms"] = "; ".join(syns[:4])
                    ants = first_meaning.get("antonyms", [])
                    if ants:
                        data["antonyms"] = "; ".join(ants[:3])

                    # Definitions & Examples
                    if first_meaning.get("definitions"):
                        first_def = first_meaning["definitions"][0]
                        en_def = first_def.get("definition", "")
                        en_ex = first_def.get("example", "")
                        if en_ex:
                            data["example_en"] = en_ex
                        
                        # Dịch định nghĩa sang tiếng Việt
                        vi_trans = translate_to_vietnamese(en_def)
                        if vi_trans:
                            data["meaning_vi"] = vi_trans
                        else:
                            data["meaning_vi"] = en_def
    except Exception as e:
        # Fallback dịch nghĩa trực tiếp nếu API dictionary không có
        data["meaning_vi"] = translate_to_vietnamese(clean_word) or "Nghĩa đang cập nhật"

    # Dịch câu ví dụ sang tiếng Việt
    if data["example_en"] and not data["example_vi"].startswith("Cô ấy"):
        data["example_vi"] = translate_to_vietnamese(data["example_en"]) or f"Ví dụ cho: {data['example_en']}"

    return data


def translate_to_vietnamese(text: str) -> str:
    """
    Dịch tự động sang tiếng Việt qua MyMemory Translation API (Miễn phí 5000 ký tự/ngày).
    """
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


def process_word_list(words: list, topic="General", level="B1") -> list:
    """
    Duyệt danh sách từ và làm giàu dữ liệu tự động.
    """
    results = []
    total = len(words)
    print(f"[*] Bắt đầu xử lý {total} từ vựng qua Free Dictionary API...")
    
    for idx, w in enumerate(words, start=1):
        if not w.strip():
            continue
        clean_w = w.strip().split()[0]  # Lấy từ đầu tiên nếu là cụm
        print(f" -> [{idx}/{total}] Đang lấy dữ liệu từ: {clean_w}...")
        item = fetch_word_details(clean_w)
        item["topic"] = topic
        item["level"] = level
        results.append(item)
        time.sleep(0.3)  # Tránh spam rate limit

    return results
