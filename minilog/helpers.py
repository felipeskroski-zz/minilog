from bcrypt import hashpw, gensalt
from flask import (
    session
)
from functools import wraps
from wtforms import (
    Form, BooleanField, StringField, PasswordField, SelectField, HiddenField,
    TextAreaField, validators
)
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from werkzeug.utils import secure_filename

def create_hash(plaintext_password):
    """Create password hash to be stored in the database"""
    return hashpw(plaintext_password, gensalt())


def check_hash(password_attempt, hashed):
    """Checks the password hash against a test"""
    return hashpw(password_attempt, hashed) == hashed

# ----------------------------
# Forms
# ----------------------------
class SignupForm(FlaskForm):
    """Sets form for signup"""
    name = StringField('Name', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=35)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    confirm = PasswordField('Confirm Password')


class LoginForm(FlaskForm):
    """Sets form for login"""
    email = StringField('Email', [validators.Length(min=6, max=35)])
    password = PasswordField('Password', [
        validators.DataRequired()
    ])


class CategoryForm(FlaskForm):
    """Sets form for category creation"""
    name = StringField('Name', [validators.DataRequired()])


class ItemForm(FlaskForm):
    """Sets form for item creation"""
    name = StringField('Name', [validators.DataRequired()])
    body = TextAreaField('Description')
    category_id = SelectField('Category', coerce=int)
    upload = FileField()
