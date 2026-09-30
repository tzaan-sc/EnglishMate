"""
Grammar & Spell Checker Engine for EnglishMate Writing Studio.
Integrates with LanguageTool API with robust local rule-based fallback.
"""

import re
import requests
from typing import List, Dict, Any

# LanguageTool Public API endpoint
LANGUAGETOOL_API_URL = "https://api.languagetool.org/v2/check"

# Common English misspellings and their corrections
COMMON_MISSPELLINGS: Dict[str, List[str]] = {
    "teh": ["the"],
    "recieve": ["receive"],
    "recieved": ["received"],
    "recieving": ["receiving"],
    "seperate": ["separate"],
    "seperated": ["separated"],
    "seperation": ["separation"],
    "definately": ["definitely"],
    "definatly": ["definitely"],
    "goverment": ["government"],
    "accomodate": ["accommodate"],
    "accomodation": ["accommodation"],
    "occured": ["occurred"],
    "occuring": ["occurring"],
    "untill": ["until"],
    "truely": ["truly"],
    "tommorow": ["tomorrow"],
    "tommorrow": ["tomorrow"],
    "enviroment": ["environment"],
    "neccessary": ["necessary"],
    "necesary": ["necessary"],
    "writting": ["writing"],
    "grammer": ["grammar"],
    "sucessful": ["successful"],
    "sucessfully": ["successfully"],
    "beleive": ["believe"],
    "beleived": ["believed"],
    "alot": ["a lot"],
    "becuase": ["because"],
    "thier": ["their"],
    "freind": ["friend"],
    "freinds": ["friends"],
    "wich": ["which"],
    "allways": ["always"],
    "realy": ["really"],
    "peaple": ["people"],
    "studing": ["studying"],
    "intrested": ["interested"],
    "intresting": ["interesting"],
    "knowlege": ["knowledge"],
    "experiance": ["experience"],
    "diffrent": ["different"],
    "diferent": ["different"],
    "existance": ["existence"],
    "occurance": ["occurrence"],
    "prefered": ["preferred"],
    "refered": ["referred"],
    "begining": ["beginning"],
    "practise": ["practice"],
    "pronounciation": ["pronunciation"],
    "convinient": ["convenient"],
    "embarass": ["embarrass"],
    "embarassed": ["embarrassed"],
    "embarassing": ["embarrassing"],
    "heigth": ["height"],
    "wierd": ["weird"],
    "rythm": ["rhythm"],
    "calender": ["calendar"],
    "foriegn": ["foreign"],
    "guarentee": ["guarantee"],
    "garantee": ["guarantee"],
    "happend": ["happened"],
    "interupt": ["interrupt"],
    "liason": ["liaison"],
    "millenium": ["millennium"],
    "noticable": ["noticeable"],
    "ocassion": ["occasion"],
    "ocasionally": ["occasionally"],
    "posession": ["possession"],
    "priviledge": ["privilege"],
    "recommand": ["recommend"],
    "recomended": ["recommended"],
    "religous": ["religious"],
    "restaraunt": ["restaurant"],
    "resturant": ["restaurant"],
    "schedual": ["schedule"],
    "succes": ["success"],
    "tendancy": ["tendency"],
    "unfortunatly": ["unfortunately"],
    "vehical": ["vehicle"],
    "weather": ["whether"], # context dependent
}

# Common grammatical confusions
GRAMMAR_PATTERNS = [
    # Subject-verb agreement (singular third person)
    (
        r"\b(he|she|it)\s+(have)\b",
        "has",
        "Động từ số ít với chủ ngữ ngôi thứ ba số ít (he/she/it) nên dùng 'has' thay vì 'have'.",
        "Grammar / Subject-Verb Agreement"
    ),
    (
        r"\b(he|she|it)\s+(do\s+not|don't)\b",
        "doesn't",
        "Với chủ ngữ ngôi thứ ba số ít (he/she/it), sử dụng trợ động từ phủ định 'doesn't'.",
        "Grammar / Subject-Verb Agreement"
    ),
    (
        r"\b(he|she|it)\s+(go)\b",
        "goes",
        "Động từ 'go' với ngôi thứ ba số ít cần thêm 'es' thành 'goes'.",
        "Grammar / Subject-Verb Agreement"
    ),
    (
        r"\b(they|we|you)\s+(has)\b",
        "have",
        "Chủ ngữ số nhiều (they/we/you) đi với động từ 'have'.",
        "Grammar / Subject-Verb Agreement"
    ),
    (
        r"\b(they|we|you)\s+(is)\b",
        "are",
        "Chủ ngữ số nhiều (they/we/you) đi với động từ 'are'.",
        "Grammar / Subject-Verb Agreement"
    ),
    (
        r"\b(they|we|you)\s+(does\s+not|doesn't)\b",
        "don't",
        "Chủ ngữ số nhiều (they/we/you) sử dụng trợ động từ phủ định 'don't'.",
        "Grammar / Subject-Verb Agreement"
    ),
    (
        r"\b(I)\s+(has)\b",
        "have",
        "Chủ ngữ 'I' đi với động từ 'have' trong thì hiện tại hoàn thành / sở hữu.",
        "Grammar / Subject-Verb Agreement"
    ),
    (
        r"\b(I)\s+(is)\b",
        "am",
        "Chủ ngữ 'I' đi với động từ to-be 'am'.",
        "Grammar / Subject-Verb Agreement"
    ),
    # Confused words
    (
        r"\b(your)\s+(welcome|right|wrong|correct|beautiful|doing|going)\b",
        "you're",
        "Bạn có thể đang muốn dùng từ viết tắt 'you're' (you are) thay cho tính từ sở hữu 'your'.",
        "Word Choice / Confused Words"
    ),
    (
        r"\b(their)\s+(is|are|was|were)\b",
        "there",
        "Sử dụng 'there is/there are' để chỉ sự tồn tại thay vì tính từ sở hữu 'their'.",
        "Word Choice / Confused Words"
    ),
    (
        r"\b(they're)\s+([a-z]+(?:s|book|house|car|money|dog|friend))\b",
        "their",
        "Kiểm tra xem bạn có muốn dùng tính từ sở hữu 'their' thay vì 'they're' (they are).",
        "Word Choice / Confused Words"
    ),
    (
        r"\b(its)\s+(a|an|the|very|not|so|really|good|great|bad)\b",
        "it's",
        "Sử dụng dạng rút gọn 'it's' (it is/it has) thay vì đại từ sở hữu 'its'.",
        "Word Choice / Confused Words"
    ),
    (
        r"\b(loose)\s+(weight|money|time|my|the|game|match)\b",
        "lose",
        "Sử dụng động từ 'lose' (thua, mất) thay vì tính từ 'loose' (lỏng lẻo).",
        "Word Choice / Confused Words"
    ),
    (
        r"\b(better|more|less|faster|slower|bigger|smaller|higher|lower)\s+(then)\b",
        "than",
        "Dùng 'than' trong cấu trúc so sánh hơn (better than, more than...).",
        "Grammar / Comparison"
    ),
]


def check_with_local_rules(text: str) -> List[Dict[str, Any]]:
    """
    Fast rule-based local grammar and spell checker.
    """
    matches = []
    if not text or not text.strip():
        return matches

    # 1. Check Repeated / Duplicated words (e.g. "the the", "in in")
    repeat_pattern = re.compile(r"\b([a-zA-Z]+)\s+\1\b", re.IGNORECASE)
    for m in repeat_pattern.finditer(text):
        word = m.group(1)
        matches.append({
            "offset": m.start(),
            "length": m.end() - m.start(),
            "message": f"Từ '{word}' bị lặp lại 2 lần liên tiếp.",
            "short_message": "Từ bị lặp",
            "replacements": [word],
            "rule_id": "REPEATED_WORD",
            "category": "Redundancy",
            "error_type": "style"
        })

    # 2. Check Lowercase 'i' pronoun (e.g. "i am", "when i went")
    i_pattern = re.compile(r"(^|\s)(i)('m|'ve|'ll|'d|\b)", re.IGNORECASE)
    for m in re.finditer(r"(^|\s)(i)(\s|$|[.,!?;])", text):
        if m.group(2) == "i":
            offset = m.start(2)
            matches.append({
                "offset": offset,
                "length": 1,
                "message": "Đại từ nhân xưng 'I' trong tiếng Anh luôn phải viết hoa.",
                "short_message": "Viết hoa đại từ 'I'",
                "replacements": ["I"],
                "rule_id": "PRONOUN_I_CAPITALIZATION",
                "category": "Capitalization",
                "error_type": "grammar"
            })

    # 3. Check Sentence Initial Capitalization
    # Match start of text or after .!? followed by whitespace
    sentence_start_pattern = re.compile(r"(?:^|[.!?]\s+)([a-z])")
    for m in sentence_start_pattern.finditer(text):
        char = m.group(1)
        # Position of the single character
        char_offset = m.end() - 1
        matches.append({
            "offset": char_offset,
            "length": 1,
            "message": f"Chữ cái đầu câu '{char}' nên được viết hoa.",
            "short_message": "Viết hoa đầu câu",
            "replacements": [char.upper()],
            "rule_id": "SENTENCE_START_CAPITALIZATION",
            "category": "Capitalization",
            "error_type": "grammar"
        })

    # 4. Check Common Misspellings
    words_with_offsets = list(re.finditer(r"\b[a-zA-Z']+\b", text))
    for m in words_with_offsets:
        raw_word = m.group(0)
        lower_word = raw_word.lower()
        if lower_word in COMMON_MISSPELLINGS:
            replacements = COMMON_MISSPELLINGS[lower_word]
            # Match original case
            if raw_word.istitle():
                replacements = [r.capitalize() for r in replacements]
            elif raw_word.isupper():
                replacements = [r.upper() for r in replacements]
                
            matches.append({
                "offset": m.start(),
                "length": len(raw_word),
                "message": f"Có thể sai chính tả từ '{raw_word}'. Gợi ý sửa: {', '.join(replacements)}.",
                "short_message": "Sai chính tả",
                "replacements": replacements,
                "rule_id": f"SPELL_{lower_word.upper()}",
                "category": "Spelling",
                "error_type": "spelling"
            })

    # 5. Check Indefinite Articles (a/an)
    # "a" before vowel sound
    a_vowel_pattern = re.compile(r"\b(a)\s+([aeiou][a-z]+)\b", re.IGNORECASE)
    for m in a_vowel_pattern.finditer(text):
        next_word = m.group(2).lower()
        # Exceptions where 'u' or 'eu' has consonant sound /j/ (e.g. university, unique, uniform, european, user, unit)
        if next_word.startswith(("univ", "uniq", "unif", "unit", "user", "europ", "util", "use")):
            continue
        matches.append({
            "offset": m.start(1),
            "length": 1,
            "message": f"Dùng mạo từ 'an' trước danh từ/tính từ bắt đầu bằng nguyên âm ('{m.group(2)}').",
            "short_message": "Mạo từ 'a' / 'an'",
            "replacements": ["an" if m.group(1).islower() else "An"],
            "rule_id": "ARTICLE_A_AN",
            "category": "Grammar",
            "error_type": "grammar"
        })

    # "an" before consonant sound
    an_consonant_pattern = re.compile(r"\b(an)\s+([bcdfghjklmnpqrstvwxyz][a-z]+)\b", re.IGNORECASE)
    for m in an_consonant_pattern.finditer(text):
        next_word = m.group(2).lower()
        # Exceptions where 'h' is silent (hour, honest, honor, heir)
        if next_word.startswith(("hour", "honest", "honor", "heir")):
            continue
        matches.append({
            "offset": m.start(1),
            "length": 2,
            "message": f"Dùng mạo từ 'a' trước từ bắt đầu bằng phụ âm ('{m.group(2)}').",
            "short_message": "Mạo từ 'a' / 'an'",
            "replacements": ["a" if m.group(1).islower() else "A"],
            "rule_id": "ARTICLE_AN_A",
            "category": "Grammar",
            "error_type": "grammar"
        })

    # 6. Check Grammar Patterns
    for pattern_str, suggested, explanation, cat in GRAMMAR_PATTERNS:
        for m in re.finditer(pattern_str, text, re.IGNORECASE):
            target_group = 1 if m.lastindex == 1 else 2
            start_pos = m.start(target_group)
            matched_sub = m.group(target_group)
            
            # preserve capitalization
            if matched_sub.istitle():
                sugg_final = suggested.capitalize()
            elif matched_sub.isupper():
                sugg_final = suggested.upper()
            else:
                sugg_final = suggested.lower()

            matches.append({
                "offset": start_pos,
                "length": len(matched_sub),
                "message": explanation,
                "short_message": "Lỗi ngữ pháp / dùng từ",
                "replacements": [sugg_final],
                "rule_id": "GRAMMAR_RULE",
                "category": cat,
                "error_type": "grammar"
            })

    # 7. Check Punctuation Spacing (space before comma/period or missing space after comma)
    space_before_punct = re.compile(r"\s+([,.:;!?])")
    for m in space_before_punct.finditer(text):
        punct = m.group(1)
        matches.append({
            "offset": m.start(),
            "length": m.end() - m.start(),
            "message": f"Không nên đặt khoảng trắng trước dấu câu '{punct}'.",
            "short_message": "Khoảng trắng dấu câu",
            "replacements": [punct],
            "rule_id": "SPACE_BEFORE_PUNCTUATION",
            "category": "Punctuation",
            "error_type": "punctuation"
        })

    # Sort matches by offset and deduplicate overlapping matches
    matches.sort(key=lambda x: x["offset"])
    unique_matches = []
    last_end = -1
    for match in matches:
        match_start = match["offset"]
        match_end = match_start + match["length"]
        if match_start >= last_end:
            unique_matches.append(match)
            last_end = match_end

    return unique_matches


def check_grammar_and_spelling(text: str) -> Dict[str, Any]:
    """
    Checks English grammar and spelling for learner writing.
    Attempts LanguageTool API first, then falls back to local rule engine.
    """
    clean_text = (text or "").strip()
    if not clean_text:
        return {
            "success": True,
            "provider": "none",
            "matches": [],
            "stats": {
                "word_count": 0,
                "sentence_count": 0,
                "error_count": 0
            }
        }

    words = re.findall(r"\b\w+\b", clean_text)
    sentences = [s for s in re.split(r"[.!?]+", clean_text) if s.strip()]
    
    matches = []
    provider = "local"

    # Try LanguageTool API (2.0s timeout to keep real-time UI super fast)
    try:
        resp = requests.post(
            LANGUAGETOOL_API_URL,
            data={
                "text": text,
                "language": "en-US",
                "enabledOnly": "false"
            },
            timeout=2.0
        )
        if resp.status_code == 200:
            lt_data = resp.json()
            lt_matches = lt_data.get("matches", [])
            for m in lt_matches:
                rule = m.get("rule", {})
                rule_id = rule.get("id", "")
                cat_name = rule.get("category", {}).get("name", "Grammar")
                replacements = [r.get("value") for r in m.get("replacements", []) if r.get("value")][:4]
                
                # Determine error type
                err_type = "grammar"
                if "SPELL" in rule_id or "TYPO" in cat_name.upper():
                    err_type = "spelling"
                elif "PUNCTUATION" in cat_name.upper():
                    err_type = "punctuation"
                elif "STYLE" in cat_name.upper():
                    err_type = "style"

                matches.append({
                    "offset": m.get("offset", 0),
                    "length": m.get("length", 0),
                    "message": m.get("message", "Phát hiện lỗi ngữ pháp/chính tả."),
                    "short_message": m.get("shortMessage") or cat_name,
                    "replacements": replacements,
                    "rule_id": rule_id,
                    "category": cat_name,
                    "error_type": err_type
                })
            provider = "languagetool"
    except Exception:
        # LanguageTool offline/slow -> Fallback to local rule checker
        pass

    # If LanguageTool returned empty or failed, run local rule checker
    if not matches:
        local_matches = check_with_local_rules(text)
        matches = local_matches
        provider = "local"

    return {
        "success": True,
        "provider": provider,
        "matches": matches,
        "stats": {
            "word_count": len(words),
            "sentence_count": len(sentences),
            "error_count": len(matches)
        }
    }
