from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin
from flask_dance.consumer.storage.sqla import OAuthConsumerMixin

db = SQLAlchemy()


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(256), unique=True)
    name = db.Column(db.String(256))
    district = db.Column(db.Integer)
    schedule = db.relationship("Schedule", uselist=False)
    oauth = db.relationship("OAuth", uselist=False)


class Schedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
    user = db.relationship(User)

    period_1 = db.Column(db.String(256))
    period_2 = db.Column(db.String(256))
    period_3 = db.Column(db.String(256))
    period_4 = db.Column(db.String(256))
    period_5 = db.Column(db.String(256))
    period_6 = db.Column(db.String(256))
    period_7 = db.Column(db.String(256))
    period_8 = db.Column(db.String(256))
    period_9 = db.Column(db.String(256))

    def get(self):
        schedule = {
            key: str(value or "")
            for key, value in sorted(self.__dict__.items())
            if str(key).startswith("period")
        }

        if self.user.district == 0:
            schedule.pop("period_9")

        return schedule


class OAuth(OAuthConsumerMixin, db.Model):
    provider_user_id = db.Column(db.String(256), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey(User.id), nullable=False)
    user = db.relationship(User)


login_manager = LoginManager()
login_manager.login_view = "google.login"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
