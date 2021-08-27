from flask import Flask, redirect, url_for, flash, render_template, request
from flask_limiter import Limiter
from flask_login import current_user, login_required, logout_user
from config import Config
from models import db, login_manager, OAuth, User, Schedule
from oauth import blueprint
from sqlalchemy import func
from cli import create_db
from datetime import datetime
import requests

app = Flask(__name__)
app.config.from_object(Config)
app.register_blueprint(blueprint, url_prefix="/login")
app.cli.add_command(create_db)
db.init_app(app)
limiter = Limiter(app, key_func=lambda: current_user.id)
login_manager.init_app(app)


@app.route("/")
def home():
    return render_template("home.html", user=current_user.is_authenticated)


@app.route("/view")
def view():
    if current_user.is_authenticated:
        schedule = current_user.schedule.get()

        if not all(schedule.values()):
            flash("You must upload your schedule to use ClassReveal.", "info")
            return redirect(url_for("edit"))

        classmates = {}

        for idx, (key, value) in enumerate(schedule.items(), start=1):
            records = (
                db.session.query(Schedule)
                .join(User)
                .filter(
                    func.lower(getattr(Schedule, key)) == func.lower(value),
                    User.district == current_user.district,
                )
                .all()
            )
            classmates[idx] = {
                value: (
                    sorted(
                        [record.user for record in records], key=lambda user: user.name
                    )
                )
            }


        return render_template("view.html", schedule=classmates)
    else:
        return redirect(url_for("home"))


@app.route("/logout")
def logout():
    if not current_user.is_authenticated:
        return redirect(url_for("home"))
    logout_user()
    return redirect(url_for("home"))


@app.route("/faq")
def faq():
    return render_template("faq.html")


@app.route("/edit", methods=["GET", "POST"])
@limiter.limit("8/hour")
def edit():
    if not current_user.is_authenticated:
        return redirect(url_for("home"))

    if request.method == "POST":
        for period, teacher in request.form.to_dict().items():
            setattr(current_user.schedule, period, teacher)
        db.session.commit()
        district = "WW-P" if current_user.district == 0 else "BR"
        PARAMS = {
            "username": "ClassRevealBot",
            "avatar_url": "https://classreveal.com/static/img/favicon.png",
            "content": f"{current_user.name} ({district}) submitted a schedule @ {datetime.today().strftime('%m-%d-%Y %H:%M:%S')}",
        }
        requests.post(url=app.config["DISCORD_WEBHOOK_URL"], data=PARAMS)
        return redirect(url_for("view"))

    if current_user.district == 0:
        flash(
            'Instructions: Enter teacher names corresponding to each period in your list schedule. If a class has more than one teacher, enter the name of the first/primary teacher. Do not enter lab periods. For study hall periods enter either "North - Study Hall" or "South - Study Hall". If your teacher isn\'t in the list, you can type it manually.',
            "info",
        )
    else:
        flash(
            'Instructions: Enter teacher names corresponding to each period in your schedule. If a class has more than one teacher, enter the name of the first/primary teacher. Do not enter lab periods. For lunch periods enter "Lunch".',
            "info",
        )

    return render_template("edit.html")


@app.route("/share/<provider_user_id>")
def share(provider_user_id):
    oauth = OAuth.query.filter_by(provider_user_id=provider_user_id).first_or_404()
    myschedule = []

    if current_user.is_authenticated:
        if current_user.schedule.get():
            myschedule = list(current_user.schedule.get().values())

    return render_template(
        "share.html", name=oauth.user.name, schedule=oauth.user.schedule.get(), myschedule=myschedule
    )


@app.errorhandler(404)
def page_not_found(e):
    return render_template("error.html", error="404 - Page not found."), 404


@app.errorhandler(429)
def too_many_requests(e):
    return render_template("error.html", error="429 - You have been rate limited."), 429


@app.errorhandler(500)
def internal_server_error(e):
    return (
        render_template("error.html", error="500 - Server Error. Please try again."),
        429,
    )
