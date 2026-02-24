import sys, os
from pathlib import Path
import json

sys.path.append(str(Path(__file__).parent.parent.resolve()))

import categories
from categories import ramp, card_draw, disruption, board_wipe, protection, tutors, recursion


BASE_DIR = os.path.dirname(__file__) 
json_path = os.path.join(BASE_DIR, "cards.json")
def get_scores(card):
    return {
        "ramp": ramp(card),
        "card_draw": card_draw(card),
        "disruption": disruption(card),
        "board_wipes": board_wipe(card),
        "protection": protection(card),
        "tutors": tutors(card),
        "recursion": recursion(card)
    }

LABELS = [
    "ramp",
    "card_draw",
    "disruption",
    "board_wipes",
    "protection",
    "tutors",
    "recursion"
]

THRESHOLD = 0.7

def scores_to_vector(score_dict):
    return [
        1 if score_dict[label] >= THRESHOLD else 0
        for label in LABELS
    ]

def build_text(card):
    oracle = card.get("oracle_text") or ""
    type_line = card.get("type_line") or ""
    return (oracle + " " + type_line).strip()


def is_valid_card(card):
    if not card.get("oracle_text"):
        return False
    if card.get("layout") in ["token", "art_series"]:
        return False
    if card.get("digital"):
        return False
    return True


def main():
    with open("cards.json", "r", encoding="utf-8") as f:
        cards = json.load(f)

    output_file = open("train.jsonl", "w", encoding="utf-8")

    kept = 0

    for card in cards:
        if not is_valid_card(card):
            continue

        scores = categories.get_scores(card)
        label_vector = scores_to_vector(scores)

        # Skip cards with no tags (optional but recommended)
        if sum(label_vector) == 0:
            continue

        example = {
            "text": build_text(card),
            "labels": label_vector
        }

        output_file.write(json.dumps(example) + "\n")
        kept += 1

    output_file.close()

    print(f"Saved {kept} labeled cards to train.jsonl")


if __name__ == "__main__":
    main()