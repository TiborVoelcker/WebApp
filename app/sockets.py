import os.path
import random

from flask import request
from flask_login import current_user, login_required
from flask_socketio import emit, join_room, leave_room, close_room

from . import socketio, db, app
from .models import Game


@socketio.on('connect')
@login_required
def handle_connect():
    current_user.sid = request.sid
    slug = os.path.split(request.referrer)[1]
    g = Game.query.get(slug)
    join_room(g.slug)
    current_user.current_game = g
    emit("player joined", {"name": current_user.name, "id": current_user.id}, room=g.slug)
    db.session.commit()
    app.logger.info(f"{g.slug} - Player {current_user.name} connected.")


@socketio.on('disconnect')
@login_required
def handle_disconnect():
    g = current_user.current_game
    leave_room(g.slug)
    current_user.current_game = None
    if g.players:
        emit("player left", {"name": current_user.name, "id": current_user.id}, room=g.slug)
    else:
        close_room(g.slug)
        db.session.delete(g)
    db.session.commit()
    app.logger.info(f"{g.slug} - Player {current_user.name} disconnected.")


@socketio.on('start game')
@login_required
def handle_game_start():
    g = current_user.current_game
    if g.make_roles():
        g.current_state = "nomination"
        g.current_president = random.choice(g.players)
        emit("nomination", room=g.slug)
        app.logger.info(f"{g.slug} - Game {g.slug} started.")
        emit("roles", g.get_roles(), room=f"{g.slug} - fascist")
    else:
        emit("error", f'The number of players need to be between 5 and 10 players! (currently {len(g.players)})')


@socketio.on('nominate chancellor')
@login_required
def handle_nominate_chancellor(player):
    g = current_user.current_game
    if g.current_state == "nomination":
        if g.current_president == current_user:
            if player in g.players and not player == g.last_president and not player == g.last_chancellor:
                g.current_state = "election"
                g.current_chancellor = player
                emit("election", player, room=g.slug)
                app.logger.info(f"{g.slug} - Player {player.name} was nominated.")
            else:
                emit("error", 'Invalid Nomination! (Player is not in the game or was last elected)')
        else:
            emit("error", 'Only the president can nominate a chancellor!')
    else:
        emit("error", 'You cannot nominate a chancellor right now!')


@socketio.on('elect chancellor')
@login_required
def handle_elect_chancellor(vote):
    g = current_user.current_game
    if g.current_state == "election":
        if current_user.get_vote() is None:
            current_user.set_vote(vote)
            if g.everybody_voted():
                if g.evaluate_votes():
                    if g.elected_polices.count(1) >= 3 and g.current_chancellor.role == "hitler":
                        emit("game ended", "fascist", room=g.slug)
                    else:
                        g.current_state = "policies_president"
                        emit("new chancellor", g.current_chancellor, room=g.slug)
                        emit("choose policies", g.select_policies(), room=g.current_president.sid)
                        app.logger.info(f"{g.slug} - Player {g.current_chancellor} was elected.")
                else:
                    g.current_state = "nomination"
                    g.advance_president()
                    g.current_chancellor = None
                    emit("nomination", room=g.slug)
                    app.logger.info(f"{g.slug} - Nomination was rejected.")
        else:
            emit('error', 'You already voted!')
    else:
        emit('error', 'You cannot elect a chancellor right now!')


@socketio.on('policies chosen')
@login_required
def handle_policies_chosen(policies):
    g = current_user.current_game
    if g.current_state == "policies_president":
        if g.current_president == current_user:
            if all(policy in [0, 1] for policy in policies) and len(policies) == 2:
                emit('choose polices', policies, room=g.current_chancellor.sid)
                app.logger.info(f"{g.slug} - The president chose {policies}.")
            else:
                emit('error', 'Your selection is invalid!')
        else:
            emit('error', 'Only the president can elect polices right now!')
    else:
        emit('error', 'You cannot elect policies right now!')
    if g.current_state == "policies_chancellor":
        if g.current_chancellor == current_user:
            if all(policy in [0, 1] for policy in policies) and len(policies) == 1:
                policy = policies[0]
                g.elected_polices.append(policy)
                if g.elected_polices.count(1) == 6:
                    emit("game ended", "fascist", room=g.slug)
                elif g.elected_polices.count(0) == 5:
                    emit("game ended", "liberals", room=g.slug)
                else:
                    g.current_state = "nomination"
                    g.last_president = g.current_president
                    g.last_chancellor = g.last_chancellor
                    g.advance_president()
                    g.current_chancellor = None
                    emit("nomination", room=g.slug)
                    app.logger.info(f"{g.slug} - The president chose {policies[0]}.")
            else:
                emit('error', 'Your selection is invalid!')
        else:
            emit('error', 'Only the chancellor can elect polices right now!')
    else:
        emit('error', 'You cannot elect policies right now!')


@socketio.on_error()
def handle_error(e):
    pass
