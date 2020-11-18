import os
from datetime import timedelta

from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    load_dotenv()

    ENV = 'production'

    SECRET_KEY = os.environ.get('SECRET_KEY') or '7Drjg22xkRxlMHdy1FiC3XyJLJcjAsSxpsY_Aj_D5CI'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    DEBUG = False
    TESTING = False
    LOG_TO_STDOUT = False
    LOG_TO_FILE = True
    SCHEDULER_API_ENABLED = False
    JOBS = [{
        'id': 'housekeeping',
        'func': 'app.tasks:housekeeping',
        'trigger': 'cron',
        'hour': '8-16/4, 16-22/2'
    }]
    SCHEDULER_ENABLED = True
    INACTIVE_TIME_DELAY = timedelta(minutes=1)


class DevelopmentConfig(Config):
    ENV = 'development'
    DEBUG = True
    LOG_TO_STDOUT = True
    LOG_TO_FILE = False
    SCHEDULER_ENABLED = True


class ProductionConfig(Config):
    pass


class TestingConfig(Config):
    ENV = 'development'
    DEBUG = True
    TESTING = True
    LOG_TO_STDOUT = False
    LOG_TO_FILE = False
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///'
    SCHEDULER_ENABLED = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
}
