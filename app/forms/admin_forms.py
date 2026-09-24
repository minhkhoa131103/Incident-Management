from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email, Length, Optional

class AdminUserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    role_id = SelectField('Role', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Create User')

class AdminUserEditForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField('Password (leave blank to keep current)', validators=[Optional(), Length(min=6)])
    role_id = SelectField('Role', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Update User')

class AdminCategoryForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=50)])
    description = StringField('Description', validators=[Length(max=200)])
    submit = SubmitField('Save Category')

class AdminRoleForm(FlaskForm):
    name = StringField('Role Name', validators=[DataRequired(), Length(max=50)])
    description = StringField('Description', validators=[Length(max=200)])
    submit = SubmitField('Save Role')
