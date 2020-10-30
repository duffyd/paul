import json
import os
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SelectField, SubmitField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from wtforms_alchemy import model_form_factory
from paul.models import User, Card
from paul import db

BaseModelForm = model_form_factory(FlaskForm)

class ModelForm(BaseModelForm):
    @classmethod
    def get_session(self):
        return db.session

tours = json.load(open(os.path.join(os.path.dirname(__file__), 'static', 'tours.json'), 'r'))

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')
    
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    sel_tour = SelectField('Select Missionary Tour', validators=[DataRequired()], choices=[(tour, 'Missionary Tour {}'.format(tour)) for tour in ['1', '2', '3']])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')
        
class UserForm(ModelForm):
    class Meta:
        model = User
        #exclude = ['created_at']
        
    submit = SubmitField('Save')
    
class CardForm(ModelForm):
    class Meta:
        model = Card
        
    submit = SubmitField('Save')