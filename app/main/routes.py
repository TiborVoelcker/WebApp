from flask import render_template, redirect, url_for, flash, jsonify, request
from flask_login import current_user

from app import db
from app.main import bp
from app.models import Game
from .forms import IndexForm, LoginForm, AdminForm


@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
def index():
    if current_user.is_authenticated:
        redirect(url_for('.game', slug=current_user.game))
    form = IndexForm()
    if form.is_submitted():
        if form.submit.data and form.validate():
            g = Game.query.get(form.game_slug.data)
            if g:
                return redirect(url_for('.lobby', slug=form.game_slug.data, admin=False))
            else:
                flash("Game ID is invalid.")
        if form.new_game.data:
            g = Game()
            db.session.add(g)
            db.session.commit()
            return redirect(url_for('.lobby', slug=g.slug, admin=True))

    return render_template('index.html', title="Home", form=form)


@bp.route('/game/<string:slug>/lobby')
def lobby(slug):
    g = Game.query.get_or_404(slug)
    if not g.current_state == "pre_game":
        redirect(url_for(".game", slug=g.slug))

    login_form = LoginForm()

    admin_form = None
    if request.args.get("admin"):
        admin_form = AdminForm()
    return render_template('lobby.html', game=g, loginform=login_form, adminform=admin_form)


@bp.route('/game/<string:slug>')
def game(slug):
    g = Game.query.get_or_404(slug)
    if g.current_state == "pre_game":
        redirect(url_for(".game", slug=g.slug))

    return render_template('game.html', game=g)


@bp.route('/game/<string:slug>/gamestate')
def gamestate(slug):
    g = Game.query.get_or_404(slug)

    return jsonify(players=g.player_list(),
                   current_state=g.current_state,
                   current_president=g.current_president,
                   current_chancellor=g.current_chancellor)


@bp.route('/game/<string:slug>/secrets')
def secrets(slug):
    g = Game.query.get_or_404(slug)

    if current_user.is_authenticated:
        if not g.current_state == "pre_game":
            if current_user.game == g and current_user.get_role() == "fascist" \
                    or len(g.players) < 7 and current_user.get_role() == "hitler":
                return jsonify(g.get_roles())
            else:
                return jsonify(success=False, message="You are not allowed!"), 403
        else:
            return jsonify(success=False, message="The game has not started yet!"), 403
    else:
        return jsonify(success=False, message="You must be in a game!"), 401
