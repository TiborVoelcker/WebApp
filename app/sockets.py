from flask import request
from flask_socketio import emit, join_room, leave_room, close_room
from flask_login import current_user
import random

from . import socketio, db
from .models import Player, Game


@socketio.on('connect')
def handle_connect():
    g = current_user.current_game
    join_room(g.slug)
    emit("player joined", {"name": current_user.name, "id": current_user.id}, room=g.slug)
    print(f"Player {current_user.name} connected.")


@socketio.on('disconnect')
def handle_disconnect():
    g = current_user.current_game
    leave_room(g.slug)
    current_user.current_game = None
    if g.players.all():
        emit("player left", {"name": current_user.name, "id": current_user.id}, room=g.slug)
    else:
        close_room(g.slug)
        db.session.delete(g)
    db.session.commit()
    print(f"Player {current_user.name} disconnected.")


@socketio.on('game start')
def handle_game_start():
    g = current_user.current_game
    g.current_state = "nomination"
    g.current_chancellor = random.choice(g.players)
    emit("new state", g.return_public(), room=g.slug)


@socketio.on('nominate chancellor')
def handle_nominate_chancellor(player):
    g = current_user.current_game
    g.current_state = "election"
    g.current_chancellor = g.players.filter(Player.id == player.id).first()
    emit("election", player, room=g.slug)
