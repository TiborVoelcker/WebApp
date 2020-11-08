import random

from flask import request
from flask_login import current_user
from flask_socketio import emit, join_room, leave_room, close_room

from app import socketio, db
from app.helper import check_game_state, dict_to_player, player_to_dict, authenticated_only
from app.main import bp
from app.models import Game


@socketio.on('connect')
def handle_connect():
    if current_user.is_authenticated:
        current_user.sid = request.sid
        slug = request.args["game"]
        g = Game.query.get(slug)
        join_room(g.slug)
        current_user.current_game = g
        db.session.commit()
        emit("player joined", player_to_dict(current_user), room=g.slug)
        bp.logger.info(f"{g.slug} - Player {current_user.name} connected.")
        return True
    else:
        return False


@socketio.on('disconnect')
@authenticated_only
def handle_disconnect():
    g = current_user.current_game
    leave_room(g.slug)
    current_user.current_game = None
    if g.players:
        emit("player left", player_to_dict(current_user), room=g.slug)
    else:
        close_room(g.slug)
        db.session.delete(g)
    db.session.commit()
    bp.logger.info(f"{g.slug} - Player {current_user.name} disconnected.")
    return True


@socketio.on('start game')
@authenticated_only
@check_game_state("pre_game")
def handle_start_game(g):
    if g.make_roles():
        g.current_state = "nomination"
        g.current_president = random.choice(g.players)
        emit("new president", player_to_dict(g.current_president), room=g.slug)
        bp.logger.info(f"{g.slug} - Game started.")
        emit("roles", g.get_roles(), room=f"{g.slug} - fascist")
        if len(g.players) < 7:
            emit("roles", g.get_roles(), room=g.get_hitler().sid)
        return True
    else:
        return False, f'The number of players need to be between 5 and 10 players! (currently {len(g.players)})'


@socketio.on('nomination')
@authenticated_only
@check_game_state("nomination")
def handle_nomination(g, nomination):
    nomination = dict_to_player(nomination)
    if g.current_president == current_user:
        if nomination in g.players and not nomination == g.last_president and not nomination == g.last_chancellor:
            g.current_state = "election"
            g.current_chancellor = nomination
            emit("new nomination", player_to_dict(nomination), room=g.slug)
            bp.logger.info(f"{g.slug} - Player {nomination.name} was nominated.")
            return True
        else:
            return False, 'Invalid Nomination! (Player is not in the game or was last elected)'
    else:
        return False, 'Only the president can nominate a chancellor!'


@socketio.on('election')
@authenticated_only
@check_game_state("election")
def handle_election(g, vote):
    if current_user.get_vote() is None:
        current_user.set_vote(vote)
        if g.everybody_voted():
            if g.evaluate_votes():
                if g.elected_polices.count(1) >= 3 and g.current_chancellor.role == "hitler":
                    g.current_state = "post_game"
                    emit("game ended", "fascist", room=g.slug)
                else:
                    g.current_state = "policies_president"
                    emit("new chancellor", player_to_dict(g.current_chancellor), room=g.slug)
                    emit("choose policies", g.select_policies(), room=g.current_president.sid)
                    bp.logger.info(f"{g.slug} - Player {g.current_chancellor} was elected.")
            else:
                g.current_state = "nomination"
                g.advance_president()
                g.current_chancellor = None
                emit("new president", player_to_dict(g.current_president), room=g.slug)
                bp.logger.info(f"{g.slug} - Nomination was rejected.")
            g.clear_votes()
        return True
    else:
        return False, 'You already voted!'


@socketio.on('policies president')
@authenticated_only
@check_game_state("policies_president")
def handle_policies_president(g, policies):
    if g.current_president == current_user:
        if all(policy in [0, 1] for policy in policies) and len(policies) == 2:
            g.current_state = "policies_chancellor"
            emit('president chose policies', room=g.slug)
            emit('choose polices', policies, room=g.current_chancellor.sid)
            bp.logger.info(f"{g.slug} - The president chose {policies}.")
            return True
        else:
            return False, 'Your selection is invalid!'
    else:
        return False, 'Only the president can elect polices right now!'


@socketio.on('policies chancellor')
@authenticated_only
@check_game_state("policies_chancellor")
def handle_chancellor_policy_chosen(g, policy):
    if g.current_chancellor == current_user:
        if policy in [0, 1]:
            g.elected_polices.append(policy)
            emit("chancellor chose policy", policy, room=g.slug)
            bp.logger.info(f"{g.slug} - New policy enacted: {policy}")
            if g.elected_polices.count(1) == 6:
                g.current_state = "post_game"
                emit("game ended", "fascist", room=g.slug)
            elif g.elected_polices.count(0) == 5:
                g.current_state = "post_game"
                emit("game ended", "liberals", room=g.slug)
            else:
                g.current_state = "nomination"
                g.last_president = g.current_president
                g.last_chancellor = g.last_chancellor
                g.advance_president()
                g.current_chancellor = None
                emit("new president", player_to_dict(g.current_president), room=g.slug)
            return True
        else:
            return False, 'Your selection is invalid!'
    else:
        return False, 'Only the chancellor can elect polices right now!'


@socketio.on_error()
def handle_error(e):
    emit('error', e)
    raise e
