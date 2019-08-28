import os
import json
from flask import Flask, flash, session, request, redirect, url_for, render_template
from functools import wraps
from werkzeug.utils import secure_filename
from flask_dance.contrib.google import make_google_blueprint, google
from datetime import datetime
import time
import database
import pdf
import pymongo
import requests

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "/tmp/uploads"
app.config['MAX_CONTENT_LENGTH'] = 4 * 1024 * 1024
app.secret_key = os.environ.get("FLASK_SECRET_KEY")
app.config["GOOGLE_OAUTH_CLIENT_ID"] = os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
app.config["GOOGLE_OAUTH_CLIENT_SECRET"] = os.environ.get(
    "GOOGLE_OAUTH_CLIENT_SECRET")
google_bp = make_google_blueprint(
    scope=["https://www.googleapis.com/auth/userinfo.email", "https://www.googleapis.com/auth/userinfo.profile", "openid"])
app.register_blueprint(google_bp, url_prefix="/login")
RATE_TIME = os.environ.get("RATE_TIME")
RATE_NUM = os.environ.get("RATE_NUM")
WEBHOOK = os.environ.get("WEBHOOK")

def catch_and_log_out(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"Exception: {e}")
            del google_bp.token
            session.clear()
            return redirect(url_for("home"))
    return decorated_function


@app.route("/")
@catch_and_log_out
def home():
    if not google.authorized:
        return render_template("home.html")

    user_info = google.get("/oauth2/v1/userinfo").json()

    try:
        if user_info["hd"] != "wwprsd.org":
            logout()
            flash("You have to be a student at WW-P to use ClassReveal", "danger")
            return redirect(url_for("home"))
    except:
        logout()
        flash("You have to be a student at WW-P to use ClassReveal", "danger")
        return redirect(url_for("home"))

    user = database.get_user(user_info["id"])

    if not user:
        flash("You must upload your schedule to use ClassReveal.", "info")
        return redirect(url_for("edit_schedule"))

    schedule = user["schedule"]
    flash("We hope you like Class Reveal. You can help improve it by sharing it. More shares eqauates to a more thorough roster for everyone. It's science!", "success")

    for i in range(8):
        classmates = []
        course = database.get_class(i, schedule[str(i)]["teacher_name"])

        for classmate in course:
            classmates.append(classmate["name"])

        schedule[str(i)]["classmates"] = classmates

    return render_template("view.html", name=user_info["name"], user_id=user_info["id"], schedule=schedule)


@app.route("/logout")
@catch_and_log_out
def logout():
    token = google_bp.token["access_token"]
    resp = google.post(
        "https://accounts.google.com/o/oauth2/revoke",
        params={"token": token},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )

    del google_bp.token
    session.clear()
    return redirect(url_for("home"))


@app.route("/view/<int:user_id>")
@catch_and_log_out
def view(user_id):
    if not user_id:
        return url_for("home")

    user = database.get_user(user_id)
    if not user:
        return url_for("home")

    return render_template("view.html", name=user["name"], user_id=None, schedule=user["schedule"])


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() == "pdf"


@app.route("/edit", methods=["GET", "POST"])
@catch_and_log_out
def edit_schedule():
    if not google.authorized:
        return redirect(url_for("home"))

    user_info = google.get("/oauth2/v1/userinfo").json()
    user = database.get_user(user_info["id"])

    try:
        if int(user_info['email'][:2]) + 2000 > int(datetime.now().year) + 4:
            flash("Middle school students are restricted to the manual entry option. Fill in your schedule with all periods (offteam and team) with the exception of Flex and lunch.", "warning")
    except:
        pass

    if user == None:
        hits = 0
    else:
        last = int(user['_id'].generation_time.timestamp())
        now = int(time.time())
        if now-last > int(RATE_TIME):
            hits = 0
        else:
            hits = user['hits']

    if request.method == "POST":
        if hits < int(RATE_NUM):
            schedule = {}
            for i in range(8):
                schedule[str(i)] = {
                    "teacher_name": f"{request.form.get('t' + str(i))}"}
            if user == None:
                PARAMS = {'username': "ClassRevealBot", "avatar_url": "https://classreveal.com/static/img/favicon.png",
                          "content": user_info['name'] + " (" + str(13-(int(user_info['email'][:2])-int(datetime.now().year-2000))) + "th grade) joined Class Reveal @ " + str(datetime.now())}
                requests.post(
                    url=WEBHOOK, data=PARAMS)

            database.add_user(
                user_info["id"], user_info["name"], hits+1, schedule)
        else:
            flash("Your account has been rate limited.", "danger")
        return redirect(url_for("home"))
    user = database.get_user(user_info["id"])
    schedule = user["schedule"] if user else ""

    return render_template("edit.html", schedule=schedule, user_id=True)

@app.route("/faq")
def faq():
    user_id = True
    if not google.authorized:
        user_id = False
    return render_template("faq.html",  user_id=user_id)


@app.errorhandler(404)
def page_not_found(e):
    flash("404 - If only that page existed... 🤔", "warning")
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)

