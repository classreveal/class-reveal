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

    return render_template("view.html", user_info=user_info)

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
    user = database.get_user(user_id)
    return str(user)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() == "pdf"

@app.route("/upload", methods=["GET", "POST"])
def upload_file():
    if google.authorized:
        if request.method == "POST":
            if "file" not in request.files:
                flash("No file part", "danger")
                return redirect(request.url)

            file = request.files["file"]

            if file.filename == "":
                flash("No selected file", "danger")
                return redirect(request.url)

            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                text = pdf.read_pdf(file)
                return redirect(url_for("home"))

        return render_template("upload.html")
    else:
        return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
