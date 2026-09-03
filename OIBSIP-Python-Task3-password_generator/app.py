"""
app.py
Advanced-tier Random Password Generator - built with Flask instead of
tkinter/PyQt5.

Features:
- Web form (GUI) with length control + checkboxes for character types
- Uses `secrets` (cryptographically secure) via generator_logic.py
- Strength indicator (Weak / Medium / Strong) with a visual bar
- Guarantees at least one character from every selected type
- "Copy to Clipboard" — auto-copies on generation via the browser's
  Clipboard API (the web-native equivalent of pyperclip, since pyperclip
  controls the OS clipboard of the machine running the Python process,
  not the user's browser/client machine)
- "Exclude ambiguous characters" checkbox (0, O, l, 1, I, etc.)
- Session-based generation history (last 5 passwords) — stored only in
  the Flask session (signed cookie, in-memory on the server side),
  never written to a file or database, and cleared when the session ends
"""

import os
from flask import Flask, render_template, request, session, flash, redirect, url_for

from generator_logic import (
    generate_password,
    score_strength,
    validate_options,
    ValidationError,
    CHAR_POOLS,
)

app = Flask(__name__)
app.secret_key = os.environ.get("PWGEN_SECRET_KEY", "dev-secret-key-change-me")

MIN_LENGTH = 8
MAX_HISTORY = 5

TYPE_LABELS = {
    "uppercase": "Uppercase letters (A-Z)",
    "lowercase": "Lowercase letters (a-z)",
    "numbers": "Numbers (0-9)",
    "symbols": "Symbols (!@#$...)",
}


@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    form_values = {
        "length": request.form.get("length", "16"),
        "selected_types": request.form.getlist("types") or ["uppercase", "lowercase", "numbers"],
        "exclude_ambiguous": bool(request.form.get("exclude_ambiguous")),
    }

    if request.method == "POST":
        length_raw = request.form.get("length", "")
        selected_types = request.form.getlist("types")
        exclude_ambiguous = bool(request.form.get("exclude_ambiguous"))

        try:
            length, selected_types = validate_options(length_raw, selected_types, MIN_LENGTH)
            password = generate_password(length, selected_types, exclude_ambiguous)
            label, score = score_strength(password, selected_types)

            result = {
                "password": password,
                "strength_label": label,
                "strength_score": score,
            }

            # Session-only history (never written to disk). Newest first, capped at 5.
            history = session.get("history", [])
            history.insert(0, {"password": password, "strength_label": label})
            session["history"] = history[:MAX_HISTORY]

        except ValidationError as e:
            flash(str(e), "error")
            result = None

    history = session.get("history", [])

    return render_template(
        "index.html",
        result=result,
        form_values=form_values,
        history=history,
        char_pools=CHAR_POOLS.keys(),
        type_labels=TYPE_LABELS,
        min_length=MIN_LENGTH,
    )


@app.route("/clear-history", methods=["POST"])
def clear_history():
    session.pop("history", None)
    flash("History cleared.", "success")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
