import re


def ramp(card):
    oracle = (card.get("oracle_text") or "").lower()
    type_line = (card.get("type_line") or "").lower()

    score = 0.0

    # pattern: "{T}: Add {G}"
    if re.search(r"\{t\}.*add\s*\{[wubrgc]\}", oracle):
        score += 1.0

    # land tutoring
    if "search your library for a land" in oracle:
        score += 1.0

    # land to battlefield ramp
    if "put a land onto the battlefield" in oracle:
        score += 0.9

    # mana rock pattern
    if "artifact" in type_line and re.search(r"add\s*\{[wubrgc]\}", oracle):
        score += 0.8

    # creature mana dork without tap symbol (rare but possible)
    if "creature" in type_line and re.search(r"add\s*\{[wubrgc]\}", oracle):
        score += 0.6

    # rituals
    if re.search(r"add\s*\{[wubrgc]\}", oracle):
        score += 0.7
 
    # keyword signals
    if "untap target land" in oracle:
        score += 0.6

    if "untap up to" in oracle:
        score += 0.3

    if "add" in oracle:
        score += 0.1  

    return min(round(score, 2), 1.0)

def card_draw(card):
    oracle = (card.get("oracle_text") or "").lower()

    score = 0.0

    # explicit matching
    if re.search(r"draw\s+three\s+cards", oracle):
        score += 1.0

    if re.search(r"draw\s+two\s+cards", oracle):
        score += 0.9

    if re.search(r"draw\s+x\s+cards", oracle):
        score += 0.9

    # generic matching
    if re.search(r"draw\s+a\s+card", oracle):
        score += 0.6

    if re.search(r"draw\s+\w+\s+cards", oracle):
        score += 0.7  

    # repeated draw
    if "whenever" in oracle and "draw" in oracle:
        score += 0.6

    if "at the beginning" in oracle and "draw" in oracle:
        score += 0.6

    if "you may draw" in oracle:
        score += 0.4

    # keyword signals
    if "draws" in oracle:
        score += 0.2

    return min(round(score, 2), 1.0)

def disruption(card):
    oracle = (card.get("oracle_text") or "").lower()
    score = 0.0
    
    # counterspells
    if re.search(r"counter\s+target", oracle):
        score += 1.0
    if re.search(r"counter\s+.*unless", oracle):
        score += 0.9

    # removal
    if re.search(r"destroy\s+target", oracle):
        score += 0.8
    if re.search(r"exile\s+target", oracle):
        score += 0.8

    # bounce spells
    if re.search(r"return\s+target.*to\s+its\s+owner'?s\s+hand", oracle):
        score += 0.7

    # stack manipulation
    if "copy target spell" in oracle:
        score += 0.6
    if "change the target" in oracle or "choose new targets" in oracle:
        score += 0.6
 
    # tappers
    if re.search(r"tap\s+target", oracle):
        score += 0.4
    if "doesn't untap" in oracle:
        score += 0.5

    # exiles
    if re.search(r"exile\s+any\s+number\s+of\s+target", oracle):
        score += 0.9


    return min(round(score, 2), 1.0)


def board_wipe(card):
    oracle = (card.get("oracle_text") or "").lower()

    score = 0.0
    #  creature board wipes
    if re.search(r"destroy\s+all\s+creatures", oracle):
        score += 1.0
    if re.search(r"exile\s+all\s+creatures", oracle):
        score += 1.0
    if re.search(r"destroy\s+all\s+.*creatures", oracle):
        score += 0.9
    if re.search(r"exile\s+all\s+.*creatures", oracle):
        score += 0.9

    # damage-based 
    if re.search(r"deals\s+\d+\s+damage\s+to\s+each\s+creature", oracle):
        score += 0.9

    # mass artifact/enchantment/planeswalker wipes
    if re.search(r"destroy\s+all\s+artifacts", oracle) or re.search(r"exile\s+all\s+artifacts", oracle):
        score += 0.8
    if re.search(r"destroy\s+all\s+enchantments", oracle) or re.search(r"exile\s+all\s+enchantments", oracle):
        score += 0.8
    if re.search(r"destroy\s+all\s+planeswalkers", oracle) or re.search(r"exile\s+all\s+planeswalkers", oracle):
        score += 0.8

    # all permanents
    if re.search(r"destroy\s+all\s+permanents", oracle) or re.search(r"exile\s+all\s+permanents", oracle):
        score += 1.0

    return min(round(score, 2), 1.0)

def protection(card):
    oracle = (card.get("oracle_text") or "").lower()
    score = 0.0

    # protection from colors
    if re.search(r"gain\s+protection\s+from", oracle):
        score += 0.9

    # hexproof 
    if re.search(r"(gains|gain|has)\s+hexproof", oracle):
        score += 0.8

    # indestructible 
    if re.search(r"(gains|gain|has)\s+indestructible", oracle):
        score += 0.9
    if "cannot be destroyed" in oracle:
        score += 0.9

    # can't be countered
    if "spells you control cannot be countered" in oracle:
        score += 0.8
    if "noncreature spells you control cannot be countered" in oracle:
        score += 0.9

    return min(round(score, 2), 1.0)

def tutors(card):
    oracle = (card.get("oracle_text") or "").lower()
    score = 0.0 

    if "search your library for a card" in oracle:
        score += 1.0
    if re.search(r"search your library for an? [a-z]+", oracle):
        score += 0.7
    if re.search(r"search your library for a? [a-z]+", oracle):
        score += 0.7
    return min(round(score, 2), 1.0)

def recursion(card):
    oracle = (card.get("oracle_text") or "").lower()
    score = 0.0
    if "from your graveyard to your hand" in oracle:
        score += 0.9
    if "from your graveyard to your battlefield" in oracle:
        score += 1.0
    return min(round(score, 2), 1.0)

