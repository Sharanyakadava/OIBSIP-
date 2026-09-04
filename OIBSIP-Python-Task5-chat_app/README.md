# Chat Application

Two separate implementations in this folder:

- **`cli/`** — Beginner tier: a two-user (extendable to more) command-line
  chat using raw TCP sockets and `threading`. No external dependencies.
- **`web/`** — Advanced tier: a full web GUI built with **Flask +
  Flask-SocketIO** (used *instead of tkinter*), with login/registration,
  multiple rooms, SQLite-backed message history, emoji shortcodes, and
  desktop notifications for messages received while the tab isn't
  focused.

---

## Beginner tier (CLI) — `cli/`

```bash
cd cli
python server.py
```

Then, in two more terminals:
```bash
python client.py
python client.py
```

Each client asks for a username, then you can type messages back and
forth. Messages are shown with a `[HH:MM] Username: text` prefix. Type
`/quit` to leave — the other client will see a "has disconnected"
notice. Everything runs on `localhost:5555`.

---

## Advanced tier (Web GUI) — `web/`

### Setup

```bash
cd web
pip install -r requirements.txt
python app.py
```

Open **http://127.0.0.1:5000** in two different browser windows (e.g.
one normal + one private/incognito window, or two different browsers)
to simulate two users chatting.

### What you can do

1. **Register** an account (username + password, min. 6 characters).
2. **Log in.**
3. On the **Rooms** page, join the default `general` room or create a
   new one.
4. In a room, past messages (last 50) load automatically, then new
   messages appear in real time via Socket.IO.
5. Try emoji shortcodes like `:smile:`, `:fire:`, `:tada:`, `:thumbsup:`
   — they're rendered as Unicode emoji for everyone in the room.
6. Switch to a different browser tab/app — if a new message arrives
   while the chat tab isn't focused, you'll get a desktop notification
   (the browser will ask for notification permission the first time).

### Project structure

```
web/
├── app.py            # Flask + Flask-SocketIO app: routes + real-time events
├── database.py         # SQLite: users, rooms, messages
├── emoji_map.py         # :shortcode: -> emoji rendering
├── requirements.txt
├── data/
│   └── chat.db          # created automatically on first run
├── templates/
│   ├── base.html, login.html, register.html, rooms.html, chat.html
└── static/
    ├── style.css
    └── chat.js           # Socket.IO client logic + notifications
```

---

## Security & Privacy — please read before using this for anything real

This project is a learning/demo app, not a production-secure messenger.
Specifically:

- **Passwords** are hashed with Werkzeug's `generate_password_hash`
  (PBKDF2-based) before being stored in SQLite — the plain password is
  never saved. This part is reasonably safe.
- **Messages are stored in plain text** in `web/data/chat.db`. Anyone
  with access to that file (or to the server) can read every message in
  every room, past and present. There is no per-message encryption.
- **No end-to-end encryption.** Messages are readable by the server at
  every step — it has to read them to save history and relay them to
  other users. This is a relay/history model, not E2E encryption like
  Signal or WhatsApp use.
- **No transport encryption by default.** Running `python app.py`
  locally serves plain HTTP, so traffic between your browser and the
  server (including your password on login/register) is unencrypted on
  the wire. If you ever deploy this beyond localhost, put it behind
  HTTPS (a reverse proxy like nginx/Caddy, or a host that provides TLS
  automatically) — otherwise credentials and messages can be
  intercepted on the network.
- **The beginner CLI version (`cli/`) has no authentication or
  encryption at all** — anyone who can connect to the port can join the
  chat and read everything, and traffic is plain, unencrypted TCP. It's
  meant for learning sockets on `localhost`, not for real conversations.
- **Session cookies** (`web/` version) are signed with `app.secret_key`.
  The default key in `app.py` is a placeholder — set your own via the
  `CHAT_SECRET_KEY` environment variable before running this anywhere
  other than your own machine for testing.

**In short:** fine for learning, local testing, or a trusted LAN demo.
Not fine for private conversations you wouldn't want a server operator,
database file, or unencrypted network traffic to expose.
