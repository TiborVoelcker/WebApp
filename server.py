from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
import secrets, threading, json, os, string
from random import choice, shuffle, seed, choices, sample


TIMEOUT = 1000

seed(os.urandom(16))
app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_urlsafe(16)
# app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=5)

games = {}
doNotSend = ["Event", "roles"]


def make_roles(num):
    if num < 3:
        return [0] * num
    libs = int(num/2) + 1
    fascists = num - libs - 1
    temp = [0] * libs + [1] * fascists + [2]
    shuffle(temp)
    return temp


def make_id():
    alphanum = string.ascii_letters + string.digits
    return "".join(choices(alphanum, k=16))


def choose_policies(policies, enacted):
    try:
        chosen = sample(policies, k=3)
    except ValueError:
        policies = [1] * (11 - enacted.count(1)) + [0] * (6 - enacted.count(0))
        chosen = sample(policies, k=3)
    for k in chosen:
        policies.remove(k)
    return chosen


@app.route('/', methods=["GET", "POST"])
def home():
    if "username" in session:
        if "in-game" in session:
            return redirect(url_for("game", game_id=session["in-game"]))
        else:
            if request.method == "GET":
                return render_template("app.html")# return render_template('home.html', name=session["username"][0])
            if request.method == "POST":
                if "submit_game_id" in request.form:
                    game_id = request.form["game_id"]
                    if game_id in games.keys():
                        return redirect(url_for('game', game_id=game_id))
                    else:
                        flash("The game ID does not exist.")
                        return render_template("home.html", name=session["username"][0])
                elif "new_game" in request.form:
                    game_id = choice([i for i in range(0, 10000) if i not in games.keys()])
                    game_id = str(game_id).zfill(4)
                    games.update({game_id: {"is-started": False, "players": [["Dummy", "blub"]], "Event": threading.Event()}})
                    session["game_leader"] = True
                    return redirect(url_for('game', game_id=game_id))
    else:
        return redirect(url_for("login"))


@app.route('/login', methods=["POST", "GET"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    if request.method == "POST":
        if request.form["username"].isalnum() and len(request.form["username"]) <= 30:
            session['username'] = [request.form["username"], make_id()]
            # session.permanent = True
            return redirect(url_for("home"))
        else:
            flash("This username is not allowed.")
            return render_template("login.html")


@app.route("/logout")
def logout():
    [session.pop(key) for key in list(session.keys()) if key != '_flashes']
    return redirect(url_for("login"))


@app.route('/game/<string:game_id>', methods=["GET"])
def game(game_id):
    if not games[game_id]["is-started"]:
        if request.method == "GET":
            if "game_leader" in session:
                return render_template("lobby.html", game_leader=True, game_id=game_id, player=session["username"])
            else:
                return render_template("lobby.html", game_leader=False, game_id=game_id, player=session["username"])
    if games[game_id]["is-started"]:
        if session["username"] in games[game_id]["players"]:
            if "in-game" not in session:  # game just started
                session["in-game"] = game_id
            if request.method == "GET":
                return render_template("game.html", game_id=game_id, player=session["username"])
        else:
            return """Sorry, the game already started."""


@app.route('/set_event', methods=["POST"])
def set_event():
    if request.data:
        data = json.loads(request.data)
        print(data) # delete!
    else:
        return jsonify(success=False)
    game_entry = games[data["game_id"]]
    if "player_joined" in data:
        game_entry["players"].append(data["player_joined"])
    elif "player_left" in data:
        if game_entry["is-started"]:
            i = game_entry["players"].index(data["player_left"])
            game_entry["roles"].pop(i)
            session.pop("in-game")
        game_entry["players"].remove(data["player_left"])
    elif "game_started" in data:
        game_entry.update({"board": data["game_started"],
                           "roles": make_roles(len(game_entry["players"])),
                           "current_president": choice(range(len(game_entry["players"]))),
                           "current_chancellor": False,
                           "policies": [1] * 11 + [0] * 6,
                           "enacted_policies": []})
        game_entry["is-started"] = True
    elif "chancellor_chosen" in data:
        chancellor = int(data["chancellor_chosen"].strip("player"))
        if game_entry["players"][game_entry["current_president"]] == session["username"]\
                and chancellor != game_entry["current_president"]:
            game_entry.update({"current_chancellor": chancellor})
        else:
            return jsonify(success=False)
    elif "reload" in data:
        pass
    else:
        return jsonify(success=False)
    game_entry["Event"].set()
    return jsonify(success=True)


@app.route('/get_event', methods=["POST"])
def get_event():
    game_id = json.loads(request.data)["game_id"]
    if game_id in games:
        flag = games[game_id]["Event"].wait(timeout=TIMEOUT)
        if flag:
            games[game_id]["Event"].clear()
        data = {key: games[game_id][key] for key in games[game_id].keys() if key not in doNotSend}
        print(data) # delete!
        return jsonify(data)
    else:
        return redirect(url_for("home"))


@app.route('/secure', methods=["POST"])
def secure():
    data = json.loads(request.data)
    print(data) # delete!
    if data["game_id"] in games:
        game_entry = games[data["game_id"]]
        if "role_all" in data:
            if game_entry["roles"][game_entry["players"].index(session["username"])] == 1:
                return jsonify({"roles": game_entry["roles"]})
            else:
                return jsonify({"roles": [0] * len(game_entry["players"])})
        if "get_policies_president" in data:
            if session["username"] == game_entry["players"][game_entry["current_president"]]:
                chosen = choose_policies(game_entry["policies"], game_entry["enacted_policies"])
                return jsonify({"policies": chosen})
    else:
        return redirect(url_for("home"))


if __name__ == '__main__':
    app.run(debug=True)
