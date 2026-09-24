from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField
from wtforms.validators import DataRequired


LEVELS = [("", "Tất cả cấp độ"), ("A1", "A1"), ("A2", "A2"), ("B1", "B1"), ("B2", "B2"), ("C1", "C1")]
SKILLS = [("", "Tất cả kỹ năng"), ("Vocabulary", "Vocabulary"), ("Grammar", "Grammar"),
          ("Reading", "Reading"), ("Listening", "Listening"), ("Speaking", "Speaking")]


class ActionForm(FlaskForm):
    submit = SubmitField("Xác nhận")


class QuizStartForm(FlaskForm):
    level = SelectField("Cấp độ", choices=LEVELS, validators=[])
    topic = SelectField("Chủ đề", choices=[], validators=[])
    submit = SubmitField("Bắt đầu thử thách")

