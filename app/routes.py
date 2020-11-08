from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse

from app import app, db
from .forms import LoginForm, GameForm
from .helper import make_slug
from .models import Game, Player


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
    form = GameForm()
    if form.is_submitted():
        if form.submit.data and form.validate():
            g = Game.query.get(form.game_slug.data)
            if g:
                return redirect(url_for('game', slug=form.game_slug.data))
            else:
                flash("Game ID is invalid.")
                return redirect(url_for('index'))
        if form.new_game.data:
            slug = make_slug()
            g = Game(slug=slug)
            db.session.add(g)
            db.session.commit()
            return redirect(url_for('game', slug=slug))

    return render_template('index.html', title="Home", form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = Player(name=form.username.data)
        db.session.add(user)
        db.session.commit()
        login_user(user, remember=form.remember_me.data)
        flash(f'Hello {user.name}!')

        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title="Login", form=form)


@app.route('/logout')
def logout():
    if current_user.is_authenticated:
        db.session.delete(current_user)
        db.session.commit()
        logout_user()
        flash(f'Successfully logged out.')
    return redirect(url_for('index'))


@app.route('/join/<string:slug>')
def join(slug):
    return redirect(url_for('game', slug=slug))


@app.route('/game/<string:slug>')
@login_required
def game(slug):
    g = Game.query.get_or_404(slug)
    return render_template('game.html', game=g)
