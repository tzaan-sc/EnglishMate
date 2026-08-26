import math
import pandas as pd
from app.extensions import db
from app.modules.exams.models import Exam, ExamQuestion


def is_nan(value):
    """Check if a value is NaN safely."""
    if isinstance(value, float) and math.isnan(value):
        return True
    return pd.isna(value)


def import_exam_from_dataframe(df, category, title, duration=120):
    """
    Import exam from a pandas DataFrame using Bulk Insert for maximum performance.
    
    Expected columns in DataFrame:
    - Skill (e.g., LISTENING, READING)
    - Part (e.g., Part 1, Part 2)
    - Type (e.g., SINGLE_CHOICE, ESSAY)
    - Question_Text
    - Option_A, Option_B, Option_C, Option_D
    - Correct_Answer
    - Audio_URL
    - Start_Time
    - End_Time
    - Transcript
    - Explanation
    """
    exam = Exam(category=category, title=title, duration=duration)
    db.session.add(exam)
    db.session.flush()  # to get exam.id
    
    questions_to_insert = []
    
    for _, row in df.iterrows():
        def get_val(col):
            if col not in row:
                return None
            val = row[col]
            return None if is_nan(val) else str(val).strip() if isinstance(val, str) else val
            
        media_info = {}
        audio_url = get_val('Audio_URL')
        start_time = get_val('Start_Time')
        end_time = get_val('End_Time')
        
        if audio_url:
            media_info['audio_url'] = audio_url
        if start_time is not None:
            media_info['start_time'] = float(start_time)
        if end_time is not None:
            media_info['end_time'] = float(end_time)
            
        q = ExamQuestion(
            exam_id=exam.id,
            skill=get_val('Skill'),
            part=get_val('Part'),
            type=get_val('Type') or 'SINGLE_CHOICE',
            question_text=get_val('Question_Text'),
            option_a=get_val('Option_A'),
            option_b=get_val('Option_B'),
            option_c=get_val('Option_C'),
            option_d=get_val('Option_D'),
            correct_answer=get_val('Correct_Answer'),
            media_info=media_info if media_info else None,
            transcript=get_val('Transcript'),
            explanation=get_val('Explanation')
        )
        questions_to_insert.append(q)
        
    # Bulk insert all questions at once
    db.session.bulk_save_objects(questions_to_insert)
    db.session.commit()
    return exam


def import_exam_from_excel(filepath, category, title, duration=120):
    """Entry point for Excel files."""
    df = pd.read_excel(filepath)
    return import_exam_from_dataframe(df, category, title, duration)


def import_exam_from_json(filepath, category, title, duration=120):
    """Entry point for JSON files."""
    df = pd.read_json(filepath, orient='records')
    return import_exam_from_dataframe(df, category, title, duration)
