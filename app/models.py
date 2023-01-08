import json
import os
from datetime import datetime
from random import choices, shuffle

from flask_login import UserMixin
from sqlalchemy import event
from sqlalchemy.orm import validates

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
    sid = db.Column(db.Integer, unique=True)
    name = db.Column(db.String(32), db.CheckConstraint("name != ''"), index=True, nullable=False)
    position = db.Column(db.Integer)
    __role = db.Column(db.String(16))
    __voted = db.Column(db.Boolean, nullable=True, default=None)

    _game_slug = db.Column(db.String(64), db.ForeignKey('game.slug'), nullable=False)
    game = db.relationship("Game", back_populates="players", foreign_keys=_game_slug)

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name

    def get_vote(self):
        return self.__voted

    def set_vote(self, vote):
        assert type(vote) is bool or vote is None
        self.__voted = vote

    def set_role(self, role):
        assert role == "fascist" or role == "liberal" or role == "hitler"
        self.__role = role

    def get_role(self):
        return self.__role


class Game(db.Model):
    slug = db.Column(db.String(64), unique=True, nullable=False, index=True, primary_key=True, default=make_slug)
    turn_no = db.Column(db.Integer, nullable=False, default=1)
    current_state = db.Column(db.String(16), nullable=False, default='pre_game')
    elected_policies = db.Column(db.PickleType(), nullable=False, default=tuple())
    __remaining_policies = db.Column(db.PickleType(), nullable=False,
                                     default=[1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])

    last_active = db.Column(db.DateTime, default=datetime.utcnow)

    _current_president_id = db.Column(db.Integer, db.ForeignKey('player.id', use_alter=True))
    current_president = db.relationship("Player", foreign_keys=_current_president_id,
                                        primaryjoin="and_(Game._current_president_id == Player.id,"
                                                    "Game.slug == Player._game_slug)", post_update=True)

    _current_chancellor_id = db.Column(db.Integer, db.ForeignKey('player.id', use_alter=True))
    current_chancellor = db.relationship("Player", foreign_keys=_current_chancellor_id,
                                         primaryjoin="and_(Game._current_chancellor_id == Player.id,"
                                                     "Game.slug == Player._game_slug)", post_update=True)

    _last_president_id = db.Column(db.Integer, db.ForeignKey('player.id', use_alter=True))
    last_president = db.relationship("Player", foreign_keys=_last_president_id,
                                     primaryjoin="and_(Game._last_president_id == Player.id,"
                                                 "Game.slug == Player._game_slug)", post_update=True)

    _last_chancellor_id = db.Column(db.Integer, db.ForeignKey('player.id', use_alter=True))
    last_chancellor = db.relationship("Player", foreign_keys=_last_chancellor_id,
                                      primaryjoin="and_(Game._last_chancellor_id == Player.id,"
                                                  "Game.slug == Player._game_slug)", post_update=True)

    players = db.relationship('Player', back_populates="game", foreign_keys=Player._game_slug, order_by=Player.position,
                              cascade="all, delete")

    @validates("current_state")
    def validate_current_state(self, key, state):
        assert state in ["pre_game", "nomination", "election", "policies_president", "policies_chancellor", "post_game"]
        return state

    @validates("elected_policies")
    def validate_elected_policies(self, key, policies):
        assert all(policy in [0, 1] for policy in policies) and type(policies) is tuple
        return policies

    def __repr__(self):
        return self.slug

    def __str__(self):
        return self.slug

    def freeze_player_positions(self, scramble=False):
        r = list(range(len(self.players)))
        if scramble:
            shuffle(r)
        for i, player in enumerate(self.players):
            player.position = r[i]

    def everybody_voted(self):
        return all(player.get_vote() is not None for player in self.players)

    def evaluate_votes(self):
        assert self.everybody_voted()
        accepted = [player for player in self.players if player.get_vote()]
        rejected = [player for player in self.players if not player.get_vote()]
        return len(accepted) > len(rejected)

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

    def get_roles(self):
        if all(player.get_role() is None for player in self.players):
            num_liberals = len(self.players) // 2 + 1
            roles = ["liberal"] * num_liberals + ["fascist"] * (len(self.players) - 1 - num_liberals) + ["hitler"]
            for player in self.players:
                player.set_role(roles.pop())
        return {(player.id, player.name): player.get_role() for player in self.players}

    def get_hitler(self):
        for player in self.players:
            if player.get_role() == "hitler":
                return player
        raise RuntimeError("No Hitler in current game found!")

    def player_list(self):
        return [(player.id, player.name,) for player in self.players]


@event.listens_for(Game, 'before_update')
def receive_after_update(mapper, connection, target):
    target.last_active = datetime.utcnow()


@login.user_loader
def load_user(user_id):
    return Player.query.get(user_id)
