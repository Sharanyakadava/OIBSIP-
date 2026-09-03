"""
bmi_logic.py
Pure calculation / validation logic, kept separate from Flask so it is
easy to unit test on its own.
"""


class ValidationError(Exception):
    """Raised when user-supplied weight/height fails validation."""
    pass


def parse_positive_float(raw_value, field_name):
    """
    Convert raw form input to a positive float.
    Rejects non-numeric input and zero/negative values with a clear message.
    """
    if raw_value is None or str(raw_value).strip() == "":
        raise ValidationError(f"{field_name} is required.")

    try:
        value = float(str(raw_value).strip())
    except ValueError:
        raise ValidationError(f"{field_name} must be a number (you entered '{raw_value}').")

    if value <= 0:
        raise ValidationError(f"{field_name} must be a positive number greater than zero.")

    return value


def calculate_bmi(weight_kg, height_m):
    """BMI = weight (kg) / height (m) squared."""
    return weight_kg / (height_m ** 2)


def classify_bmi(bmi):
    """
    Standard adult BMI categories:
      Underweight : < 18.5
      Normal      : 18.5 - 24.9
      Overweight  : 25 - 29.9
      Obese       : >= 30
    """
    if bmi < 18.5:
        return "Underweight"
    elif bmi < 25:
        return "Normal"
    elif bmi < 30:
        return "Overweight"
    else:
        return "Obese"


# Colour used for GUI (web) colour-coded feedback
CATEGORY_COLORS = {
    "Underweight": "#f0ad4e",  # amber
    "Normal": "#28a745",       # green
    "Overweight": "#fd7e14",   # orange
    "Obese": "#dc3545",        # red
}


def evaluate(weight_raw, height_raw):
    """
    Validate raw inputs, compute BMI, classify it.
    Returns dict: weight, height, bmi (rounded to 2dp), category, color.
    Raises ValidationError on bad input.
    """
    weight = parse_positive_float(weight_raw, "Weight")
    height = parse_positive_float(height_raw, "Height")

    if height > 3:
        # Common user mistake: entering height in cm instead of metres.
        raise ValidationError(
            "Height looks too large for metres (did you mean to enter it in cm? "
            "e.g. 1.75 instead of 175)."
        )

    bmi = calculate_bmi(weight, height)
    category = classify_bmi(bmi)

    return {
        "weight": weight,
        "height": height,
        "bmi": round(bmi, 2),
        "category": category,
        "color": CATEGORY_COLORS[category],
    }
