from pathlib import Path
import csv
import os
import pandas as pd

BASE_DIR = Path(__file__).parent
CORRECTIONS_FILE = BASE_DIR / "corrections.csv"


def save_correction(card, correct_tags):
    file_exists = CORRECTIONS_FILE.exists()

    with open(CORRECTIONS_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        if not file_exists:
            writer.writerow(["oracle_text", "type_line", "tags"])

        writer.writerow([
            card.get("oracle_text", ""),
            card.get("type_line", ""),
            ",".join(correct_tags)
        ])

    print("Correction saved.")


def load_corrections():
    if CORRECTIONS_FILE.exists():
        return pd.read_csv(CORRECTIONS_FILE)
    return None