# BMI Calculator

A BMI calculator with two run modes:

- **Beginner tier (CLI):** `cli.py` — plain command-line input/validation/output.
- **Advanced tier (GUI):** `app.py` — a Flask web app used *instead of tkinter* as the
  GUI layer, with multi-user SQLite storage and a matplotlib BMI trend chart.

## Setup

```bash
pip install -r requirements.txt
```

## Run the CLI version

```bash
python cli.py
```

## Run the Flask GUI version

```bash
python app.py
```

Then open **http://127.0.0.1:5000** in your browser.

- Enter a name, weight (kg), and height (m), then click **Calculate**.
- The result is colour-coded by category (green = normal, red = obese, etc.)
  and automatically saved to `data/bmi_records.db` (SQLite).
- Use **View history** on the home page to see a user's past records and a
  matplotlib line chart of their BMI trend over time.
- Records can be deleted from the history page.
- Database read/write failures are caught and shown as on-page messages
  instead of crashing the app.

## Project structure

```
bmi_calculator/
├── app.py            # Flask app (advanced tier GUI + routes)
├── cli.py             # Command-line app (beginner tier)
├── bmi_logic.py        # Shared BMI calculation / validation logic
├── database.py         # SQLite persistence layer
├── requirements.txt
├── data/
│   └── bmi_records.db  # created automatically on first run
├── templates/
│   ├── base.html
│   ├── index.html
│   └── history.html
└── static/
    └── style.css
```
