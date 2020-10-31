import random

from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy

from config import Config

random.seed()

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
socketio = SocketIO(app)
login = LoginManager(app)
login.login_view = 'login'

from app import routes, models, sockets, logs
