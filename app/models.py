import json
import os
from random import choices

from flask_login import UserMixin
from flask_socketio import join_room

from app import db, login
from config import basedir


def make_slug():
    path = os.path.abspath(os.path.join(basedir, 'app/short_words.json'))
    with open(path, "r") as f:
        words = json.load(f)
        slug = "_".join(choices(words, k=3))
    if Game.query.get(slug):
        slug = make_slug()

    return slug


class Player(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    sid = db.Column(db.Integer)
    name = db.Column(db.String(32), db.CheckConstraint("name != ''"), index=True, nullable=False)
    __role = db.Column(db.String(16))
    __voted = db.Column(db.Boolean, nullable=True, default=None)

    game_slug = db.Column(db.String(64), db.ForeignKey('game.slug'))
    game = db.relationship("Game", back_populates="players", foreign_keys=game_slug)

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name

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
                join_room(f"{self.current_game.slug} - fascist", sid=self.sid)
        else:
            raise TypeError(f"Role was invalid! ({self.role})")

    def get_role(self):
        return self.__role


class Game(db.Model):
    slug = db.Column(db.String(64), unique=True, nullable=False, index=True, primary_key=True, default=make_slug)
    turn_no = db.Column(db.Integer, nullable=False, default=1)
    current_state = db.Column(db.String(16), nullable=False, default='pre_game')
    elected_policies = db.Column(db.PickleType(), nullable=False, default=list())
    __remaining_policies = db.Column(db.PickleType(), nullable=False,
                                     default=[1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])

    current_president_id = db.Column(db.Integer, db.ForeignKey('player.id', use_alter=True))
    current_president = db.relationship("Player", foreign_keys=current_president_id,
                                        primaryjoin="and_(Game.current_president_id == Player.id,"
                                                    "Game.slug == Player.game_slug)")

    current_chancellor_id = db.Column(db.Integer, db.ForeignKey('player.id', use_alter=True))
    current_chancellor = db.relationship("Player", foreign_keys=current_chancellor_id,
                                         primaryjoin="and_(Game.current_chancellor_id == Player.id,"
                                                     "Game.slug == Player.game_slug)")

    last_president_id = db.Column(db.Integer, db.ForeignKey('player.id', use_alter=True))
    last_president = db.relationship("Player", foreign_keys=last_president_id,
                                     primaryjoin="and_(Game.last_president_id == Player.id,"
                                                 "Game.slug == Player.game_slug)")

    last_chancellor_id = db.Column(db.Integer, db.ForeignKey('player.id', use_alter=True))
    last_chancellor = db.relationship("Player", foreign_keys=last_chancellor_id,
                                      primaryjoin="and_(Game.last_chancellor_id == Player.id,"
                                                  "Game.slug == Player.game_slug)")

    players = db.relationship('Player', back_populates="game", foreign_keys=Player.game_slug)

    def __repr__(self):
        return self.slug

    def __str__(self):
        return self.slug

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
        else:
            num_liberals = len(self.players) // 2 + 1
            roles = ["liberal"] * num_liberals + ["fascist"] * (len(self.players) - 1 - num_liberals) + ["hitler"]
            for player in self.players:
                player.set_role(roles.pop())
            return True

    def get_roles(self):
        return {player.id: player.get_role() for player in self.players}

    def get_hitler(self):
        for player in self.players:
            if player.get_role() == "hitler":
                return player
        raise RuntimeError("No Hitler in current game found!")


@login.user_loader
def load_user(id):
    return Player.query.get(int(id))
