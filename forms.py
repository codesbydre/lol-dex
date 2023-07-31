from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length
from models import User
from database import bcrypt, db
from flask import flash

class SignupForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is taken. Please choose a different one.')
    
    def save_user(self):
        try:
            hashed_password = bcrypt.generate_password_hash(self.password.data).decode('utf-8')
            user = User(username=self.username.data, email=self.email.data, password=hashed_password)
            db.session.add(user)
            db.session.commit()
        except Exception as e:
            flash('An error occurred while creating the user. Please try again.', 'error')
            print(f"Error: {e}")

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class UserEditForm(FlaskForm):
    image_url = StringField('Profile Image URL')
    bio = StringField('Bio')
    summoner_name = StringField('Summoner Name')
    submit = SubmitField('Update Profile')

class CommentForm(FlaskForm):
    content = TextAreaField('Content', validators=[DataRequired(), Length(min=1, max=500)])
    submit = SubmitField('Post')
