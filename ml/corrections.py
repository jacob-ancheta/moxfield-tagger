from pathlib import Path
import csv
import os
import pandas as pd

BASE_DIR = Path(__file__).parent
CORRECTIONS_FILE = BASE_DIR / "corrections.csv"


def save_correction(card, correct_tags):
    file_exists = CORRECTIONS_FILE.exists()

    with open(CORRECTIONS_FILE, "a", newline="", encoding="utf-8") as f:
        if CORRECTIONS_FILE.stat().st_size == 0:
            f.write("oracle_text,type_line,tags\n")

        writer = csv.writer(f)

        if not file_exists:
            writer.writerow(["oracle_text", "type_line", "tags"])

        writer.writerow([
            card.get("oracle_text", "").replace("\n", " "),
            card.get("type_line", ""),
            ",".join(correct_tags)
        ])

    print("Correction saved.")

def safe_split(x):
        if isinstance(x, str):
            return [t.strip() for t in x.split(",") if t.strip()]
        return []

def load_corrections():
    if CORRECTIONS_FILE.exists():
        df = pd.read_csv(CORRECTIONS_FILE)

        df["text"] = df["oracle_text"].fillna("") + " " + df["type_line"].fillna("")
        df["tags"] = df["tags"].apply(safe_split)

        return df[["text", "tags"]]

    return None

