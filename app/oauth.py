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
)


@oauth_authorized.connect_via(blueprint)
def google_logged_in(blueprint, token):
    if not token:
        flash("Failed to log in.", category="danger")
        return False

    resp = blueprint.session.get("/oauth2/v1/userinfo")
    if not resp.ok:
        flash("Failed to fetch user info.", category="danger")
        return False

    info = resp.json()

    if (
        "hd" not in info
        or info["hd"] != "wwprsd.org"
        and info["hd"] != "gapps.brrsd.k12.nj.us"
    ):
        flash("You must sign in with your school email.", category="danger")
        return False

    query = OAuth.query.filter_by(provider=blueprint.name, provider_user_id=info["id"])
    try:
        oauth = query.one()
    except NoResultFound:
        oauth = OAuth(provider=blueprint.name, provider_user_id=info["id"], token=token)

    if oauth.user:
        login_user(oauth.user)
    else:
        district = 0 if info["hd"] == "wwprsd.org" else 1
        user = User(email=info["email"], name=info["name"], district=district)
        schedule = Schedule(user=user)
        oauth.user = user

        db.session.add_all([user, schedule, oauth])
        db.session.commit()

        login_user(user)

    return False


@oauth_error.connect_via(blueprint)
def google_error(blueprint, message, response):
    flash(
        f"OAuth error from {blueprint.name}! message={message} response={response}",
        category="danger",
    )
