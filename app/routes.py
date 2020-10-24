from app import app, db
from flask import render_template, session, flash, redirect, url_for

from .models import Game, Player
from .forms import LoginForm, GameForm


@app.route('/')
@app.route('/index')
def index():
    p = Player.query.get(session["ID"])
    form = GameForm()
    return render_template('index.html', title="Home", username=p.name, form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        flash(f'Login requested for user {form.username.data}, remember_me={form.remember_me.data}')
        return redirect(url_for('index'))
    return render_template('login.html', title="Login", form=form)


@app.route('/game/<string:slug>')
def game(slug):
    g = Game.query.get_or_404(slug)
    p = Player.query.get(session["ID"])
    g.players.append(p)

    return render_template('game.html', game=g)
