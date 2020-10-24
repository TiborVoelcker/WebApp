from app import app
from flask import render_template

from .models import  Game

@app.route('/')
@app.route('/index')
def index():
    return "Hello, World!"

@app.route('/game/<string:slug>')
def game(slug):
    g = Game.query.get_or_404(slug)
    return render_template('game.html', game=g)
