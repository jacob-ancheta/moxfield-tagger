from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from config import CHROMEDRIVER_PATH
import requests
import categories
import re
# selenium accesses elements using locators like By.ID, By.NAME, By.CSS_SELECTOR, By.XPATH, etc.

service = Service(CHROMEDRIVER_PATH)
driver = webdriver.Chrome(service=service)

api = "https://api.scryfall.com/cards/collection"

# url = input("paste url here (must be unlisted or public): ")
url = "https://www.google.com"
url2 = "https://moxfield.com/"
url3 = "https://moxfield.com/decks/IAy9EmFU6E69zz-WGrsc-g"
driver.get(str(url3))


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

for card in all_cards:
    oracle = card.get("oracle_text") or ""
    card_type = card.get("type_line") or ""
    norm_oracle = normalize_text(oracle)
    norm_type = normalize_text(card_type)

    tags = []
    matches = {}  # record category -> score
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

    # print card with category scores
    print({
        "name": card["name"],
        "tags": tags,
        "category_scores": matches,
    })


input("Press Enter to close the browser..." )
driver.quit()
