from app import db


class Game(db.Model):
    slug = db.Column(db.String(64), unique=True, nullable=False, index=True, primary_key=True)
    players = db.relationship('Player', backref='current_game', lazy=True)
    current_president = db.relationship('Player', backref='president_from', lazy=True, uselist=False)
    current_chancellor = db.relationship('Player', backref='chancellor_from', lazy=True, uselist=False)
    turn_no = db.Column(db.Integer, nullable=False, default=1)
    current_state = db.Column(db.String(16), nullable=False, default='pre_game')
    elected_policies = db.Column(db.PickleType(), nullable=False, default=list())
    _remaining_policies = db.Column(db.PickleType(), nullable=False,
                                    default=[1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])

    def __repr__(self):
        return f"Game {self.slug}"

    def return_public(self):
        return {key: self.__dict__[key] for key in self.__dict__ if not key.startswith("_")}


class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), index=True)
    game = db.Column(db.String(64), db.ForeignKey('game.slug'))
    _voted = db.Column(db.Boolean(), default=False)

    def __repr__(self):
        return f"User {self.name} (ID: {self.id})"