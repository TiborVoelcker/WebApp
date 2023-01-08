import functools
import random

from flask import request, current_app, session
from flask_login import current_user, login_user
from flask_socketio import emit, join_room
from werkzeug.datastructures import ImmutableMultiDict

from app import socketio, db
from app.main.forms import LoginForm, AdminForm
from app.main.helper import player_to_tuple, tuple_to_player
from app.models import Player, Game


def check_game_state(state):
    def wrapper(f):
        @functools.wraps(f)
        def wrapped(*args, **kwargs):
            g = current_user.game
            if not g.current_state == state:
                return False, 'You cannot do that right now!'
            return f(g, *args, **kwargs)

        return wrapped

    return wrapper


@socketio.on('connect', namespace="/lobby")
def handle_lobby_connect():
    g = Game.query.get_or_404(request.args.get("game"))
    join_room(g.slug, namespace="/lobby")

    current_app.logger.info(f"{g} - {request.sid} connected to the lobby.")
    return dict(success=True, status_code=200)


@socketio.on('login', namespace="/lobby")
def handle_login(form_data):
    g = Game.query.get_or_404(request.args.get("game"))
    print(session)
    print(current_user)
    print(request.cookies)
    form = LoginForm(ImmutableMultiDict(form_data))
    if form.validate():
        if current_user.is_authenticated:
            return dict(success=False, status_code=403, message="You are already logged in.")
        user = Player(name=form.username.data, game=g, sid=request.sid)
        db.session.add(user)
        db.session.commit()
        login_user(user, remember=form.remember_me.data)
        session["test"] = "testing"

        emit("players", g.player_list(), room=g.slug, namespace="/lobby")

        current_app.logger.info(f"{g} - {request.sid} logged in as {current_user}.")
        return dict(success=True, status_code=200)
    return dict(success=False, message="Form is not valid!", status_code=400)


@socketio.on('admin', namespace="/lobby")
def handle_admin(form_data):
    g = Game.query.get_or_404(request.args.get("game"))
    form = AdminForm(ImmutableMultiDict(form_data))
    if form.validate():
        if len(g.players) > 10 or len(g.players) < 5:
            return dict(success=False, status_code=403,
                        message=f'The number of players need to be between 5 and 10 players! '
                                f'(currently {len(g.players)})')
        g.get_roles()
        g.current_state = "nomination"
        g.current_president = random.choice(g.players)
        db.session.commit()

        emit("game started", namespace="/lobby")

        current_app.logger.info(f"{g} - Game started. {g.current_president} is the new president")
        return dict(success=True, status_code=200)
    else:
        return dict(success=False, message="Form is not valid!", status_code=400)


@socketio.on('connect', namespace="/game")
def handle_game_connect():
    if current_user.is_anonymous:
        return False
    g = current_user.game
    join_room(g.slug, namespace="/game")

    current_app.logger.info(f"{g} - {current_user} connected to the game.")
    return dict(success=True, status_code=200)


@socketio.on('nomination')
@check_game_state("nomination")
def handle_nomination(g, nomination):
    nomination = tuple_to_player(nomination)
    if g.current_president == current_user:
        if nomination in g.players and not nomination == g.last_president and not nomination == g.last_chancellor:
            g.current_state = "election"
            g.current_chancellor = nomination
            db.session.commit()
            emit("new nomination", player_to_tuple(nomination), room=g.slug)

            current_app.logger.info(f"{g} - {nomination} was nominated as chancellor.")
            return True
        else:
            return False, 'Invalid Nomination! (Player is not in the game or was last elected)'
    else:
        return False, 'Only the president can nominate a chancellor!'


@socketio.on('election')
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
@check_game_state("policies_president")
def handle_policies_president(g, policies):
    if g.current_president == current_user:
        if all(policy in [0, 1] for policy in policies) and len(policies) == 2:
            g.current_state = "policies_chancellor"
            db.session.commit()

            emit('president chose policies', room=g.slug)
            emit('choose polices', policies, room=g.current_chancellor.sid)

            current_app.logger.info(f"{g} - The president chose policies. Remaining policies:"
                                    f"[{', '.join([('liberal', 'fascist')[policy] for policy in policies])}]")
            return True
        else:
            return False, 'Your selection is invalid!'
    else:
        return False, 'Only the president can elect polices right now!'


@socketio.on('policies chancellor')
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
