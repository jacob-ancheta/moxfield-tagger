import json
import pandas as pd
import sys 
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.resolve()))

from categories import ramp, card_draw, disruption, board_wipe, protection, tutors, recursion


def classify_with_rules(card, threshold=0.7):
    scores = {
        "ramp": ramp(card),
        "card_draw": card_draw(card),
        "disruption": disruption(card),
        "board_wipe": board_wipe(card),
        "protection": protection(card),
        "tutors": tutors(card),
        "recursion": recursion(card),
    }

    tags = [k for k, v in scores.items() if v >= threshold]
    max_conf = max(scores.values()) if scores else 0

    return tags, max_conf, scores

def bootstrap_training_data():
    base_dir = Path(__file__).parent
    cards_path = base_dir / "cards.json"

    with open(cards_path, "r", encoding="utf-8") as f:
        cards = json.load(f)

    rows = []

    for card in cards:
        tags, confidence, _ = classify_with_rules(card, threshold=0.7)

        if tags:  # only high confidence cards
            if "board_wipe" in tags:
                tags = ["board_wipe"]
            rows.append({
                "oracle_text": card.get("oracle_text", ""),
                "type_line": card.get("type_line", ""),
                "tags": ",".join(tags)
            })

    df = pd.DataFrame(rows)
    out_path = base_dir / "training_data.csv"
    df.to_csv(out_path, index=False)

    print(f"Bootstrapped {len(df)} examples. Wrote {out_path}")


if __name__ == "__main__":
    bootstrap_training_data()