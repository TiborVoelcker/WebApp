import logging
import os
import random
from logging.handlers import TimedRotatingFileHandler

from flask import Flask
from flask.logging import default_handler
from flask_apscheduler import APScheduler
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy

from config import config

random.seed()

# Flask extensions
db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view = 'auth.login'
login.login_message = 'Please log in to access this page.'
socketio = SocketIO()
scheduler = APScheduler()

from . import models


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize flask extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    socketio.init_app(app)
    scheduler.init_app(app)

    # Register blueprints
    from app.errors import bp as errors_bp
    app.register_blueprint(errors_bp)

    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp)

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    # Handle logging behaviour
    if app.config["LOG_TO_STDOUT"]:
        default_handler.setFormatter(logging.Formatter('%(message)s'))
    else:
        app.logger.removeHandler(default_handler)

    if app.config["LOG_TO_FILE"]:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = TimedRotatingFileHandler('logs/webgame.logs', when="midnight", backupCount=7)
        # file_handler.setFormatter(logging.Formatter(""))
        app.logger.addHandler(file_handler)

    app.logger.setLevel(logging.INFO)
    app.logger.info(f"WebGame startup with configuration [{config_name}]")

    # Handle tasks
    if app.config["SCHEDULER_ENABLED"]:
        from app import tasks

        scheduler.start()
        app.logger.info(f"Started tasks: {[job.name for job in scheduler.get_jobs()]}")

    return app
