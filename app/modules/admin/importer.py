import csv
import io
import json
import uuid
from datetime import datetime
from openpyxl import load_workbook

from app.extensions import db
from app.modules.learning.models import Vocabulary, GrammarTopic, Lesson, Question
from app.modules.exams.models import Exam, ExamQuestion
from app.modules.admin.models import AuditLog


CONTENT_SCHEMAS = {
    "vocabulary": {
        "title": "Từ vựng (Vocabulary)",
        "required_columns": ["word", "pronunciation", "part_of_speech", "meaning_vi", "example_en", "example_vi", "topic", "level"],
        "optional_columns": ["category", "subcategory", "lesson_unit", "image_url", "collocations", "synonyms", "antonyms"],
        "level_valid": ["A1", "A2", "B1", "B2", "C1", "C2"],
    },
    "grammar": {
        "title": "Ngữ pháp (Grammar Topics)",
        "required_columns": ["title", "category", "level", "difficulty", "summary", "rule_explanation", "examples_json"],
        "optional_columns": [
            "common_mistakes", "tips_tricks",
            "order_index", "order", "exam_targets", "exam", "exams",
            "toeic_parts", "toeic_weight", "importance"
        ],
        "level_valid": ["A1", "A2", "B1", "B2", "C1", "C2"],
        "difficulty_valid": ["Easy", "Medium", "Hard"],
    },
    "lessons": {
        "title": "Bài học (Lessons)",
        "required_columns": ["title", "level", "skill", "short_description", "content", "examples"],
        "optional_columns": [
            "thumbnail_url", "audio_url", "accent", "audio_duration", "listening_transcript", "transcript",
            "reading_genre", "reading_passage", "reading_questions",
            "speaking_genre", "speaking_sentences", "speaking_tips",
            "writing_genre", "min_words", "max_words", "writing_templates", "template"
        ],
        "level_valid": ["A1", "A2", "B1", "B2", "C1", "C2"],
        "skill_valid": ["Grammar", "Vocabulary", "Reading", "Listening", "Speaking", "Writing", "General"],
    },
    "questions": {
        "title": "Câu hỏi Trắc nghiệm (Questions)",
        "required_columns": ["question_text", "option_a", "option_b", "option_c", "option_d", "correct_option", "explanation", "topic", "level"],
        "optional_columns": ["skill"],
        "level_valid": ["A1", "A2", "B1", "B2", "C1", "C2"],
        "correct_option_valid": ["A", "B", "C", "D"],
    },
    "exams": {
        "title": "Đề thi & Kiểm tra (Exams)",
        "required_columns": ["category", "title", "duration_minutes", "difficulty", "skill", "part", "question_text", "option_a", "option_b", "option_c", "option_d", "correct_answer", "explanation"],
        "optional_columns": ["type", "transcript", "media_url"],
        "difficulty_valid": ["Easy", "Medium", "Hard"],
        "correct_answer_valid": ["A", "B", "C", "D"],
    }
}

HEADER_ALIASES = {
    "examples": "examples_json",
    "order": "order_index",
    "exam": "exam_targets",
    "exams": "exam_targets",
    "description": "summary",
    "name": "title",
}


def _normalize_grammar_examples(val):
    """
    Ensures grammar examples are stored in the line-delimited format
    expected by learner templates: 'English Sentence|Vietnamese Translation'
    """
    if not val:
        return ""
    val_str = str(val).strip()
    if val_str.startswith("[") or val_str.startswith("{"):
        try:
            parsed = json.loads(val_str)
            if isinstance(parsed, list):
                lines = []
                for item in parsed:
                    if isinstance(item, dict):
                        en = item.get("en") or item.get("english") or item.get("sentence") or ""
                        vi = item.get("vi") or item.get("vietnamese") or item.get("meaning") or ""
                        if en and vi:
                            lines.append(f"{en}|{vi}")
                        elif en:
                            lines.append(en)
                    elif isinstance(item, str) and item.strip():
                        lines.append(item.strip())
                if lines:
                    return "\n".join(lines)
            elif isinstance(parsed, dict):
                en = parsed.get("en") or parsed.get("english") or ""
                vi = parsed.get("vi") or parsed.get("vietnamese") or ""
                if en and vi:
                    return f"{en}|{vi}"
        except Exception:
            pass
    return val_str


def _extract_lesson_skill_data_from_dict(d):
    """
    Extracts structured skill_data dictionary from row for all 4 skills:
    Listening, Reading, Speaking, Writing.
    Fully compatible with routes.py and learner detail templates.
    """
    skill_data = {}

    # Listening
    if d.get("audio_url"):
        skill_data["audio_url"] = str(d["audio_url"]).strip()
    if d.get("accent"):
        skill_data["accent"] = str(d["accent"]).strip().upper()
    if d.get("audio_duration"):
        skill_data["audio_duration"] = str(d["audio_duration"]).strip()
    trans = d.get("listening_transcript") or d.get("transcript")
    if trans:
        skill_data["transcript"] = str(trans).strip()

    # Reading
    if d.get("reading_genre"):
        skill_data["reading_genre"] = str(d["reading_genre"]).strip()
    passage = d.get("reading_passage") or d.get("passage")
    if passage:
        skill_data["passage"] = str(passage).strip()
    q_raw = d.get("reading_questions") or d.get("reading_questions_json")
    if q_raw:
        if isinstance(q_raw, list):
            skill_data["questions"] = q_raw
        elif isinstance(q_raw, str) and q_raw.strip().startswith("["):
            try:
                skill_data["questions"] = json.loads(q_raw)
            except Exception:
                pass

    # Speaking
    if d.get("speaking_genre"):
        skill_data["speaking_genre"] = str(d["speaking_genre"]).strip()
    sent_raw = d.get("speaking_sentences") or d.get("speaking_sentences_json")
    if sent_raw:
        if isinstance(sent_raw, list):
            skill_data["sentences"] = sent_raw
        elif isinstance(sent_raw, str):
            sent_str = sent_raw.strip()
            if sent_str.startswith("["):
                try:
                    skill_data["sentences"] = json.loads(sent_str)
                except Exception:
                    pass
            else:
                parsed = []
                for idx, line in enumerate(sent_str.splitlines()):
                    line = line.strip()
                    if not line:
                        continue
                    parts = [p.strip() for p in line.split("|")]
                    parsed.append({
                        "idx": idx + 1,
                        "text": parts[0],
                        "ipa": parts[1] if len(parts) > 1 else "",
                        "vi": parts[2] if len(parts) > 2 else ""
                    })
                if parsed:
                    skill_data["sentences"] = parsed
    tips_raw = d.get("speaking_tips")
    if tips_raw:
        if isinstance(tips_raw, list):
            skill_data["tips"] = tips_raw
        elif isinstance(tips_raw, str):
            skill_data["tips"] = [t.strip() for t in tips_raw.splitlines() if t.strip()]

    # Writing
    if d.get("writing_genre"):
        skill_data["writing_genre"] = str(d["writing_genre"]).strip()
    if d.get("min_words"):
        try:
            skill_data["min_words"] = int(float(d["min_words"]))
        except (ValueError, TypeError):
            pass
    if d.get("max_words"):
        try:
            skill_data["max_words"] = int(float(d["max_words"]))
        except (ValueError, TypeError):
            pass
    tpl_raw = d.get("writing_templates") or d.get("writing_templates_json") or d.get("template")
    if tpl_raw:
        if isinstance(tpl_raw, list):
            skill_data["templates"] = tpl_raw
        elif isinstance(tpl_raw, str):
            tpl_str = tpl_raw.strip()
            if tpl_str.startswith("["):
                try:
                    skill_data["templates"] = json.loads(tpl_str)
                except Exception:
                    pass
            else:
                parsed = []
                for line in tpl_str.splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    parts = [p.strip() for p in line.split("|")]
                    parsed.append({
                        "label": parts[0],
                        "text": parts[1] if len(parts) > 1 else "",
                        "vi": parts[2] if len(parts) > 2 else ""
                    })
                if parsed:
                    skill_data["templates"] = parsed

    return skill_data


def _validate_record(row_data, schema):
    row_errors = []

    for req_col in schema["required_columns"]:
        if not row_data.get(req_col):
            row_errors.append(f"Cột/Trường '{req_col}' không được để trống")

    if "level" in row_data and row_data["level"]:
        level_upper = row_data["level"].upper()
        if "level_valid" in schema and level_upper not in schema["level_valid"]:
            row_errors.append(f"Cấp độ '{row_data['level']}' không hợp lệ (Phải là A1, A2, B1, B2, C1, hoặc C2)")
        row_data["level"] = level_upper

    if "difficulty" in row_data and row_data["difficulty"]:
        diff_title = row_data["difficulty"].title()
        if "difficulty_valid" in schema and diff_title not in schema["difficulty_valid"]:
            row_errors.append(f"Độ khó '{row_data['difficulty']}' không hợp lệ (Phải là Easy, Medium, hoặc Hard)")
        row_data["difficulty"] = diff_title

    if "skill" in row_data and row_data["skill"]:
        skill_title = row_data["skill"].title()
        if "skill_valid" in schema and skill_title not in schema["skill_valid"]:
            row_errors.append(f"Kỹ năng '{row_data['skill']}' không hợp lệ (Phải là Grammar, Vocabulary, Reading, Listening, Speaking, Writing, General)")
        row_data["skill"] = skill_title

    if "correct_option" in row_data and row_data["correct_option"]:
        opt_upper = row_data["correct_option"].upper()
        if "correct_option_valid" in schema and opt_upper not in schema["correct_option_valid"]:
            row_errors.append(f"Đáp án đúng '{row_data['correct_option']}' không hợp lệ (Phải là A, B, C, hoặc D)")
        row_data["correct_option"] = opt_upper

    if "correct_answer" in row_data and row_data["correct_answer"]:
        ans_upper = row_data["correct_answer"].upper()
        if "correct_answer_valid" in schema and ans_upper not in schema["correct_answer_valid"]:
            row_errors.append(f"Đáp án đúng '{row_data['correct_answer']}' không hợp lệ (Phải là A, B, C, hoặc D)")
        row_data["correct_answer"] = ans_upper

    if "duration_minutes" in row_data and row_data["duration_minutes"]:
        val_dur = str(row_data["duration_minutes"]).strip()
        try:
            dur_int = int(float(val_dur))
            if dur_int <= 0:
                row_errors.append(f"Thời lượng bài thi '{val_dur}' phải lớn hơn 0 phút")
            row_data["duration_minutes"] = str(dur_int)
        except (ValueError, TypeError):
            row_errors.append(f"Thời lượng bài thi '{val_dur}' không hợp lệ (Phải là số nguyên phút, ví dụ: 60)")

    return row_errors


def parse_and_validate_file(file_stream, filename, content_type):
    fn = filename.lower()
    if fn.endswith(".json"):
        return parse_and_validate_json(file_stream, content_type)
    elif fn.endswith(".csv"):
        return parse_and_validate_csv(file_stream, content_type)
    return parse_and_validate_excel(file_stream, content_type)


def parse_and_validate_csv(file_stream, content_type):
    if content_type not in CONTENT_SCHEMAS:
        return {
            "success": False,
            "error": f"Loại nội dung '{content_type}' không được hỗ trợ."
        }

    schema = CONTENT_SCHEMAS[content_type]
    raw_bytes = file_stream.read()
    
    # Try decoding with utf-8-sig (for Excel utf-8 BOM), utf-8, or latin-1
    text_content = None
    for enc in ["utf-8-sig", "utf-8", "cp1258", "latin-1"]:
        try:
            text_content = raw_bytes.decode(enc)
            break
        except Exception:
            continue
            
    if text_content is None:
        return {
            "success": False,
            "error": "Không thể giải mã file CSV. Vui lòng lưu file ở định dạng UTF-8."
        }

    # Detect delimiter (comma or semicolon)
    sample_line = text_content.splitlines()[0] if text_content.splitlines() else ""
    delimiter = ";" if sample_line.count(";") > sample_line.count(",") else ","

    reader = csv.reader(io.StringIO(text_content), delimiter=delimiter)
    rows = list(reader)

    if not rows:
        return {
            "success": False,
            "error": "File CSV trống, không có dữ liệu."
        }

    raw_headers = [HEADER_ALIASES.get(str(h or "").strip().lower(), str(h or "").strip().lower()) for h in rows[0]]
    missing_cols = [col for col in schema["required_columns"] if col not in raw_headers]
    if missing_cols:
        return {
            "success": False,
            "error": f"File CSV thiếu các cột bắt buộc: {', '.join(missing_cols)}."
        }

    header_indices = {col: raw_headers.index(col) for col in raw_headers if col}

    valid_records = []
    error_records = []

    for row_idx, row in enumerate(rows[1:], start=2):
        if not any(row) or all(not str(c).strip() for c in row):
            continue

        row_data = {}
        for col_name, col_idx in header_indices.items():
            val = row[col_idx] if col_idx < len(row) else ""
            row_data[col_name] = str(val).strip() if val is not None else ""

        row_errors = _validate_record(row_data, schema)

        if row_errors:
            error_records.append({
                "row_number": row_idx,
                "data": row_data,
                "errors": row_errors
            })
        else:
            valid_records.append({
                "row_number": row_idx,
                "data": row_data
            })

    batch_id = str(uuid.uuid4())

    return {
        "success": True,
        "batch_id": batch_id,
        "content_type": content_type,
        "content_title": schema["title"],
        "total_rows": len(valid_records) + len(error_records),
        "valid_count": len(valid_records),
        "error_count": len(error_records),
        "valid_records": valid_records,
        "error_records": error_records,
        "preview_sample": [r["data"] for r in valid_records[:10]]
    }


def parse_and_validate_json(file_stream, content_type):
    if content_type not in CONTENT_SCHEMAS:
        return {
            "success": False,
            "error": f"Loại nội dung '{content_type}' không được hỗ trợ."
        }

    schema = CONTENT_SCHEMAS[content_type]
    try:
        raw_content = file_stream.read()
        if isinstance(raw_content, bytes):
            raw_content = raw_content.decode("utf-8")
        data = json.loads(raw_content)
    except Exception as e:
        return {
            "success": False,
            "error": f"Không thể đọc file JSON. Vui lòng đảm bảo định dạng file là .json hợp lệ. ({str(e)})"
        }

    if isinstance(data, dict):
        for k in ["items", "data", "records", "vocabulary", "grammar", "lessons", "questions", "exams"]:
            if k in data and isinstance(data[k], list):
                data = data[k]
                break
        else:
            data = [data]

    if not isinstance(data, list) or len(data) == 0:
        return {
            "success": False,
            "error": "File JSON trống hoặc không chứa danh sách các bản ghi (Array of Objects)."
        }

    valid_records = []
    error_records = []

    for idx, item in enumerate(data, start=1):
        if not isinstance(item, dict):
            error_records.append({
                "row_number": idx,
                "data": {"raw": str(item)},
                "errors": ["Bản ghi không phải là JSON Object (dict)"]
            })
            continue

        row_data = {}
        normalized_item = {str(k).strip().lower(): str(v).strip() if v is not None else "" for k, v in item.items()}

        for col_name in schema["required_columns"] + schema.get("optional_columns", []):
            row_data[col_name] = normalized_item.get(col_name, "")

        row_errors = _validate_record(row_data, schema)

        if row_errors:
            error_records.append({
                "row_number": idx,
                "data": row_data,
                "errors": row_errors
            })
        else:
            valid_records.append({
                "row_number": idx,
                "data": row_data
            })

    batch_id = str(uuid.uuid4())

    return {
        "success": True,
        "batch_id": batch_id,
        "content_type": content_type,
        "content_title": schema["title"],
        "total_rows": len(valid_records) + len(error_records),
        "valid_count": len(valid_records),
        "error_count": len(error_records),
        "valid_records": valid_records,
        "error_records": error_records,
        "preview_sample": [r["data"] for r in valid_records[:10]]
    }


def parse_and_validate_excel(file_stream, content_type):
    if content_type not in CONTENT_SCHEMAS:
        return {
            "success": False,
            "error": f"Loại nội dung '{content_type}' không được hỗ trợ."
        }

    schema = CONTENT_SCHEMAS[content_type]
    try:
        wb = load_workbook(filename=io.BytesIO(file_stream.read()), data_only=True)
    except Exception as e:
        return {
            "success": False,
            "error": f"Không thể đọc file Excel. Vui lòng đảm bảo định dạng file là .xlsx hợp lệ. ({str(e)})"
        }

    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))

    if not rows:
        return {
            "success": False,
            "error": "File Excel trống, không có dữ liệu."
        }

    # Header check
    raw_headers = [HEADER_ALIASES.get(str(h or "").strip().lower(), str(h or "").strip().lower()) for h in rows[0]]
    missing_cols = [col for col in schema["required_columns"] if col not in raw_headers]
    if missing_cols:
        return {
            "success": False,
            "error": f"File Excel thiếu các cột bắt buộc: {', '.join(missing_cols)}."
        }

    header_indices = {col: raw_headers.index(col) for col in raw_headers if col}

    valid_records = []
    error_records = []

    # Iterate data rows
    for row_idx, row in enumerate(rows[1:], start=2):
        # Check if entire row is empty
        if not any(row):
            continue

        row_data = {}
        for col_name, col_idx in header_indices.items():
            val = row[col_idx] if col_idx < len(row) else ""
            if val is not None:
                val = str(val).strip()
            else:
                val = ""
            row_data[col_name] = val

        row_errors = _validate_record(row_data, schema)

        if row_errors:
            error_records.append({
                "row_number": row_idx,
                "data": row_data,
                "errors": row_errors
            })
        else:
            valid_records.append({
                "row_number": row_idx,
                "data": row_data
            })

    batch_id = str(uuid.uuid4())

    return {
        "success": True,
        "batch_id": batch_id,
        "content_type": content_type,
        "content_title": schema["title"],
        "total_rows": len(valid_records) + len(error_records),
        "valid_count": len(valid_records),
        "error_count": len(error_records),
        "valid_records": valid_records,
        "error_records": error_records,
        "preview_sample": [r["data"] for r in valid_records[:10]]
    }


def commit_import_records(content_type, valid_records, user_id=None, mode="insert_or_update"):
    """
    Persist validated records into PostgreSQL/SQLite database.
    """
    inserted_count = 0
    updated_count = 0

    if content_type == "vocabulary":
        for rec in valid_records:
            d = rec["data"]
            word_str = d["word"].strip()
            pos_str = d.get("part_of_speech", "").strip()

            if pos_str:
                existing = Vocabulary.query.filter(
                    Vocabulary.word.ilike(word_str),
                    Vocabulary.part_of_speech.ilike(pos_str)
                ).first()
            else:
                existing = Vocabulary.query.filter(Vocabulary.word.ilike(word_str)).first()

            if existing and mode == "insert_or_update":
                existing.pronunciation = d.get("pronunciation", existing.pronunciation)
                existing.part_of_speech = d.get("part_of_speech", existing.part_of_speech)
                existing.meaning_vi = d.get("meaning_vi", existing.meaning_vi)
                existing.example_en = d.get("example_en", existing.example_en)
                existing.example_vi = d.get("example_vi", existing.example_vi)
                existing.topic = d.get("topic", existing.topic)
                existing.level = d.get("level", existing.level)
                if d.get("category"):
                    existing.category = d["category"].strip()
                if d.get("subcategory"):
                    existing.subcategory = d["subcategory"].strip()
                if d.get("lesson_unit"):
                    existing.lesson_unit = d["lesson_unit"].strip()
                if d.get("image_url"):
                    existing.image_url = d["image_url"].strip()
                if d.get("collocations"):
                    existing.collocations = d["collocations"].strip()
                if d.get("synonyms"):
                    existing.synonyms = d["synonyms"].strip()
                if d.get("antonyms"):
                    existing.antonyms = d["antonyms"].strip()
                updated_count += 1
            elif not existing:
                item = Vocabulary(
                    word=word_str,
                    pronunciation=d.get("pronunciation", ""),
                    part_of_speech=d.get("part_of_speech", "noun"),
                    meaning_vi=d.get("meaning_vi", ""),
                    example_en=d.get("example_en", ""),
                    example_vi=d.get("example_vi", ""),
                    topic=d.get("topic", "General"),
                    level=d.get("level", "A1"),
                    category=d.get("category", "CEFR") or "CEFR",
                    subcategory=d.get("subcategory") or None,
                    lesson_unit=d.get("lesson_unit") or None,
                    image_url=d.get("image_url") or None,
                    collocations=d.get("collocations") or None,
                    synonyms=d.get("synonyms") or None,
                    antonyms=d.get("antonyms") or None,
                )
                db.session.add(item)
                inserted_count += 1

    elif content_type == "grammar":
        for rec in valid_records:
            d = rec["data"]
            title_str = d["title"].strip()
            existing = GrammarTopic.query.filter_by(title=title_str).first()
            norm_examples = _normalize_grammar_examples(d.get("examples_json", ""))

            # Safe order_index parsing
            order_idx = 0
            if d.get("order_index"):
                try:
                    order_idx = int(float(d["order_index"]))
                except (ValueError, TypeError):
                    order_idx = 0

            exam_targets_val = (d.get("exam_targets") or "General English, TOEIC").strip()
            toeic_parts_val = d.get("toeic_parts").strip() if d.get("toeic_parts") else None
            toeic_weight_val = (d.get("toeic_weight") or "Medium").strip().title()
            importance_val = (d.get("importance") or "Medium").strip().title()

            if existing and mode == "insert_or_update":
                existing.category = d.get("category", existing.category)
                existing.level = d.get("level", existing.level)
                existing.difficulty = d.get("difficulty", existing.difficulty)
                existing.summary = d.get("summary", existing.summary)
                existing.rule_explanation = d.get("rule_explanation", existing.rule_explanation)
                if norm_examples:
                    existing.examples_json = norm_examples
                if d.get("common_mistakes"):
                    existing.common_mistakes = d["common_mistakes"]
                if d.get("tips_tricks"):
                    existing.tips_tricks = d["tips_tricks"]
                if d.get("order_index") is not None:
                    existing.order_index = order_idx
                if d.get("exam_targets"):
                    existing.exam_targets = exam_targets_val
                if d.get("toeic_parts") is not None:
                    existing.toeic_parts = toeic_parts_val
                if d.get("toeic_weight"):
                    existing.toeic_weight = toeic_weight_val
                if d.get("importance"):
                    existing.importance = importance_val
                updated_count += 1
            elif not existing:
                item = GrammarTopic(
                    title=title_str,
                    category=d.get("category", "General"),
                    level=d.get("level", "A1"),
                    difficulty=d.get("difficulty", "Medium"),
                    summary=d.get("summary", ""),
                    rule_explanation=d.get("rule_explanation", ""),
                    examples_json=norm_examples,
                    common_mistakes=d.get("common_mistakes") or None,
                    tips_tricks=d.get("tips_tricks") or None,
                    order_index=order_idx,
                    exam_targets=exam_targets_val,
                    toeic_parts=toeic_parts_val,
                    toeic_weight=toeic_weight_val,
                    importance=importance_val,
                    is_active=True,
                )
                db.session.add(item)
                inserted_count += 1

    elif content_type == "lessons":
        for rec in valid_records:
            d = rec["data"]
            title_str = d["title"].strip()
            existing = Lesson.query.filter_by(title=title_str).first()

            skill_data = _extract_lesson_skill_data_from_dict(d)

            if existing and mode == "insert_or_update":
                existing.level = d.get("level", existing.level)
                existing.skill = d.get("skill", existing.skill)
                existing.short_description = d.get("short_description", existing.short_description)
                existing.content = d.get("content", existing.content)
                existing.examples = d.get("examples", existing.examples)
                if d.get("thumbnail_url"):
                    existing.thumbnail_url = d["thumbnail_url"]
                if skill_data:
                    existing.skill_data = {**(existing.skill_data or {}), **skill_data}
                updated_count += 1
            elif not existing:
                item = Lesson(
                    title=title_str,
                    level=d.get("level", "A1"),
                    skill=d.get("skill", "General"),
                    short_description=d.get("short_description", ""),
                    content=d.get("content", ""),
                    examples=d.get("examples", ""),
                    thumbnail_url=d.get("thumbnail_url") or None,
                    skill_data=skill_data if skill_data else None,
                    is_active=True,
                )
                db.session.add(item)
                inserted_count += 1

    elif content_type == "questions":
        for rec in valid_records:
            d = rec["data"]
            q_text = d["question_text"].strip()
            existing = Question.query.filter_by(question_text=q_text).first()

            if existing and mode == "insert_or_update":
                existing.option_a = d.get("option_a", existing.option_a)
                existing.option_b = d.get("option_b", existing.option_b)
                existing.option_c = d.get("option_c", existing.option_c)
                existing.option_d = d.get("option_d", existing.option_d)
                existing.correct_option = d.get("correct_option", existing.correct_option)
                existing.explanation = d.get("explanation", existing.explanation)
                existing.topic = d.get("topic", existing.topic)
                existing.level = d.get("level", existing.level)
                updated_count += 1
            elif not existing:
                item = Question(
                    question_text=q_text,
                    option_a=d.get("option_a", ""),
                    option_b=d.get("option_b", ""),
                    option_c=d.get("option_c", ""),
                    option_d=d.get("option_d", ""),
                    correct_option=d.get("correct_option", "A"),
                    explanation=d.get("explanation", ""),
                    topic=d.get("topic", "General"),
                    level=d.get("level", "A1"),
                )
                db.session.add(item)
                inserted_count += 1

    elif content_type == "exams":
        # Group questions by exam title
        exam_groups = {}
        for rec in valid_records:
            d = rec["data"]
            exam_title = d["title"].strip()
            if exam_title not in exam_groups:
                try:
                    dur = int(float(d.get("duration_minutes", 15)))
                except (ValueError, TypeError):
                    dur = 15
                exam_groups[exam_title] = {
                    "category": d.get("category", "General"),
                    "duration_minutes": dur,
                    "difficulty": d.get("difficulty", "Medium"),
                    "questions": []
                }
            exam_groups[exam_title]["questions"].append(d)

        for title_str, grp in exam_groups.items():
            exam = Exam.query.filter_by(title=title_str).first()
            category = grp["category"]
            questions = grp["questions"]

            # Calculate part_distribution for TOEIC exams
            part_dist = None
            if category.upper() == "TOEIC":
                p5 = sum(1 for q in questions if "5" in str(q.get("part", "")))
                p6 = sum(1 for q in questions if "6" in str(q.get("part", "")))
                p7 = sum(1 for q in questions if "7" in str(q.get("part", "")))
                if p5 or p6 or p7:
                    part_dist = {"part5": p5, "part6": p6, "part7": p7}
                else:
                    part_dist = {"part5": 30, "part6": 16, "part7": 54}

            if not exam:
                exam = Exam(
                    title=title_str,
                    category=category,
                    duration=grp["duration_minutes"],
                    duration_minutes=grp["duration_minutes"],
                    difficulty=grp["difficulty"],
                    question_count=len(questions),
                    part_distribution=part_dist,
                    is_published=True,
                    is_active=True
                )
                db.session.add(exam)
                db.session.flush()
                inserted_count += 1
            else:
                if part_dist:
                    exam.part_distribution = part_dist
                exam.question_count = len(questions)
                exam.duration_minutes = grp["duration_minutes"]
                exam.duration = grp["duration_minutes"]
                ExamQuestion.query.filter_by(exam_id=exam.id).delete()
                updated_count += 1

            for q_data in questions:
                media_info = None
                if q_data.get("media_url"):
                    media_url_clean = str(q_data["media_url"]).strip()
                    media_info = {"audio_url": media_url_clean, "media_url": media_url_clean}

                eq = ExamQuestion(
                    exam_id=exam.id,
                    skill=q_data.get("skill", "READING"),
                    part=q_data.get("part", "Part 1"),
                    type=q_data.get("type", "SINGLE_CHOICE") or "SINGLE_CHOICE",
                    question_text=q_data.get("question_text", ""),
                    option_a=q_data.get("option_a", ""),
                    option_b=q_data.get("option_b", ""),
                    option_c=q_data.get("option_c", ""),
                    option_d=q_data.get("option_d", ""),
                    correct_answer=q_data.get("correct_answer", "A"),
                    media_info=media_info,
                    transcript=q_data.get("transcript") or None,
                    explanation=q_data.get("explanation", "")
                )
                db.session.add(eq)

    # Log audit
    if user_id:
        log = AuditLog(
            user_id=user_id,
            action="IMPORT_EXCEL",
            target_type=content_type,
            details=f"Imported {inserted_count} new and updated {updated_count} records via Excel."
        )
        db.session.add(log)

    db.session.commit()

    return {
        "success": True,
        "inserted_count": inserted_count,
        "updated_count": updated_count,
        "total_processed": inserted_count + updated_count
    }
