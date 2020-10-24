from app import app, db
from flask import render_template, session, flash, redirect, url_for, request
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse

from .models import Game, Player
from .forms import LoginForm, GameForm


@app.route('/')
@app.route('/index')
def index():
    form = GameForm()
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
    logout_user()
    return redirect(url_for('index'))


@login_required
@app.route('/game/<string:slug>')
def game(slug):
    g = Game.query.get_or_404(slug)
    p = Player.query.get(session["ID"])
    g.players.append(p)

    return render_template('game.html', game=g)
