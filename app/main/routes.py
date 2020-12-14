from flask import render_template
from flask_login import login_required

from app.main import bp
from app.models import Game


@bp.route('/game/<string:slug>')
@login_required
def game(slug):
    g = Game.query.get_or_404(slug)
    return render_template('game.html', game=g)
