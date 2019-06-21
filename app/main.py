import os
import json
from flask import Flask, flash, request, redirect, url_for, render_template
from werkzeug.utils import secure_filename
import google_auth
import database
import pdf

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "/tmp/uploads"
app.config['MAX_CONTENT_LENGTH'] = 4 * 1024 * 1024
app.secret_key = os.environ.get("FN_FLASK_SECRET_KEY", default=False)
app.register_blueprint(google_auth.app)

@app.route("/")
def home():
    if google_auth.is_logged_in():
        user_info = google_auth.get_user_info()

        if user_info["hd"] != "wwprsd.org":
            google_auth.logout()
            flash("You have to be a student at WW-P to use ClassReveal", "danger")
            return redirect(url_for("home"))
        
        return render_template("view.html", user_info=user_info)

    return render_template("home.html")

@app.route("/view/<int:user_id>")
def view(user_id):
    user = database.get_user(user_id)
    return str(user)
    

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() == "pdf"

@app.route("/upload", methods=["GET", "POST"])
def upload_file():
    if google_auth.is_logged_in():
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
