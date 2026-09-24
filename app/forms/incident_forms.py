from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length
from app.utils.constants import TYPES, PRIORITIES, STATUSES

class IncidentForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=150)])
    description = TextAreaField('Description', validators=[DataRequired()])
    type = SelectField('Type', choices=[(t, t) for t in TYPES], validators=[DataRequired()])
    category_id = SelectField('Category', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Submit')

class IncidentUpdateForm(FlaskForm):
    type = SelectField('Type', choices=[(t, t) for t in TYPES], validators=[DataRequired()])
    category_id = SelectField('Category', coerce=int, validators=[DataRequired()])
    priority = SelectField('Priority', choices=[(p, p) for p in PRIORITIES], validators=[DataRequired()])
    status = SelectField('Status', choices=[(s, s) for s in STATUSES], validators=[DataRequired()])
    submit = SubmitField('Update Incident')

class IncidentReporterEditForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=150)])
    description = TextAreaField('Description', validators=[DataRequired()])
    type = SelectField('Type', choices=[(t, t) for t in TYPES], validators=[DataRequired()])
    category_id = SelectField('Category', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Save Changes')

class IncidentAssignForm(FlaskForm):
    assignee_id = SelectField('Assign to Agent', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Assign')

class IncidentCommentForm(FlaskForm):
    content = TextAreaField('Add a comment...', validators=[DataRequired()])
    submit = SubmitField('Post Comment')
