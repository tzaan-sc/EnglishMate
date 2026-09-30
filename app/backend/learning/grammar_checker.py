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


def evaluate_writing_submission(
    text: str,
    target_min: int = 40,
    target_max: int = 80,
    prompt: str = ""
) -> Dict[str, Any]:
    """
    Evaluates a completed essay submission across 4 standard criteria:
    1. Task Response / Achievement
    2. Coherence & Cohesion
    3. Lexical Resource (Vocabulary Diversity)
    4. Grammatical Range & Accuracy

    Returns a comprehensive evaluation report with scores (0-10),
    CEFR/IELTS band estimates, strengths, weaknesses, and actionable feedback.
    """
    clean_text = (text or "").strip()
    if not clean_text:
        return {
            "overall_score": 0.0,
            "grade": "Chưa hoàn thành",
            "band_estimate": "N/A",
            "criteria": {
                "task_response": {"score": 0.0, "label": "Task Response", "feedback": "Chưa có nội dung bài viết."},
                "coherence_cohesion": {"score": 0.0, "label": "Coherence & Cohesion", "feedback": "Chưa có nội dung bài viết."},
                "lexical_resource": {"score": 0.0, "label": "Lexical Resource", "feedback": "Chưa có nội dung bài viết."},
                "grammatical_accuracy": {"score": 0.0, "label": "Grammar & Accuracy", "feedback": "Chưa có nội dung bài viết."}
            },
            "word_count": 0,
            "sentence_count": 0,
            "paragraph_count": 0,
            "connectors_detected": [],
            "error_count": 0,
            "strengths": [],
            "improvements": ["Hãy bắt đầu viết bài theo đề bài yêu cầu."],
            "general_feedback": "Vui lòng nhập nội dung bài viết trước khi nộp bài."
        }

    words = re.findall(r"\b[a-zA-Z']+\b", clean_text)
    word_count = len(words)
    sentences = [s.strip() for s in re.split(r"[.!?]+", clean_text) if s.strip()]
    sentence_count = len(sentences) or 1
    paragraphs = [p.strip() for p in clean_text.splitlines() if p.strip()]
    paragraph_count = len(paragraphs) or 1

    # 1. Grammar & Spelling check
    check_res = check_grammar_and_spelling(clean_text)
    matches = check_res.get("matches", [])
    error_count = len(matches)

    # 2. Connectors & Transition Devices
    connectors_list = [
        "first", "firstly", "second", "secondly", "finally", "then", "after that",
        "furthermore", "moreover", "in addition", "additionally", "besides",
        "however", "although", "even though", "on the other hand", "in contrast",
        "therefore", "as a result", "thus", "consequently",
        "for example", "for instance", "such as", "to illustrate",
        "in conclusion", "to sum up", "overall", "in summary",
        "because", "since", "due to", "while", "whereas"
    ]
    lower_text = clean_text.lower()
    found_connectors = []
    for c in connectors_list:
        if re.search(r"\b" + re.escape(c) + r"\b", lower_text):
            found_connectors.append(c)

    # 3. Vocabulary Richness (Type-Token Ratio & Academic words)
    unique_words = set(w.lower() for w in words)
    ttr = len(unique_words) / max(1, word_count)

    academic_vocab = [
        "significant", "crucial", "essential", "advantage", "disadvantage", "benefit",
        "opportunity", "challenge", "perspective", "environment", "development",
        "community", "technology", "experience", "education", "relationship",
        "improve", "increase", "decrease", "enhance", "require", "encourage",
        "effective", "positive", "negative", "important", "convenient", "modern"
    ]
    used_academic = [w for w in academic_vocab if w in unique_words]

    # --- CRITERIA SCORING (Scale 0-10) ---

    # Criterion 1: Task Response
    if word_count >= target_min:
        if word_count <= target_max + 40:
            task_score = 9.5
            task_fb = f"Rất tốt! Bài viết đạt {word_count} từ, hoàn toàn nằm trong dung lượng chuẩn ({target_min}-{target_max} từ)."
        else:
            task_score = 8.5
            task_fb = f"Bài viết khá chi tiết ({word_count} từ), vượt trên mức yêu cầu ({target_max} từ). Chú ý tinh gọn ý tưởng hơn."
    elif word_count >= int(target_min * 0.75):
        task_score = 7.0
        task_fb = f"Bài viết đạt {word_count} từ (gần đạt mục tiêu tối thiểu {target_min} từ). Hãy mở rộng thêm 1-2 ví dụ hoặc lý do."
    elif word_count >= int(target_min * 0.5):
        task_score = 5.5
        task_fb = f"Bài viết còn khá ngắn ({word_count}/{target_min} từ). Cần triển khai các luận điểm sâu hơn."
    else:
        task_score = 4.0
        task_fb = f"Dung lượng bài viết ({word_count} từ) chưa đạt yêu cầu tối thiểu {target_min} từ."

    # Criterion 2: Coherence & Cohesion
    conn_count = len(found_connectors)
    if conn_count >= 4 and paragraph_count >= 2:
        coherence_score = 9.5
        coherence_fb = f"Mạch lạc xuất sắc! Bài viết phân đoạn rõ ràng và sử dụng linh hoạt {conn_count} từ nối ({', '.join(found_connectors[:4])})."
    elif conn_count >= 2:
        coherence_score = 8.0
        coherence_fb = f"Bài viết có tính liên kết tốt với {conn_count} từ nối. Hãy thử phân chia đoạn văn rõ hơn nếu bài dài."
    elif conn_count == 1:
        coherence_score = 6.5
        coherence_fb = "Bài viết có sử dụng từ nối cơ bản. Hãy bổ sung thêm các liên từ (furthermore, however, for example) để bài viết mượt mà hơn."
    else:
        coherence_score = 5.0
        coherence_fb = "Chưa phát hiện nhiều từ nối liên kết giữa các câu. Hãy dùng thêm các từ như First, Because, Therefore, However."

    # Criterion 3: Lexical Resource
    if ttr >= 0.65 and len(used_academic) >= 2:
        lexical_score = 9.5
        lexical_fb = f"Vốn từ rất phong phú và đa dạng (TTR: {int(ttr*100)}%), sử dụng các từ vựng học thuật tốt ({', '.join(used_academic[:3])})."
    elif ttr >= 0.50 or len(used_academic) >= 1:
        lexical_score = 8.0
        lexical_fb = f"Sử dụng từ vựng tương đối đa dạng (TTR: {int(ttr*100)}%). Bạn có thể nâng cấp thêm các cụm từ đồng nghĩa để tránh lặp từ."
    else:
        lexical_score = 6.0
        lexical_fb = f"Tỷ lệ từ lặp lại còn hơi cao (TTR: {int(ttr*100)}%). Hãy chú ý mở rộng vốn từ vựng theo chủ đề."

    # Criterion 4: Grammatical Range & Accuracy
    errors_per_100 = (error_count / max(1, word_count)) * 100
    if errors_per_100 == 0:
        grammar_score = 10.0
        grammar_fb = "Tuyệt đối chính xác! Không phát hiện lỗi chính tả hoặc ngữ pháp nào."
    elif errors_per_100 <= 2.5:
        grammar_score = 8.5
        grammar_fb = f"Ngữ pháp rất tốt, chỉ phát hiện {error_count} lỗi nhỏ không ảnh hưởng nhiều đến ý nghĩa bài viết."
    elif errors_per_100 <= 6.0:
        grammar_score = 7.0
        grammar_fb = f"Phát hiện {error_count} lỗi ngữ pháp/chính tả. Hãy xem lại gợi ý sửa lỗi để hoàn thiện bài."
    elif errors_per_100 <= 12.0:
        grammar_score = 5.5
        grammar_fb = f"Có {error_count} lỗi chính tả và ngữ pháp. Cần chú ý kỹ chia động từ và viết hoa."
    else:
        grammar_score = 4.0
        grammar_fb = f"Mật độ lỗi ngữ pháp & chính tả còn cao ({error_count} lỗi). Hãy tận dụng tính năng sửa lỗi tự động."

    # Overall Score Calculation
    overall_score = round(0.30 * task_score + 0.25 * coherence_score + 0.25 * lexical_score + 0.20 * grammar_score, 1)
    overall_score = max(1.0, min(10.0, overall_score))

    # Band estimate & Grade
    if overall_score >= 8.5:
        grade = "Xuất sắc"
        band = "C1 (IELTS 7.5 - 8.5)"
    elif overall_score >= 7.0:
        grade = "Giỏi"
        band = "B2 (IELTS 6.0 - 7.0)"
    elif overall_score >= 5.5:
        grade = "Khá"
        band = "B1 (IELTS 5.0 - 5.5)"
    else:
        grade = "Cần luyện tập thêm"
        band = "A2 (IELTS 4.0 - 4.5)"

    # Strengths and Improvements
    strengths = []
    if word_count >= target_min:
        strengths.append(f"Độ dài bài viết đạt chuẩn ({word_count} từ)")
    if conn_count >= 2:
        strengths.append(f"Sử dụng hiệu quả các từ nối ({', '.join(found_connectors[:3])})")
    if ttr >= 0.55:
        strengths.append("Vốn từ vựng phong phú, ít bị lặp từ")
    if error_count == 0:
        strengths.append("Chính tả và ngữ pháp hoàn hảo, không có lỗi")
    elif error_count <= 2:
        strengths.append("Độ chính xác ngữ pháp cao")
    if not strengths:
        strengths.append("Đã hoàn thành và nộp bài viết nghiêm túc")

    improvements = []
    if word_count < target_min:
        improvements.append(f"Mở rộng thêm luận điểm để đạt mức tối thiểu {target_min} từ (hiện có {word_count} từ).")
    if conn_count < 2:
        improvements.append("Bổ sung thêm 2-3 liên từ chuyển ý (In addition, However, For instance) để bài viết mạch lạc hơn.")
    if error_count > 0:
        improvements.append(f"Khắc phục {error_count} lỗi chính tả và ngữ pháp đã được hệ thống cảnh báo.")
    if ttr < 0.50:
        improvements.append("Tìm từ đồng nghĩa để thay thế cho các từ lặp lại nhiều lần.")
    if not improvements:
        improvements.append("Tiếp tục phát huy phong độ và thử sức với các chủ đề bài viết nâng cao hơn!")

    general_feedback = (
        f"Bài viết của bạn đạt điểm tổng kết {overall_score}/10 ({grade}, tương đương trình độ {band}). "
        f"{task_fb} {coherence_fb}"
    )

    return {
        "overall_score": overall_score,
        "grade": grade,
        "band_estimate": band,
        "criteria": {
            "task_response": {"score": task_score, "label": "Hoàn thành yêu cầu (Task Response)", "feedback": task_fb},
            "coherence_cohesion": {"score": coherence_score, "label": "Mạch lạc & Liên kết (Coherence & Cohesion)", "feedback": coherence_fb},
            "lexical_resource": {"score": lexical_score, "label": "Vốn từ vựng (Lexical Resource)", "feedback": lexical_fb},
            "grammatical_accuracy": {"score": grammar_score, "label": "Ngữ pháp & Chính xác (Grammar & Accuracy)", "feedback": grammar_fb}
        },
        "word_count": word_count,
        "sentence_count": sentence_count,
        "paragraph_count": paragraph_count,
        "connectors_detected": found_connectors,
        "error_count": error_count,
        "strengths": strengths,
        "improvements": improvements,
        "general_feedback": general_feedback
    }
