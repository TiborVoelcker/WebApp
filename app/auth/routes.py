from flask import redirect, url_for, flash, render_template, request
from flask_login import current_user, login_user, logout_user
from werkzeug.urls import url_parse

from app import db
from app.auth import bp
from app.auth.forms import GameForm, LoginForm
from app.models import Game, Player


@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
def index():
    form = GameForm()
    if form.is_submitted():
        if form.submit.data and form.validate():
            g = Game.query.get(form.game_slug.data)
            if g:
                current_user.game = None
                return redirect(url_for('main.game', slug=form.game_slug.data))
            else:
                flash("Game ID is invalid.")
                return redirect(url_for('.index'))
        if form.new_game.data:
            current_user.game = None
            g = Game()
            db.session.add(g)
            return redirect(url_for('main.game', slug=g.slug))
        if form.rejoin.data:
            return redirect(url_for('main.game', slug=current_user.game.slug))

    rejoin = False
    if not current_user.is_anonymous and current_user.game:
        rejoin = True
    return render_template('index.html', title="Home", form=form, rejoin=rejoin)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = Player(name=form.username.data)
        db.session.add(user)
        login_user(user, remember=form.remember_me.data)
        flash(f'Hello {user.name}!')

        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('.index')
        return redirect(next_page)
    return render_template('login.html', title="Login", form=form)


@bp.route('/logout')
def logout():
    if current_user.is_authenticated:
        db.session.delete(current_user)
        logout_user()
        flash(f'Successfully logged out.')
    return redirect(url_for('.index'))


@bp.after_app_request
def commit_session(response):
    db.session.commit()
    return response
