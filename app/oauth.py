from flask import flash
from flask_login import current_user, login_user
from flask_dance.contrib.google import make_google_blueprint
from flask_dance.consumer import oauth_authorized, oauth_error
from flask_dance.consumer.storage.sqla import SQLAlchemyStorage
from sqlalchemy.orm.exc import NoResultFound
from models import db, User, OAuth, Schedule


blueprint = make_google_blueprint(
    scope=["profile", "email"],
    storage=SQLAlchemyStorage(OAuth, db.session, user=current_user),
    reprompt_select_account=True,
    hosted_domain="wwprsd.org"
)


@oauth_authorized.connect_via(blueprint)
def google_logged_in(blueprint, token):
    if not token:
        flash("Failed to log in.", category="error")
        return False

    resp = blueprint.session.get("/oauth2/v1/userinfo")
    if not resp.ok:
        msg = "Failed to fetch user info."
        flash(msg, category="error")
        return False

    info = resp.json()

    if "hd" not in info or info["hd"] != "wwprsd.org":
        flash("Failed to validate hosted domain.", category="error")
        return False

    query = OAuth.query.filter_by(provider=blueprint.name, provider_user_id=info["id"])
    try:
        oauth = query.one()
    except NoResultFound:
        oauth = OAuth(provider=blueprint.name, provider_user_id=info["id"], token=token)

    if oauth.user:
        login_user(oauth.user)
    else:
        user = User(email=info["email"], name=info["name"])
        schedule = Schedule(user=user)
        oauth.user = user

        db.session.add_all([user, schedule, oauth])
        db.session.commit()

        login_user(user)

    return False


@oauth_error.connect_via(blueprint)
def google_error(blueprint, message, response):
    msg = f"OAuth error from {blueprint.name}! message={message} response={response}"
    flash(msg, category="error")
