from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(max=32)])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class GameForm(FlaskForm):
    game_slug = StringField('Game ID', validators=[DataRequired()])
    submit = SubmitField('Join')
    new_game = SubmitField('New Game')