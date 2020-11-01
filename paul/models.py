import json
import os
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms import SelectField, TextAreaField
from wtforms.validators import Length
from paul import db
from paul import login
from paul.config import INITIAL_SCORE, CARD_TYPES

tours = json.load(open(os.path.join(os.path.dirname(__file__), 'static', 'tours.json'), 'r'))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    curpos = db.Column(db.Integer, default=0)
    sel_tour = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    score = db.Column(db.String, default=str(INITIAL_SCORE))
    seen_cards = db.Column(db.String, default=str([]))
    b_places = db.Column(db.String, default=str({}))
    e_places = db.Column(db.String, default=str({}))
    c_places = db.Column(db.String, default=str({}))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return '<User {}>'.format(self.username)
    
@login.user_loader
def load_user(id):
    return User.query.get(int(id))

class Card(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tour = db.Column(db.String, info={'label': 'Missionary Tour', 'form_field_class': SelectField, 'choices': [('', 'N/A')] + [(tour, 'Missionary Tour {}'.format(tour)) for tour in ['1', '2', '3']]})
    location = db.Column(db.String, info={'label': 'Location'})
    type = db.Column(db.String, info={'label': 'Type', 'form_field_class': SelectField, 'choices': CARD_TYPES})
    content = db.Column(db.String, info={'label': 'Content', 'form_field_class': TextAreaField})
    result = db.Column(db.String, info={'label': 'Answer/Result', 'form_field_class': TextAreaField})
    more_info = db.Column(db.String, info={'label': 'Further Info', 'form_field_class': TextAreaField})
    score = db.Column(db.String, info={'label': 'Score'})
 
class UserTurn(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.String, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref='userturn')
    miss_turn = db.Column(db.String, default=str([]))
    won = db.Column(db.String)
    game_over = db.Column(db.String, default=str([]))