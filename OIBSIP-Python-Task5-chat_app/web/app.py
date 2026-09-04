"""
app.py
Advanced-tier chat app: Flask + Flask-SocketIO web GUI (instead of
tkinter), with username/password auth, multiple rooms, SQLite-backed
message history, emoji shortcode rendering, and desktop notifications
for messages received while the tab isn't focused (handled client-side
in static/chat.js).

Run:
    python app.py
Then open http://127.0.0.1:5000 in two different browser windows (or
one normal + one private/incognito window) to chat between two users.
"""

import os
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_socketio import SocketIO, join_room, leave_room, emit
from werkzeug.security import generate_password_hash, check_password_hash

import database as db
from emoji_map import render_emoji

app = Flask(__name__)
app.secret_key = os.environ.get("CHAT_SECRET_KEY", "dev-secret-key-change-me")
socketio = SocketIO(app, async_mode="threading")

MAX_MESSAGE_LENGTH = 1000

try:
    db.init_db()
except db.DatabaseError as e:
    print(f"FATAL: could not initialise database: {e}")

# sid -> {"username": ..., "room": ...}, used to announce departures and
# for the browser-tab-focus based desktop notification feature.
active_connections = {}


def current_username():
    return session.get("username")


def login_required_redirect():
    if not current_username():
        flash("Please log in first.", "error")
        return redirect(url_for("login"))
    return None


# ---------------------------------------------------------------- routes

@app.route("/")
def home():
    if current_username():
        return redirect(url_for("rooms"))
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if not username or not password:
            flash("Username and password are required.", "error")
        elif password != confirm:
            flash("Passwords do not match.", "error")
        elif len(password) < 6:
            flash("Password must be at least 6 characters.", "error")
        else:
            try:
                password_hash = generate_password_hash(password)
                db.create_user(username, password_hash)
                flash("Account created. Please log in.", "success")
                return redirect(url_for("login"))
            except db.DatabaseError as e:
                flash(str(e), "error")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        try:
            user = db.get_user_by_username(username)
        except db.DatabaseError as e:
            flash(f"Login failed: {e}", "error")
            user = None

        if user and check_password_hash(user["password_hash"], password):
            session["username"] = user["username"]
            return redirect(url_for("rooms"))
        elif user is not None or username:
            flash("Invalid username or password.", "error")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("login"))


@app.route("/rooms", methods=["GET", "POST"])
def rooms():
    redirect_resp = login_required_redirect()
    if redirect_resp:
        return redirect_resp

    if request.method == "POST":
        room_name = request.form.get("room_name", "").strip()
        if not room_name:
            flash("Room name cannot be empty.", "error")
        else:
            try:
                db.create_room(room_name, current_username())
                flash(f"Room '{room_name}' created.", "success")
                return redirect(url_for("chat", room_name=room_name))
            except db.DatabaseError as e:
                flash(str(e), "error")

    try:
        room_list = db.list_rooms()
        db_error = None
    except db.DatabaseError as e:
        room_list = []
        db_error = str(e)

    return render_template("rooms.html", rooms=room_list, db_error=db_error, username=current_username())


@app.route("/chat/<room_name>")
def chat(room_name):
    redirect_resp = login_required_redirect()
    if redirect_resp:
        return redirect_resp

    try:
        room = db.get_room_by_name(room_name)
    except db.DatabaseError as e:
        flash(f"Could not load room: {e}", "error")
        return redirect(url_for("rooms"))

    if not room:
        flash(f"Room '{room_name}' does not exist.", "error")
        return redirect(url_for("rooms"))

    return render_template("chat.html", room_name=room_name, username=current_username())


# ---------------------------------------------------------------- sockets

@socketio.on("join")
def on_join(data):
    username = current_username()
    room_name = (data or {}).get("room", "").strip()
    if not username or not room_name:
        return

    try:
        room = db.get_room_by_name(room_name)
    except db.DatabaseError as e:
        emit("system_error", {"message": f"Could not join room: {e}"})
        return

    if not room:
        emit("system_error", {"message": f"Room '{room_name}' does not exist."})
        return

    join_room(room_name)
    active_connections[request.sid] = {"username": username, "room": room_name}

    try:
        history = db.get_recent_messages(room["id"], limit=50)
    except db.DatabaseError as e:
        history = []
        emit("system_error", {"message": f"Could not load message history: {e}"})

    emit("history", {"messages": history})
    emit(
        "system_message",
        {"text": f"{username} joined the room.", "time": datetime.now().strftime("%H:%M")},
        to=room_name,
        include_self=False,
    )


@socketio.on("send_message")
def on_send_message(data):
    username = current_username()
    room_name = (data or {}).get("room", "").strip()
    text = (data or {}).get("message", "")

    if not username or not room_name or not text.strip():
        return

    text = text.strip()[:MAX_MESSAGE_LENGTH]
    text = render_emoji(text)

    try:
        room = db.get_room_by_name(room_name)
        if not room:
            emit("system_error", {"message": "Room no longer exists."})
            return
        db.add_message(room["id"], username, text)
    except db.DatabaseError as e:
        emit("system_error", {"message": f"Message could not be saved: {e}"})
        return

    payload = {
        "username": username,
        "content": text,
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }
    emit("new_message", payload, to=room_name)


@socketio.on("disconnect")
def on_disconnect():
    info = active_connections.pop(request.sid, None)
    if info:
        emit(
            "system_message",
            {"text": f"{info['username']} left the room.", "time": datetime.now().strftime("%H:%M")},
            to=info["room"],
        )


if __name__ == "__main__":
    socketio.run(app, debug=True)
