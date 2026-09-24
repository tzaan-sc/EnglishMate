from flask_wtf import FlaskForm
from wtforms import SubmitField


class ActionForm(FlaskForm):
    submit = SubmitField("Xác nhận")
