from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from config import CHROMEDRIVER_PATH
import requests
import categories as cat_module
import re
import joblib
from pathlib import Path
from ai.corrections import save_correction, load_corrections



# UTILS -----------------------------
def normalize_text(s: str) -> str:
    if not s:
        return ""
    s = s.lower()
    s = re.sub(r'[^a-z0-9 ]+', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s


def chunked(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i+n]


# LOAD MODEL + CORRECTIONS -----------------------------
base_dir = Path(__file__).parent / "ai"
model_path = base_dir / "ml_model.pkl"

pipeline, mlb = joblib.load(model_path)

corrections_df = load_corrections()
correction_lookup = {}

if corrections_df is not None:
    for _, row in corrections_df.iterrows():
        key = normalize_text(row["text"])
        correction_lookup[key] = row["tags"]


# ML PREDICTION -----------------------------
def predict_with_ml(card):
    text = (card.get("oracle_text", "") + " " +
            card.get("type_line", ""))

    probs = pipeline.predict_proba([text])[0]

    tags = []
    norm_type = normalize_text(card.get("type_line", ""))

    for tag, prob in zip(mlb.classes_, probs):
        if isinstance(tag, str) and tag.startswith("["):
            tag = tag.strip("[]'\"")

        if prob >= 0.5:
            if (tag == "ramp" or tag == "tutors") and "land" in norm_type:
                continue
            tags.append(tag)

    max_conf = max(probs) if len(probs) > 0 else 0
    return tags, float(max_conf)

# CATEGORY MAP ------------------------------
category_map = {
    "ramp": cat_module.ramp,
    "card_draw": cat_module.card_draw,
    "disruption": cat_module.disruption,
    "board_wipes": cat_module.board_wipe,
    "protection": cat_module.protection,
    "tutors": cat_module.tutors,
    "recursion": cat_module.recursion,
}



# MAIN ENGINE ------------------------------
def tag_deck(url):
    service = Service(CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service)

    api = "https://api.scryfall.com/cards/collection"

    driver.get(url)

    wait = WebDriverWait(driver, 15)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a.table-deck-row-link.text-body")))

    cards = driver.find_elements(By.CSS_SELECTOR, "a.table-deck-row-link.text-body")

    card_list = []

    for card in cards:
        href = card.get_attribute("href")
        if href and "/cards/" in href:
            name_spans = card.find_elements(By.CSS_SELECTOR, "span.underline")
            full_name = " ".join(span.text.strip() for span in name_spans if span.text.strip())
            if full_name not in card_list:
                card_list.append(full_name)

    identifiers = [{"name": name} for name in card_list]

    all_cards = []

    for chunk in chunked(identifiers, 75):
        response = requests.post(api, json={"identifiers": chunk})
        response.raise_for_status()
        data = response.json()
        all_cards.extend(data["data"])

    results = []

    for card in all_cards:

        # CHECK MANUAL CORRECTIONS ------------------------------
        lookup_key = normalize_text(
            (card.get("oracle_text", "") or "") + " " +
            (card.get("type_line", "") or "")
        )

        if lookup_key in correction_lookup:
            results.append({
                "name": card["name"],
                "tags": correction_lookup[lookup_key],
                "category_scores": {"manual": 1.0},
                "source": "manual",
                "card": card
            })
            continue

        # RULES ------------------------------
        norm_type = normalize_text(card.get("type_line", ""))

        tags = []
        matches = {}
        source = "rules"

        for cat_name, classifier in category_map.items():
            try:
                score = classifier(card)
            except Exception:
                score = 0.0

            if score > 0:
                if (cat_name in ["ramp", "tutors"]) and "land" in norm_type:
                    continue

                tags.append(cat_name)
                matches[cat_name] = float(round(score, 2))

        # ML FALLBACK ------------------------------
        use_ml = not any(score >= 0.7 for score in matches.values())

        if use_ml:
            ml_tags, ml_conf = predict_with_ml(card)

            if ml_tags:
                tags = ml_tags
                matches = {"ml_model": float(round(ml_conf, 2))}
                source = "ml"

        results.append({
            "name": card["name"],
            "tags": tags,
            "category_scores": matches,
            "source": source,
            "card": card
        })

    driver.quit()
    return results