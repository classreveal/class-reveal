from flask import Flask, redirect, url_for, flash, render_template, request
from flask_limiter import Limiter
from flask_login import current_user, login_required, logout_user
from config import Config
from models import db, login_manager, OAuth, User, Schedule
from oauth import blueprint
from cli import create_db
from werkzeug.exceptions import HTTPException
import os
from datetime import datetime
import requests

app = Flask(__name__)
app.config.from_object(Config)
app.register_blueprint(blueprint, url_prefix="/login")
app.cli.add_command(create_db)
db.init_app(app)
limiter = Limiter(app, key_func=lambda: current_user.id)
login_manager.init_app(app)
WEBHOOK = os.environ.get("WEBHOOK")


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
                    getattr(Schedule, key) == value,
                    User.district == current_user.district,
                )
                .all()
            )
            zipped = list(zip([record.user.name for record in records], [record.user.virtual for record in records]))
            classmates[idx] = {value: zipped}
        return render_template(
            "view.html", name=current_user.name, schedule=classmates, user=current_user.is_authenticated
        )
    else:
        return redirect(url_for("home"))



@app.route("/logout")
def logout():
    if not current_user.is_authenticated:
        return redirect(url_for("home"))
    logout_user()
    return redirect(url_for("home"))


@app.route('/faq')
def faq():
    return render_template("faq.html", user=current_user.is_authenticated)


@app.route("/edit", methods=["GET", "POST"])
@limiter.limit("4/hour", methods=["POST"])
def edit():
    if not current_user.is_authenticated:
        return redirect(url_for("home"))
    if request.method == "POST":
        for period, teacher in request.form.to_dict().items():
            if period == "virtual":
                setattr(current_user, "virtual", int(0 if int(teacher) == 0 else 1))
                continue
            setattr(current_user.schedule, period, teacher)
        db.session.commit()
        district = ("WW-P" if current_user.district == 0 else "BR")
        PARAMS = {'username': "ClassRevealBot", "avatar_url": "https://classreveal.com/static/img/favicon.png",
                  "content": f"{current_user.name} ({district}) submitted a schedule @ {datetime.now()}"}
        requests.post(url=WEBHOOK, data=PARAMS)
        return redirect(url_for("view"))
    districtjson = "json/wwp.json" if current_user.district == 0 else "json/br.json"
    return render_template("edit.html", schedule=current_user.schedule.get(), districtjson=districtjson, user=current_user.is_authenticated, virtual=current_user.virtual)


@app.errorhandler(Exception)
def handle_exception(e):
    if e.code == 404:
        message = "4owo4 - Huh couldn't find that page."
    elif e.code == 429:
        message = "429 - It appears you have submitted too many requests."
    else:
        message = f"{e.code} - A server error occured. Please try again."
    return render_template("error.html", error=message, user=current_user.is_authenticated)
