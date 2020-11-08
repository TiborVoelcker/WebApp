from flask import Blueprint

bp = Blueprint('main', __name__, template_folder='templates', static_folder='static', url_prefix="/main")

from app.main import routes, sockets
