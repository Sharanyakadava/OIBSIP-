"""
cli.py
Beginner-tier command-line BMI calculator.
Run with:  python cli.py
(The advanced/full-featured version is the Flask web app in app.py)
"""

from bmi_logic import evaluate, ValidationError


def main():
    print("=== BMI Calculator (Command Line) ===")
    while True:
        weight_raw = input("Enter your weight in kg: ")
        height_raw = input("Enter your height in m (e.g. 1.75): ")

        try:
            result = evaluate(weight_raw, height_raw)
        except ValidationError as e:
            print(f"\nInput error: {e}\nPlease try again.\n")
            continue

        print(f"\nYour BMI is: {result['bmi']:.2f}")
        print(f"Category: {result['category']}\n")

        again = input("Calculate another? (y/n): ").strip().lower()
        if again != "y":
            print("Goodbye!")
            break


if __name__ == "__main__":
    main()
