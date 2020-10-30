import os
from flask import (
    Flask, flash, g, redirect, render_template, request, session, url_for
)
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from paul.config import Config

app = Flask(__name__, instance_relative_config=True)
app.config.from_object(Config)
app.jinja_env.globals['adminuser'] = os.environ.get('ADMIN_USER', None)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login = LoginManager(app)
login.init_app(app)
login.login_view = 'login'

from paul import routes, models