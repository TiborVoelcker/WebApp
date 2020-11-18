import functools
import random

from flask import request, current_app
from flask_login import current_user
from flask_socketio import emit, join_room, leave_room, disconnect

from app import socketio, db
from app.models import Game
from app.models import Player


# ToDo: change commit to flush? Automatically commit on right times (maybe from model methods?)

def authenticated_only(f):
    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            disconnect()
        else:
            return f(*args, **kwargs)
    return wrapped


def check_game_state(state):
    def wrapper(func):
        def inner(*args):
            g = current_user.game
            if g.current_state == state:
                return func(g, *args)
            else:
                return False, 'You cannot do that right now!'

        return inner

    return wrapper


def tuple_to_player(player_tuple):
    return Player.query.get(player_tuple[0])


def player_to_tuple(player):
    return player.id, player.name


@socketio.on('connect')
@authenticated_only
def handle_connect(s=None):
    current_user.sid = request.sid

    if s or request.args["game"]:
        return handle_join_game(s)
    else:
        return True


@socketio.on('join game')
@authenticated_only
def handle_join_game(s=None):
    if not current_user.game:
        slug = s or request.args["game"]
        g = Game.query.get(slug)

        current_user.game = g
        join_room(g.slug)
        emit("player joined", player_to_tuple(current_user), room=g.slug, skip_sid=current_user.sid)

        current_app.logger.info(f"{g} - {current_user} joined.")
        db.session.commit()
        return True
    else:
        return False, f"You are already in a game! ({g})"


@socketio.on('disconnect')
@authenticated_only
def handle_disconnect():
    g = current_user.game

    leave_room(g.slug)
    emit("player left", player_to_tuple(current_user), room=g.slug)

    current_app.logger.info(f"{g} - {current_user} disconnected.")
    return True


@socketio.on('start game')
@authenticated_only
@check_game_state("pre_game")
def handle_start_game(g):
    if len(g.players) > 10 or len(g.players) < 5:
        roles = g.get_roles()
        for player in g.players:
            if player.get_role() == "fascist":
                join_room(f"{g.slug} - fascist", sid=player.sid)
        g.current_state = "nomination"

        g.current_president = random.choice(g.players)
        emit("new president", player_to_tuple(g.current_president), room=g.slug)
        emit("nominate chancellor", room=g.current_president.sid)

        emit("roles", roles, room=f"{g.slug} - fascist")
        if len(g.players) < 7:
            emit("roles", roles, room=g.get_hitler().sid)

        current_app.logger.info(f"{g} - Game started. {g.current_president} is the new president")
        db.session.commit()
        return True
    else:
        return False, f'The number of players need to be between 5 and 10 players! (currently {len(g.players)})'


@socketio.on('nomination')
@authenticated_only
@check_game_state("nomination")
def handle_nomination(g, nomination):
    nomination = tuple_to_player(nomination)
    if g.current_president == current_user:
        if nomination in g.players and not nomination == g.last_president and not nomination == g.last_chancellor:
            g.current_state = "election"

            g.current_chancellor = nomination
            emit("new nomination", player_to_tuple(nomination), room=g.slug)

            current_app.logger.info(f"{g} - {nomination} was nominated as chancellor.")
            db.session.commit()
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
                if g.elected_policies.count(1) >= 3 and g.current_chancellor.role == "hitler":
                    g.current_state = "post_game"

                    emit("game ended", "fascist", room=g.slug)
                    current_app.logger.info(f"{g} - Game ended. Fascists won.")
                else:
                    g.current_state = "policies_president"

                    emit("new chancellor", player_to_tuple(g.current_chancellor), room=g.slug)
                    emit("choose policies", g.select_policies(), room=g.current_president.sid)
                    current_app.logger.info(f"{g} - {g.current_chancellor} was elected as chancellor.")
            else:
                g.current_state = "nomination"

                g.advance_president()
                g.current_chancellor = None
                emit("new president", player_to_tuple(g.current_president), room=g.slug)
                emit("nominate chancellor", room=g.current_president.sid)
                current_app.logger.info(f"{g} - {g.current_chancellor} was rejected as chancellor. "
                                        f"{g.current_president} is the new president.")

            g.clear_votes()
        db.session.commit()
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

            current_app.logger.info(f"{g} - The president chose policies. Remaining policies:"
                                    f"[{', '.join([('liberal', 'fascist')[policy] for policy in policies])}]")
            db.session.commit()
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
            g.elected_policies += (policy,)
            emit("chancellor chose policy", policy, room=g.slug)
            current_app.logger.info(f"{g} - New policy enacted: {('liberal', 'fascist')[policy]}")

            if g.elected_policies.count(1) == 6:
                g.current_state = "post_game"

                emit("game ended", "fascist", room=g.slug)
                current_app.logger.info(f"{g} - Game ended. Fascists won.")
            elif g.elected_policies.count(0) == 5:
                g.current_state = "post_game"

                emit("game ended", "liberals", room=g.slug)
                current_app.logger.info(f"{g} - Game ended. Liberals won.")
            else:
                g.current_state = "nomination"

                g.last_president = g.current_president
                g.last_chancellor = g.last_chancellor
                g.advance_president()
                g.current_chancellor = None

                emit("new president", player_to_tuple(g.current_president), room=g.slug)
                emit("nominate chancellor", room=g.current_president.sid)
                current_app.logger.info(f"{g.current_president} is the new president.")

            db.session.commit()
            return True
        else:
            return False, 'Your selection is invalid!'
    else:
        return False, 'Only the chancellor can elect polices right now!'
