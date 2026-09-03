# Random Password Generator

Two run modes:

- **Beginner tier (CLI):** `cli.py` — uses `random` + `string`, plain
  command-line prompts and validation.
- **Advanced tier (GUI):** `app.py` — a Flask web app used *instead of
  tkinter* as the GUI layer. Uses the cryptographically secure `secrets`
  module (see `generator_logic.py`), a strength indicator, guaranteed
  character-type coverage, ambiguous-character exclusion, clipboard copy,
  and session-only history.

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

Then open **http://127.0.0.1:5000**.

- Drag the length slider, tick the character types you want (at least 2),
  optionally exclude ambiguous characters, and click **Generate**.
- The password is built with `secrets` and is guaranteed to include at
  least one character from every type you selected.
- It's copied to your clipboard automatically (via the browser's
  Clipboard API — the web equivalent of `pyperclip`, since `pyperclip`
  would copy to the clipboard of the *server* machine, not your browser).
- A strength bar (Weak / Medium / Strong) is shown based on length and
  character diversity.
- The last 5 passwords generated in this browser session are listed
  under **History** — this is stored only in the Flask session (a signed
  cookie), never written to a file or database, and can be cleared at
  any time with the **Clear** button.

## Project structure

```
password_generator/
├── app.py               # Flask app (advanced tier GUI + routes)
├── cli.py                # Command-line app (beginner tier, random/string)
├── generator_logic.py     # secrets-based generation, validation, strength scoring
├── requirements.txt
├── templates/
│   ├── base.html
│   └── index.html
└── static/
    └── style.css
```
