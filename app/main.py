import os
import json
from flask import Flask, flash, session, request, redirect, url_for, render_template
from functools import wraps
from werkzeug.utils import secure_filename
from flask_dance.contrib.google import make_google_blueprint, google

import database
import pdf

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
    if user == None:
        hits = 0
    else:
        hits = user['hits']

    if request.method == "POST":
        if hits < 8:
            schedule = {}
            for i in range(8):
                schedule[str(i)] = {
                    "teacher_name": f"{request.form.get('t' + str(i))}"}
            database.add_user(
                user_info["id"], user_info["name"], hits+1, schedule)
        else:
            flash("Your account has been rate limited.", "danger")
    user = database.get_user(user_info["id"])
    schedule = user["schedule"] if user else ""

    return render_template("edit.html", schedule=schedule)


@app.route("/upload", methods=["GET", "POST"])
@catch_and_log_out
def upload_schedule():
    if not google.authorized:
        return redirect(url_for("home"))

    if request.method == "POST":
        if "file" not in request.files:
            flash("No file part", "danger")
            return redirect(url_for("upload_schedule"))

        file = request.files["file"]

        if file.filename == "":
            flash("No selected file", "danger")
            return redirect(url_for("upload_schedule"))

        if not (allowed_file(file.filename)):
            flash("Only PDF files are allowed", "danger")
            return redirect(url_for("upload_schedule"))

        try:
            text = pdf.read_pdf(file)
            schedule = pdf.parse_pdf(text)

            if not schedule:
                flash("Something went wrong", "danger")
                return redirect(url_for("upload_schedule"))

            user_info = google.get("/oauth2/v1/userinfo").json()
            user = database.get_user(user_info["id"])
            if user == None:
                hits = 0
            else:
                hits = user['hits']
            
            if hits < 8:
                database.add_user(user_info["id"], user_info["name"], hits+1, schedule)
            else:
                flash("Your account has been rate limited.", "danger")

            return redirect(url_for("home"))
        except Exception as e:
            flash("Something went wrong", "danger")
            return redirect(url_for("upload_schedule"))

    return render_template("upload.html")


@app.route("/faq")
def faq():
    user_login = True
    if not google.authorized:
        user_login = False
    return render_template("faq.html",  user_login=user_login)


if __name__ == "__main__":
    app.run(debug=True)
