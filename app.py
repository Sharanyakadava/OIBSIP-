"""
app.py
Advanced-tier BMI Calculator - built with Flask instead of tkinter/PyQt5.

Features:
- Web form (GUI) for weight/height/user name -> "Calculate" button
- Colour-coded result feedback
- Multi-user support with named records
- SQLite persistence (database.py)
- BMI trend line chart per user, rendered with matplotlib
- Error handling for DB read/write failures (flash messages, no crashes)
"""

import io
import os

from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, send_file, abort
)
import matplotlib
matplotlib.use("Agg")  # headless rendering, no GUI backend needed
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

import database as db
from bmi_logic import evaluate, ValidationError

app = Flask(__name__)
app.secret_key = os.environ.get("BMI_SECRET_KEY", "dev-secret-key-change-me")

# Make sure the DB / table exist before serving any request.
try:
    db.init_db()
except db.DatabaseError as e:
    # If the DB can't even be created, the app can't function.
    # We still let Flask start so the error is visible in the browser,
    # rather than crashing silently on import.
    print(f"FATAL: could not initialise database: {e}")


@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    form_values = {"user_name": "", "weight": "", "height": ""}

    if request.method == "POST":
        user_name = request.form.get("user_name", "").strip()
        weight_raw = request.form.get("weight", "")
        height_raw = request.form.get("height", "")
        form_values = {"user_name": user_name, "weight": weight_raw, "height": height_raw}

        try:
            if not user_name:
                raise ValidationError("Please enter a name so your result can be saved.")

            result = evaluate(weight_raw, height_raw)

            # Persist the record; handle DB failures gracefully.
            try:
                db.add_record(
                    user_name=user_name,
                    weight_kg=result["weight"],
                    height_m=result["height"],
                    bmi=result["bmi"],
                    category=result["category"],
                )
                flash(f"Saved result for {user_name}.", "success")
            except db.DatabaseError as e:
                flash(f"Result calculated, but could not be saved: {e}", "warning")

        except ValidationError as e:
            flash(str(e), "error")
            result = None

    # Populate the "view history for" dropdown; tolerate DB errors.
    try:
        known_users = db.get_all_user_names()
        db_error = None
    except db.DatabaseError as e:
        known_users = []
        db_error = str(e)

    return render_template(
        "index.html",
        result=result,
        form_values=form_values,
        known_users=known_users,
        db_error=db_error,
    )


@app.route("/history/<user_name>")
def history(user_name):
    try:
        records = db.get_records_for_user(user_name)
    except db.DatabaseError as e:
        flash(f"Could not load history: {e}", "error")
        records = []

    if not records:
        flash(f"No records found for '{user_name}'.", "warning")

    return render_template("history.html", user_name=user_name, records=list(reversed(records)))


@app.route("/graph/<user_name>.png")
def graph(user_name):
    """Render a matplotlib line chart of a user's BMI trend as a PNG."""
    try:
        records = db.get_records_for_user(user_name)
    except db.DatabaseError:
        abort(500, description="Could not read records for graph.")

    if not records:
        abort(404, description="No records for this user yet.")

    dates = [datetime.fromisoformat(r["recorded_at"]) for r in records]
    bmis = [r["bmi"] for r in records]

    fig, ax = plt.subplots(figsize=(7, 4), dpi=110)
    ax.plot(dates, bmis, marker="o", color="#2b6cb0", linewidth=2)

    # Reference bands for the four BMI categories.
    ax.axhspan(0, 18.5, color="#f0ad4e", alpha=0.12)
    ax.axhspan(18.5, 25, color="#28a745", alpha=0.12)
    ax.axhspan(25, 30, color="#fd7e14", alpha=0.12)
    ax.axhspan(30, max(40, max(bmis) + 5), color="#dc3545", alpha=0.12)

    ax.set_title(f"BMI Trend — {user_name}")
    ax.set_xlabel("Date")
    ax.set_ylabel("BMI")
    ax.set_ylim(bottom=min(15, min(bmis) - 2), top=max(35, max(bmis) + 2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    fig.autofmt_xdate()
    ax.grid(True, linestyle="--", alpha=0.4)
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    plt.close(fig)
    buf.seek(0)

    return send_file(buf, mimetype="image/png")


@app.route("/delete/<int:record_id>/<user_name>", methods=["POST"])
def delete(record_id, user_name):
    try:
        db.delete_record(record_id)
        flash("Record deleted.", "success")
    except db.DatabaseError as e:
        flash(f"Could not delete record: {e}", "error")
    return redirect(url_for("history", user_name=user_name))


if __name__ == "__main__":
    app.run(debug=True)
