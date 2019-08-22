import os, json
from flask import Flask, flash, session, request, redirect, url_for, render_template
from werkzeug.utils import secure_filename
from flask_dance.contrib.google import make_google_blueprint, google

import database, pdf

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "/tmp/uploads"
app.config['MAX_CONTENT_LENGTH'] = 4 * 1024 * 1024
app.secret_key = os.environ.get("FLASK_SECRET_KEY")
app.config["GOOGLE_OAUTH_CLIENT_ID"] = os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
app.config["GOOGLE_OAUTH_CLIENT_SECRET"] = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET")
google_bp = make_google_blueprint(scope=["profile", "email"])
app.register_blueprint(google_bp, url_prefix="/login")

@app.route("/")
def home():
    if not google.authorized:
        return render_template("home.html")

    user_info = google.get("/oauth2/v1/userinfo").json()

    if user_info["hd"] != "wwprsd.org":
        logout()
        flash("You have to be a student at WW-P to use ClassReveal", "danger")
        return redirect(url_for("home"))

    user = database.get_user(user_info["id"])

    if not user:
        flash("You must upload your schedule to use ClassReveal.", "info")
        return redirect(url_for("edit_schedule"))

    classmates = []

    for i in range(8):
        course = database.get_class(i, user["schedule"][str(i)]["teacher_name"])
        for classmate in course:
            classmates.append(classmate["name"])
        i += 1

    return render_template("view.html", name=user_info["name"], user_id=user_info["id"], schedule=user["schedule"], classmates=classmates)

@app.route("/logout")
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
def edit_schedule():
    if not google.authorized:
        return redirect(url_for("home"))

    user_info = google.get("/oauth2/v1/userinfo").json()

    if request.method == "POST":
        schedule = {}

        for i in range(1, 9):
            schedule[str(i)] = {"teacher_name": f"{request.form.get('t' + str(i))}"}

        database.add_user(user_info["id"], user_info["name"], schedule)

    user = database.get_user(user_info["id"])
    schedule = user["schedule"] if user else ""

    return render_template("edit.html", schedule=schedule)

@app.route("/upload", methods=["GET", "POST"])
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
            database.add_user(user_info["id"], user_info["name"], schedule)
            return redirect(url_for("home"))
        except Exception as e:
            flash("Something went wrong", "danger")
            return redirect(url_for("upload_schedule"))

    return render_template("upload.html")

@app.route("/admin", methods=["GET"])
def edit_schedule():
    if not google.authorized:
        return redirect(url_for("home"))
    user_info = google.get("/oauth2/v1/userinfo").json()

    users = database.get_users(request.args.offset, request.args.num)

    # didnt design the ui for admin
    return render_template("edit.html", schedule=schedule)
 

if __name__ == "__main__":
    app.run(debug=True)
