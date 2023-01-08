from app.models import Player


def tuple_to_player(player_tuple):
    p = Player.query.get(player_tuple[0])
    if p is None:
        raise ValueError(f"This player does not exist: {player_tuple}")
    return p


def player_to_tuple(player):
    return player.id, player.name