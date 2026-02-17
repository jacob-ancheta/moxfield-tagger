from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from config import CHROMEDRIVER_PATH
import requests
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


# categories are: ramp, card_adv, disruption, board wipes, part of plan, other
# rough categorization based on oracle text keywords
ramp = [
    "add",
    "adds",
    "search your library for a land",
    "put a land onto the battlefield",
    "untap target land",
    "untap up to"
]

card_adv = [
    "draw a card",
    "draw two cards",
    "draw three cards",
    "draw X cards",
    "you may draw",
    "draws"
]

disruption = [
    "counter target",
    "counter unless",
    "copy target spell",
    "destroy target",
    "exile target",
    "return target to its owner's hand",
    "tap target",
    "doesn't untap",
    "exile all cards",
    "change the target",
    "choose new targets",
    "exile any number of target",
    "return target"
]

board_wipes = [
    "destroy all",
    "exile all",
    "each creature",
    "all creatures get damage to each creature",
    "deals damage to all"
]

# Print collected card data and tag them based on oracle text
import re

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
    "ramp": ramp,
    "card_draw": card_adv,
    "disruption": disruption,
    "board_wipes": board_wipes,
}

for card in all_cards:
    oracle = card.get("oracle_text") or ""
    card_type = card.get("type_line") or ""
    norm_oracle = normalize_text(oracle)
    norm_type = normalize_text(card_type)

    tags = []
    matches = {}  # record which keywords matched per category
    for cat_name, keywords in categories.items():
        matched_kw = []
        for kw in keywords:
            if not kw:
                continue
            norm_kw = normalize_text(kw)
            if not norm_kw:
                continue
            # match whole words/phrases only (avoid substrings like 'add' matching 'additional')
            pattern = r'\b' + re.escape(norm_kw) + r'\b'
            if re.search(pattern, norm_oracle):
                matched_kw.append(kw)
        if matched_kw and "land" not in norm_type:
            tags.append(cat_name)
            matches[cat_name] = matched_kw

    print({
        "name": card["name"],
        #"type_line": card.get("type_line"),
        #"oracle_text": oracle,
        "tags": tags,
        "matches": matches,
    })


input("Press Enter to close the browser..." )
driver.quit()
