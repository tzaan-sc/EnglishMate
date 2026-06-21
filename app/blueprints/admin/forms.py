from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length

LEVELS = [(x, x) for x in ("A1", "A2", "B1", "B2", "C1")]
SKILLS = [(x, x) for x in ("Vocabulary", "Grammar", "Reading", "Listening", "Speaking")]


class LessonForm(FlaskForm):
    title = StringField("Tên bài học", validators=[DataRequired(), Length(max=160)])
    level = SelectField("Cấp độ", choices=LEVELS, validators=[DataRequired()])
    skill = SelectField("Kỹ năng", choices=SKILLS, validators=[DataRequired()])
    short_description = TextAreaField("Mô tả ngắn", validators=[DataRequired(), Length(max=280)])
    content = TextAreaField("Nội dung", validators=[DataRequired()])
    examples = TextAreaField("Ví dụ (mỗi dòng một câu)", validators=[DataRequired()])
    submit = SubmitField("Lưu bài học")


class VocabularyForm(FlaskForm):
    word = StringField("Từ", validators=[DataRequired(), Length(max=100)])
    pronunciation = StringField("Phiên âm", validators=[DataRequired(), Length(max=100)])
    part_of_speech = StringField("Từ loại", validators=[DataRequired(), Length(max=30)])
    meaning_vi = StringField("Nghĩa tiếng Việt", validators=[DataRequired(), Length(max=200)])
    example_en = TextAreaField("Ví dụ tiếng Anh", validators=[DataRequired(), Length(max=300)])
    example_vi = TextAreaField("Dịch ví dụ", validators=[DataRequired(), Length(max=300)])
    topic = StringField("Chủ đề", validators=[DataRequired(), Length(max=80)])
    level = SelectField("Cấp độ", choices=LEVELS, validators=[DataRequired()])
    submit = SubmitField("Lưu từ vựng")


class ConfirmForm(FlaskForm):
    submit = SubmitField("Xác nhận")

