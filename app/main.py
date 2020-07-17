from flask import Flask, redirect, url_for, flash, render_template, request
from flask_limiter import Limiter
from flask_login import current_user, login_required, logout_user
from config import Config
from models import db, login_manager, OAuth, User, Schedule
from oauth import blueprint
from cli import create_db


app = Flask(__name__)
app.config.from_object(Config)
app.register_blueprint(blueprint, url_prefix="/login")
app.cli.add_command(create_db)
db.init_app(app)
limiter = Limiter(app, key_func=lambda: current_user.id)
login_manager.init_app(app)


@app.route("/")
def home():
    if current_user.is_authenticated:
        schedule = current_user.schedule.get()

        if not all(schedule.values()):
            flash("You must upload your schedule to use ClassReveal.", "info")
            return redirect(url_for("edit"))

        classmates = {}

        for idx, (key, value) in enumerate(schedule.items(), start=1):
            records = (
                db.session.query(Schedule).filter(getattr(Schedule, key) == value).all()
            )
            classmates[idx] = {value: [record.user.name for record in records]}

        return render_template(
            "view.html",
            name=current_user.name,
            schedule=classmates,
            provider_user_id=current_user.oauth.provider_user_id,
        )
    else:
        return render_template("home.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))


@app.route("/edit", methods=["GET", "POST"])
@limiter.limit("10 per hour", methods=["POST"])
@login_required
def edit():
    if request.method == "POST":
        for period, teacher in request.form.to_dict().items():
            setattr(current_user.schedule, period, teacher)
        db.session.commit()

        return redirect(url_for("home"))

    return render_template("edit.html", schedule=current_user.schedule.get())


@app.route("/share/<provider_user_id>")
def share(provider_user_id):
    oauth = OAuth.query.filter_by(provider_user_id=provider_user_id).first_or_404()

    return render_template(
        "share.html", name=oauth.user.name, schedule=oauth.user.schedule.get()
    )
