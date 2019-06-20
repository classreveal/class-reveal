import os
import json
from flask import Flask, flash, request, redirect, url_for, render_template
from werkzeug.utils import secure_filename
from flask_cors import CORS
from authlib.client import OAuth2Session
import google.oauth2.credentials
import googleapiclient.discovery
import google_auth

UPLOAD_FOLDER = "/tmp/uploads"
ALLOWED_EXTENSIONS = set(["pdf", "png", "jpg", "jpeg"])

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 4 * 1024 * 1024
app.secret_key = os.environ.get("FN_FLASK_SECRET_KEY", default=False)
app.register_blueprint(google_auth.app)
CORS(app)

@app.route("/")
def index():
    if google_auth.is_logged_in():
        user_info = google_auth.get_user_info()

        if user_info["hd"] != "wwprsd.org":
            google_auth.logout()
            return "You have to be a student at WW-P to use ClassReveal"
        
        return "<pre>" + json.dumps(user_info, indent=4) + "</pre>"

    return render_template("home.html")

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/upload", methods=["GET", "POST"])
def upload_file():
    if google_auth.is_logged_in():
        if request.method == "POST":
            if "file" not in request.files:
                flash("No file part")
                return redirect(request.url)
            file = request.files["file"]
            if file.filename == "":
                flash("No selected file")
                return redirect(request.url)
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
                return redirect(url_for("uploaded_file", filename=filename))
    return '''
    <!doctype html>
    <title>Upload Schedule</title>
    <h1>Upload Schedule</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file>
      <input type=submit value=Upload>
    </form>
    '''

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
