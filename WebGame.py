from app import app, db, socketio
from app.models import Game, Player


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'Game': Game, 'Player': Player}


if __name__ == '__main__':
    socketio.run(app, log_output=False)