from flask import Flask, request, render_template, make_response, redirect
import redis
from flask_cors import CORS
import string
import random
from datetime import datetime
import collections
import json
import hashlib
import os

def getID(length=5):
    return "".join([random.choice(string.ascii_lowercase+string.digits) for _ in range(0, length)])

def getkey(base, key):
    if type(base) == bytes:
        base = base.decode("utf-8")
    if type(key) == bytes:
        key = key.decode("utf-8")
    return "%s:%s" % (base, key)


def check_admin():
    return request.cookies.get("secret") == ADMIN_SECRET or (
                    request.method == "POST" and request.form["password"] == ADMIN_PASSWORD
                )

ADMIN_PASSWORD = os.environ["ADMIN_PASSWORD"]
ADMIN_SECRET = hashlib.sha256(ADMIN_PASSWORD.encode("utf-8")).hexdigest()
DEFAULT_REDIRECT_URL = os.environ["DEFAULT_REDIRECT_URL"]
DEFAULT_USE_JS = bool(int(os.environ["DEFAULT_USE_JS"]))
IGNORE_FAVICON = bool(int(os.environ["IGNORE_FAVICON"]))
REDIS_HOST = os.environ["REDIS_HOST"]
REDIS_PORT = int(os.environ["REDIS_PORT"])


app = Flask(__name__)
CORS(app)
db = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)


@app.route("/admin", methods=["GET", "POST"])
def admin():
    if not check_admin():
        return render_template("login.html")
    
    if request.method == "POST" and "path" in request.form:
            redirects = db.get("redirects")
            if redirects is not None:
                redirects = json.loads(redirects)
            else:
                redirects = []
            redirects.append(dict(
                path=request.form["path"],
                url=request.form["url"],
                js="js" in request.form
            ))
            db.set("redirects", json.dumps(redirects))

    logs = []
    for id in db.lrange("logs", 0, -1):
        elem = db.get(getkey("log", id))
        if elem is not None:
            elem = json.loads(elem)
            elem["id"] = id.decode("utf-8")
            logs.append(elem)

    redirects = db.get("redirects")
    if redirects is not None:
        redirects = json.loads(redirects)
    else:
        redirects = []
    redirects.append(dict(
        path="*",
        url=DEFAULT_REDIRECT_URL,
        js=DEFAULT_USE_JS
    ))
    resp = make_response(render_template("admin.html", logs=logs, redirects=redirects))
    resp.set_cookie("secret", ADMIN_SECRET)

    return resp

@app.route("/clear/<elem>")
def clear(elem):
    if not check_admin():
        return render_template("login.html")
    
    if elem == "logs":
        for key in db.scan_iter("log:*"):
            db.delete(key)
        db.delete("logs")
    if elem == "redirects":
        db.delete("redirects")

    return redirect("/admin", code=302)

@app.route("/view/<id>", methods=["GET"])
def view(id):
    if not check_admin():
        return redirect("/admin", code=302)
    elem = db.get(getkey("log", id)) 
    if elem is not None:
        elem = json.loads(elem)
        return render_template("view.html", id=id, information=json.dumps(elem, indent=4))
    return ""


@app.errorhandler(404)
def track(e):
    if IGNORE_FAVICON and request.path == "/favicon.ico":
        return ""
    if request.method == "POST":
        if "id" in request.json and "info" in request.json:
            id = request.json["id"]
            info = json.loads(db.get(getkey("log", id)))
            for k, v in request.json["info"].items():
                # Write only if field do not exists to avoid erasing
                if k not in info: info[k] = v
            db.set(getkey("log", id), json.dumps(info))
        return "", 200
    else:
        id = getID()

        if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
            ip = request.environ['REMOTE_ADDR']
        else:
            ip = request.environ['HTTP_X_FORWARDED_FOR']
        
        info = json.dumps(dict(
            date=datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            path=request.path,
            ip=ip,
            headers=str(request.headers)
        ))
        
        db.set(getkey("log", id), info)
        db.lpush("logs", id)

        use_js = DEFAULT_USE_JS
        redirect_url = DEFAULT_REDIRECT_URL

        redirects = db.get("redirects")
        if redirects is not None:
            redirects = json.loads(redirects)
            for elem in redirects:
                if request.path == elem["path"]:
                    use_js = elem["js"]
                    redirect_url = elem["url"]
        
        if use_js:
            return render_template("track.html", id=id, redirect_url=redirect_url)
        else:
            return redirect(redirect_url, code=302)