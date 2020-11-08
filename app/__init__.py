import logging
import random

from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy

from config import Config

random.seed()

db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view = 'auth.login'
login.login_message = 'Please log in to access this page.'
socketio = SocketIO()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    socketio.init_app(app)

    from app.errors import bp as errors_bp
    app.register_blueprint(errors_bp)

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp)

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    if app.debug and not app.testing:  # ToDo: log to file, and check if removeHandler is necessary
        # app.logger.removeHandler(default_handler)
        ch = logging.StreamHandler()
        formatter = logging.Formatter('%(message)s')
        ch.setFormatter(formatter)
        app.logger.addHandler(ch)

    return app


from app import models
