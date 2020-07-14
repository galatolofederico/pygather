from flask import Flask, request, render_template, make_response, redirect
from flask_cors import CORS
import string
import random
from datetime import datetime
import collections
import json

## Configuration ##

ADMIN_PASSWORD = "admin"
DEFAULT_REDIRECT_URL = "https://google.com"
DEFAULT_USE_JS = True
IGNORE_FAVICON = True

###################

def getID(length=5):
    return "".join([random.choice(string.ascii_lowercase+string.digits) for _ in range(0, length)])

app = Flask(__name__)
CORS(app)

db = collections.OrderedDict()

redirects = collections.OrderedDict()
redirects["*"] = dict(
    url=DEFAULT_REDIRECT_URL,
    js=DEFAULT_USE_JS
)

admin_secret = getID(20)


@app.route("/admin", methods=["GET", "POST"])
def admin():
    logged_in = request.cookies.get("secret") == admin_secret or (
                    request.method == "POST" and request.form["password"] == ADMIN_PASSWORD
                )
    
    if request.method == "POST" and "path" in request.form:
            redirects[request.form["path"]] = dict(
                url=request.form["url"],
                js="js" in request.form
            )

    if logged_in:
        resp = make_response(render_template("admin.html", db=reversed(list(db.items())), redirects=redirects.items()))
    else:
        resp = make_response(render_template("login.html"))
    
    if request.method == "POST" and "password" in request.form:
        if request.form["password"] == ADMIN_PASSWORD:
            resp.set_cookie("secret", admin_secret)

    return resp


@app.route("/view/<id>", methods=["GET"])
def view(id):
    logged_in = request.cookies.get("secret") == admin_secret or (
                request.method == "POST" and request.form["password"] == ADMIN_PASSWORD
            )
    if not logged_in:
        return redirect("/admin", code=302)
    if id in db:
        return render_template("view.html", id=id, information=json.dumps(db[id], indent=4))
    return ""

@app.errorhandler(404)
def track(e):
    if IGNORE_FAVICON and request.path == "/favicon.ico":
        return ""
    if request.method == "POST":
        if "id" in request.json and "info" in request.json:
            id = request.json["id"]
            for k, v in request.json["info"].items():
                # Write only if field do not exists to avoid erasing
                if k not in db[id]: db[id][k] = v
        return "", 200
    else:
        id = getID()

        if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
            ip = request.environ['REMOTE_ADDR']
        else:
            ip = request.environ['HTTP_X_FORWARDED_FOR']
        
        db[id] = dict(
            date=datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            path=request.path,
            ip=ip,
            headers=str(request.headers)
        )

        elem = redirects["*"]
        if request.path in redirects: elem = redirects[request.path]

        if elem["js"]:
            return render_template("track.html", id=id, redirect_url=elem["url"])
        else:
            return redirect(elem["url"], code=302)