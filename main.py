from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from config import CHROMEDRIVER_PATH
import requests
import categories
import re
import joblib
from pathlib import Path
from ai.corrections import save_correction, load_corrections
# selenium accesses elements using locators like By.ID, By.NAME, By.CSS_SELECTOR, By.XPATH, etc.

# Load ML model
base_dir = Path(__file__).parent / "ai"
model_path = base_dir / "ml_model.pkl"

pipeline, mlb = joblib.load(model_path)

def predict_with_ml(card):
    text = (card.get("oracle_text", "") + " " +
            card.get("type_line", ""))

    probs = pipeline.predict_proba([text])[0]

    tags = []
    confidences = []
    norm_type = normalize_text(card.get("type_line", ""))

    for tag, prob in zip(mlb.classes_, probs):
        if isinstance(tag, str) and tag.startswith("["):
            tag = tag.strip("[]'\"")
        if prob >= 0.5:
            if (tag == "ramp" or tag == "tutors") and "land" in norm_type:
                continue
            tags.append(tag)
            confidences.append(prob)

    max_conf = max(probs) if len(probs) > 0 else 0
    return tags, max_conf



service = Service(CHROMEDRIVER_PATH)
driver = webdriver.Chrome(service=service)

api = "https://api.scryfall.com/cards/collection"

# url = input("paste url here (must be unlisted or public): ")
url_m = "https://moxfield.com/decks/IAy9EmFU6E69zz-WGrsc-g"
url = input("Please paste Moxfield decklist page URL: ")
driver.get(str(url))


card_list = []
#cards = driver.find_elements(By.CSS_SELECTOR, '.decklist-card')
wait = WebDriverWait(driver, 15)

wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a.table-deck-row-link.text-body")))
cards = driver.find_elements(By.CSS_SELECTOR, "a.table-deck-row-link.text-body")

for card in cards:
    # checks if has attribute href, ignoring section titles
    href = card.get_attribute("href")
    if href and "/cards/" in href:
        name_spans = card.find_elements(By.CSS_SELECTOR, "span.underline")
        full_name = " ".join(span.text.strip() for span in name_spans if span.text.strip())
        if full_name not in card_list:
            card_list.append(full_name)


identifiers = []

for name in card_list:
    identifiers.append({"name": name}) 

def chunked(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i+n]

all_cards = []
for chunk in chunked(identifiers, 75):
    payload = {"identifiers": chunk}
    try:
        response = requests.post(api, json=payload)
    except requests.RequestException as exc:
        print("Network error while contacting Scryfall:", exc)
        raise

    if response.status_code != 200:
        print(f"Scryfall API error: {response.status_code} - {response.text}")
        response.raise_for_status()

    data = response.json()
    if "data" not in data:
        print("Unexpected API response:", data)
        raise KeyError("'data' missing in Scryfall response")

    all_cards.extend(data["data"])

def normalize_text(s: str) -> str:
    """lowercase and replace non-alphanumeric characters with spaces for robust matching."""
    if not s:
        return ""
    s = s.lower()
    s = re.sub(r'[^a-z0-9 ]+', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

corrections_df = load_corrections()

correction_lookup = {}

if corrections_df is not None:
    for _, row in corrections_df.iterrows():
        key = normalize_text(row["text"])
        correction_lookup[key] = row["tags"]

# map category names to their keyword lists
categories = {
    "ramp": categories.ramp,
    "card_draw": categories.card_draw,
    "disruption": categories.disruption,
    "board_wipes": categories.board_wipe,
    "protection": categories.protection,
    "tutors": categories.tutors,
    "recursion": categories.recursion,
}

results = []

for card in all_cards:
    # Check manual corrections first
    lookup_key = normalize_text(
        (card.get("oracle_text", "") or "") + " " +
        (card.get("type_line", "") or "")
    )

    if lookup_key in correction_lookup:
        tags = correction_lookup[lookup_key]
        matches = {"manual": 1.0}
        source = "manual"

        result = {
            "name": card["name"],
            "tags": tags,
            "category_scores": matches,
            "source": source,
            "card": card
        }

        results.append(result)

        print({
            "name": result["name"],
            "tags": result["tags"],
            "category_scores": result["category_scores"],
            "source": result["source"]
        })

        continue
    
    # then go
    oracle = card.get("oracle_text") or ""
    card_type = card.get("type_line") or ""
    norm_oracle = normalize_text(oracle)
    norm_type = normalize_text(card_type)

    tags = []
    matches = {}  # record category -> score
    source = "rules"
    for cat_name, classifier in categories.items():
        try:
            score = classifier(card)
        except Exception:
            score = 0.0
        if score and score > 0:
            # don't tag lands as ramp, but allow other categories (e.g. disruption) on lands
            if (cat_name == "ramp" or cat_name == "tutors") and "land" in norm_type:
                continue
            tags.append(cat_name)
            matches[cat_name] = float(round(score, 2))
    
    use_ml = True

    # if ANY category >= 0.7 we keep rule-based result
    for score in matches.values():
        if score >= 0.7:
            use_ml = False
            break

    if use_ml:
        ml_tags, ml_conf = predict_with_ml(card)

        if ml_tags:
            tags = ml_tags
            matches = {"ml_model": float(round(ml_conf, 2))}
            source = "ml"

    # print card with category scores
    result = {
    "name": card["name"],
    "tags": tags,
    "category_scores": matches,
    "source": source,
    "card": card
}

    results.append(result)

    print({
        "name": result["name"],
        "tags": result["tags"],
        "category_scores": result["category_scores"],
        "source": result["source"]
    })

category_totals = {}

for r in results:
    for tag in r["tags"]:
        category_totals[tag] = category_totals.get(tag, 0) + 1

print("\nCategory totals:\n")
for cat, count in sorted(category_totals.items()):
    print(f"{cat}: {count}")

choice = input("\nWould you like to perform manual corrections? (Y/N): ").strip().lower()

if choice == "y":
    correction_count = 0
    print("\nCards detected:\n")

    for i, r in enumerate(results, start=1):
        print(f"{i}. {r['name']} -> {r['tags']} ({r['source']})")

    selection = input(
        "\nEnter card numbers to correct (example: 1 2 4 5 12): "
    ).strip()

    if selection:

        indices = [int(x) for x in selection.split() if x.isdigit()]

        for idx in indices:

            if idx < 1 or idx > len(results):
                print(f"Invalid card number: {idx}")
                continue

            selected = results[idx - 1]

            print("\n-------------------------")
            print("Card:", selected["name"])
            print("Current tags:", selected["tags"])

            user_tags = input(
                "Enter correct tags (comma separated) "
                "(ramp, card_draw, disruption, board_wipes, protection, tutors, recursion, none): "
            ).strip()

            if not user_tags or user_tags.lower() in ["none", "na", "n/a"]:
                print("Skipping correction.")
                continue

            correct_tags = [t.strip() for t in user_tags.split(",") if t.strip()]

            if correct_tags:
                save_correction(selected["card"], correct_tags)
                correction_count += 1
            else:
                print("No valid tags entered. Skipping.")
    print(f"\nSaved {correction_count} corrections.")

print("\nDone.")
retrain = input("\nWould you like to retrain the model now? (Y/N): ").strip().lower()

if retrain == "y":
    print("\nRetraining model...\n")
    try:
        from ai.train_model import train_model
        train_model()
    except Exception as e:
        print(f"Error during training: {e}")
driver.quit()
