from random import choices

from flask_login import UserMixin
from flask_socketio import join_room

from app import db, login


class Game(db.Model):
    slug = db.Column(db.String(64), unique=True, nullable=False, index=True, primary_key=True)
    players = db.relationship('Player', backref='current_game', foreign_keys='[Player.game]')
    current_president = db.Column(db.Integer, db.ForeignKey('player.id'))
    current_chancellor = db.Column(db.Integer, db.ForeignKey('player.id'))
    last_president = db.Column(db.Integer, db.ForeignKey('player.id'))
    last_chancellor = db.Column(db.Integer, db.ForeignKey('player.id'))
    turn_no = db.Column(db.Integer, nullable=False, default=1)
    current_state = db.Column(db.String(16), nullable=False, default='pre_game')
    elected_policies = db.Column(db.PickleType(), nullable=False, default=list())
    __remaining_policies = db.Column(db.PickleType(), nullable=False,
                                     default=[1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])

    def __repr__(self):
        return f"Game {self.slug}"

    def everybody_voted(self):
        return all(player.get_vote() is not None for player in self.players)

    def evaluate_votes(self):
        accepted = [player for player in self.players if player.get_vote()]
        rejected = [player for player in self.players if not player.get_vote()]
        return accepted > rejected

    def clear_votes(self):
        for player in self.players:
            player.set_vote(None)

    def advance_president(self):
        i = self.players.index(self.current_president)
        try:
            self.current_president = self.players[i+1]
        except IndexError:
            self.current_president = self.players[0]

    def get_policies(self):
        select = choices(self.__remaining_policies, k=3)
        for item in select:
            self.__remaining_policies.remove(item)
        if len(self.__remaining_policies) < 3:
            self.__remaining_policies = [1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        return select

    def make_roles(self):
        if len(self.players) > 10 or len(self.players) < 5:
            return False
        num_liberals = len(self.players) // 2 + 1
        roles = ["liberal"] * num_liberals + ["facsist"] * (len(self.players) - 1 - num_liberals) + ["hitler"]
        for player in self.players:
            player.set_role(roles.pop())
        return True

    def get_fascists(self):
        return [player for player in self.player if player.get_role() == "fascist"]


class Player(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    sid = db.Column(db.Integer)
    name = db.Column(db.String(32), index=True)
    game = db.Column(db.String(64), db.ForeignKey('game.slug'))
    __role = db.Column(db.String(16))
    __voted = db.Column(db.Boolean, nullable=True, default=None)

    def __repr__(self):
        return f"User {self.name} (ID: {self.id})"

    def get_vote(self):
        return self.__voted

    def set_vote(self, vote):
        if type(vote) is bool or vote is None:
            self.__voted = vote
        else:
            raise TypeError(f"Type of the vote needs to be None or Bool (was: {type(vote)})!")

    def set_role(self, role):
        if role == "fascist" or role == "liberal" or role == "hitler":
            self.__role = role
            if role == "fascist":
                join_room(f"{self.game.slug} - fascist", sid=self.sid)
        else:
            raise TypeError(f"Role was invalid! ({self.role})")

    def get_role(self):
        return self.__role


@login.user_loader
def load_user(id):
    return Player.query.get(int(id))
