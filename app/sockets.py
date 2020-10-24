from flask import session
from flask_socketio import emit
from . import socketio

from .models import Game, Player


@socketio.on('new_state', namespace="/event")
def handle_my_custom_event(json):
    r = request.sid
    print('received json: ' + str(json))


@socketio.on('nominate_chancellor', namespace="/vote")
def handle_nominate_chancellor(nomination, game_slug):
    g = Game.query.get(game_slug)


@socketio.on('connect')
def new_player():
    emit('my response', {'data': 'Connected'})

@socketio.on('disconnect')
def test_disconnect():
    print('Client disconnected')