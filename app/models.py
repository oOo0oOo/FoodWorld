from datetime import datetime

from . import db


class User(db.Model):
    __tablename__ = 'users'
    # The userid assigned by amazon
    user_id = db.Column(db.String(512), unique=True, primary_key=True)

    # The state machine (so we can pick up exactly where we left off)
    # A cheap pickle type for now
    state_machine = db.Column(db.PickleType)

    # Some stats
    joined = db.Column(db.DateTime, unique=False)
    last_online = db.Column(db.DateTime, unique=False)

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)

        self.joined = datetime.now()
        self.update_online()

    def update_online(self):
        self.last_online = datetime.now()