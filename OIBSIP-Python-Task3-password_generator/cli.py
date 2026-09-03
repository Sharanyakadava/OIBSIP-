"""
cli.py
Beginner-tier command-line password generator.
Uses the `random` and `string` modules only (per beginner spec).

NOTE: `random` is NOT cryptographically secure. The advanced Flask app
(app.py / generator_logic.py) uses the `secrets` module instead, which is
the recommended approach for real-world password generation.
"""

import random
import string

MIN_LENGTH = 8

CHAR_POOLS = {
    "1": ("uppercase letters", string.ascii_uppercase),
    "2": ("lowercase letters", string.ascii_lowercase),
    "3": ("numbers", string.digits),
    "4": ("symbols", "!@#$%^&*()-_=+[]{};:,.<>?/"),
}


def get_length():
    while True:
        raw = input(f"Enter desired password length (minimum {MIN_LENGTH}): ").strip()
        try:
            length = int(raw)
        except ValueError:
            print(f"  Invalid input: '{raw}' is not a whole number. Try again.\n")
            continue
        if length < MIN_LENGTH:
            print(f"  Invalid length: must be at least {MIN_LENGTH} characters. Try again.\n")
            continue
        return length


def get_character_types():
    print("\nChoose character types to include (select at least 2):")
    for key, (label, _) in CHAR_POOLS.items():
        print(f"  {key}. {label}")

    while True:
        raw = input("Enter numbers separated by spaces (e.g. 1 2 3): ").strip()
        choices = raw.split()

        if not all(c in CHAR_POOLS for c in choices):
            print("  Invalid selection: please enter only the listed numbers. Try again.\n")
            continue

        unique_choices = sorted(set(choices))
        if len(unique_choices) < 2:
            print("  Invalid selection: choose at least 2 different character types. Try again.\n")
            continue

        return unique_choices


def generate_password(length, choices):
    """
    Build the character pool from the selected types, then generate a
    password. Guarantees at least one character per selected type so the
    password always satisfies the chosen criteria.
    """
    selected_pools = [CHAR_POOLS[c][1] for c in choices]

    # Guarantee at least one character from each selected type.
    guaranteed = [random.choice(pool) for pool in selected_pools]

    combined_pool = "".join(selected_pools)
    remaining_length = length - len(guaranteed)
    filler = [random.choice(combined_pool) for _ in range(remaining_length)]

    password_chars = guaranteed + filler
    random.shuffle(password_chars)

    return "".join(password_chars)


def main():
    print("=== Random Password Generator (Command Line) ===")
    while True:
        length = get_length()
        choices = get_character_types()

        password = generate_password(length, choices)

        print(f"\nGenerated password: {password}\n")

        again = input("Generate another password? (y/n): ").strip().lower()
        if again != "y":
            print("Goodbye!")
            break
        print()


if __name__ == "__main__":
    main()
