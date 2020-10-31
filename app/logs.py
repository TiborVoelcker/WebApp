import logging

from flask.logging import default_handler

from . import app

if app.debug:
    app.logger.removeHandler(default_handler)
    ch = logging.StreamHandler()
    formatter = logging.Formatter('%(message)s')
    ch.setFormatter(formatter)
    app.logger.addHandler(ch)