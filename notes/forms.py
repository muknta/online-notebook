from flask_wtf import FlaskForm
from wtforms import (
		StringField,
		TextAreaField,
		SubmitField,
		PasswordField,
		BooleanField,
		RadioField
	)
from wtforms.fields.html5 import EmailField
from wtforms.validators import (
		DataRequired, EqualTo, Length
	)


class NoteForm(FlaskForm):
	title = StringField('Title', validators=[DataRequired(),
										Length(max=100)])
	text = TextAreaField('Text')
	save = SubmitField('Save')
	publish = SubmitField('Publish')


class UserNoteParamsForm(FlaskForm):
	access = RadioField('access', choices=['private','public'])
	encryption = BooleanField('encryption')
	change_possibility = BooleanField('change possibility')


class RegisterForm(FlaskForm):
	username = StringField('Username *', validators=[DataRequired()])
	password = PasswordField('Password *', validators=[
				DataRequired(),
				Length(min=8, max=40),
				EqualTo('confirm', message='Passwords must match')
			])
	confirm = PasswordField('Repeat Password *')
	email = EmailField('Email')
	submit = SubmitField('Sign Up')


class LoginForm(FlaskForm):
	username = StringField('Username', validators=[DataRequired()])
	password = PasswordField('Password', validators=[DataRequired()])
	remember_me = BooleanField('Remember me')
	submit = SubmitField('Sign In')


class UserForm(FlaskForm):
	username = StringField('Username *', validators=[DataRequired(),
										Length(max=30)])
	curr_password = PasswordField('Current password *', validators=[DataRequired()])
	new_password = PasswordField('New password', validators=[
				Length(max=40),
				EqualTo('confirm', message='Passwords must match')
			])
	confirm = PasswordField('Repeat password')
	email = EmailField('Email', validators=[Length(max=50)])
	submit = SubmitField('Update')
