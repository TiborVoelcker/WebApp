from datetime import datetime

from app import db
from app import scheduler
from app.models import Game


@scheduler.task('cron', hour='8-16/4, 16-22/2')
def housekeeping():
    with scheduler.app.app_context():
        now = datetime.utcnow()
        inactive_time_elapsed = scheduler.app.config["INACTIVE_TIME_DELAY"]
        games = Game.query.filter(Game.last_active < now - inactive_time_elapsed).delete()
        db.session.commit()
        if games:
            scheduler.app.logger.info(f"Deleted {games} inactive game{('', 's')[games > 1]}.")
