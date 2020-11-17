import functools

from flask_login import current_user
from flask_socketio import disconnect

from .models import Player


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
            g = current_user.current_game
            if g.current_state == state:
                return func(g, *args)
            else:
                return False, 'You cannot do that right now!'

        return inner

    return wrapper


def tuple_to_player(player_tuple):
    return Player.query.get(player_tuple[0])


def player_to_tuple(player):
    return (player.id, player.name)
