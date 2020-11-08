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


def dict_to_player(player_dict):
    return Player.query.get(player_dict["id"])


def player_to_dict(player):
    return {"name": player.name, "id": player.id}
