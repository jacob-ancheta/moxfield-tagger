import json
from unicodedata import name
import joblib
from dataset import classify_with_rules
from pathlib import Path
from corrections import save_correction

# Load ML model
base_dir = Path(__file__).parent
model_path = base_dir / "ml_model.pkl"
pipeline, mlb = joblib.load(model_path)

def predict_with_ml(card):
    text = (card.get("oracle_text", "") + " " +
            card.get("type_line", ""))

    probs = pipeline.predict_proba([text])[0]

    tags = []
    confidences = []

    for tag, prob in zip(mlb.classes_, probs):
        if prob >= 0.5:
            tags.append(tag)
            confidences.append(prob)

    max_conf = max(probs) if len(probs) > 0 else 0
    return tags, max_conf


def test_random_cards(sample_size=20):
    cards_path = base_dir / "cards.json"
    with open(cards_path, "r", encoding="utf-8") as f:
        cards = json.load(f)
    
    import random
    sample = random.sample(cards, sample_size)

    for card in sample:
        name = card.get("name", "Unknown")
        print("\n==============================")
        print("Card:", name)

        rule_tags, rule_conf, _ = classify_with_rules(card)
        ml_tags, ml_conf = predict_with_ml(card)

        print("Rules:", rule_tags, "conf:", round(rule_conf, 2))
        print("ML   :", ml_tags, "conf:", round(ml_conf, 2))

        correct = input("Correct? (y/n): ").strip().lower()
        if correct == "n":
            user_tags = input("correct tags by comma (ramp, card_draw, disruption, board_wipes, protection, tutors, recursion, none):").strip()
        if not correct or correct.lower() in ["n/a", "na", "none"]:
            print("Skipping correction.")
        else:
            user_tags = [t.strip() for t in user_tags.split(",") if t.strip()]
        if user_tags:
            save_correction(card, user_tags)
        else:
            print("No valid tags entered. Skipping.")
       
        



    rule_tags, rule_conf, _ = classify_with_rules(card)
    ml_tags, ml_conf = predict_with_ml(card)

    print("Rules:", rule_tags, "conf:", round(rule_conf, 2))
    print("ML   :", ml_tags, "conf:", round(ml_conf, 2))

   
if __name__ == "__main__":
    test_random_cards()