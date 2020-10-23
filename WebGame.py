from app import app, db
from app.models import Game, Player

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'Game': Game, 'Player': Player}