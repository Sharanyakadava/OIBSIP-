"""
generator_logic.py
Core password generation, validation, and strength-scoring logic.
Kept separate from both cli.py and app.py so it's easy to test on its own.

Uses `secrets` (cryptographically secure) rather than `random` for all
actual password generation, per security best practice.
"""

import string
import secrets

# Characters that are easy to visually confuse: 0/O, l/1/I, etc.
AMBIGUOUS_CHARS = "0Ol1I|`'\""

CHAR_POOLS = {
    "uppercase": string.ascii_uppercase,
    "lowercase": string.ascii_lowercase,
    "numbers": string.digits,
    "symbols": "!@#$%^&*()-_=+[]{};:,.<>?/",
}


class ValidationError(Exception):
    """Raised when the user's requested settings are invalid."""
    pass


def validate_options(length, selected_types, min_length=8):
    """
    Validate password length and character type selections.
    Raises ValidationError with a clear, user-facing message.
    """
    try:
        length = int(length)
    except (TypeError, ValueError):
        raise ValidationError("Length must be a whole number.")

    if length < min_length:
        raise ValidationError(f"Length must be at least {min_length} characters.")

    if length > 256:
        raise ValidationError("Length must be 256 characters or fewer.")

    if not selected_types:
        raise ValidationError("Select at least one character type.")

    unknown = set(selected_types) - set(CHAR_POOLS.keys())
    if unknown:
        raise ValidationError(f"Unknown character type(s): {', '.join(unknown)}")

    if len(selected_types) < 2:
        raise ValidationError("Select at least 2 character types for a stronger password.")

    return length, list(selected_types)


def _strip_ambiguous(pool):
    return "".join(ch for ch in pool if ch not in AMBIGUOUS_CHARS)


def generate_password(length, selected_types, exclude_ambiguous=False):
    """
    Generate a cryptographically secure password that is GUARANTEED to
    contain at least one character from every selected type.

    Approach:
      1. Build the pool for each selected type (optionally stripped of
         ambiguous characters).
      2. Pick one guaranteed character from each selected type's pool.
      3. Fill the remaining length from the combined pool.
      4. Shuffle using secrets.SystemRandom (CSPRNG-backed shuffle) so the
         guaranteed characters aren't predictably placed at the front.
    """
    length, selected_types = validate_options(length, selected_types)

    pools = {}
    for t in selected_types:
        pool = CHAR_POOLS[t]
        if exclude_ambiguous:
            pool = _strip_ambiguous(pool)
        if not pool:
            raise ValidationError(
                f"No characters left for '{t}' after excluding ambiguous characters."
            )
        pools[t] = pool

    # Step 1: guarantee one character from each selected type.
    guaranteed = [secrets.choice(pools[t]) for t in selected_types]

    # Step 2: fill the rest from the combined pool.
    combined_pool = "".join(pools.values())
    remaining = length - len(guaranteed)
    filler = [secrets.choice(combined_pool) for _ in range(remaining)]

    password_chars = guaranteed + filler

    # Step 3: secure shuffle (secrets.SystemRandom, not random.shuffle).
    secrets.SystemRandom().shuffle(password_chars)

    return "".join(password_chars)


def score_strength(password, selected_types):
    """
    Score password strength as 'Weak', 'Medium', or 'Strong' based on
    length and character-type diversity. Returns (label, score_0_to_100).
    """
    length = len(password)
    diversity = len(selected_types)

    score = 0

    # Length contribution (up to 60 points)
    score += min(length, 20) * 2  # up to 40 for first 20 chars
    if length > 20:
        score += min(length - 20, 10)  # up to 10 more
    score = min(score, 60)

    # Diversity contribution (up to 40 points)
    score += diversity * 10  # up to 40 for 4 types

    score = min(score, 100)

    if score < 45:
        label = "Weak"
    elif score < 75:
        label = "Medium"
    else:
        label = "Strong"

    return label, score
