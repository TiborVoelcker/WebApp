import os

from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    dotenv_path = os.path.join(basedir, ".flaskenv")
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)

    SECRET_KEY = os.environ.get('SECRET_KEY') or '7Drjg22xkRxlMHdy1FiC3XyJLJcjAsSxpsY_Aj_D5CI'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
