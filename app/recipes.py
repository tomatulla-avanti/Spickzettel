import re

UNIT_PATTERN = re.compile(
    r"^\s*\d+([.,]\d+)?\s*(g|kg|mg|ml|l|tl|el|el\.|prise(n)?|st(ü|ue)ck|st\.|scheibe(n)?|dose(n)?|packung(en)?|zehe(n)?|kopf|knolle(n)?|bund|bündel)?\s*\S",
    re.IGNORECASE,
)

BULLETS = "-•*– "


def parse_recipe_text(text):
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    ingredients, steps = [], []
    section = None
    for line in lines:
        low = line.lower().rstrip(":").strip()
        if low.startswith(("zutaten", "ingredients")):
            section = "ing"
            continue
        if low.startswith(("zubereitung", "preparation", "steps", "zubereiten")):
            section = "steps"
            continue
        stripped = line.lstrip(BULLETS).strip()
        if section == "ing":
            ingredients.append(stripped)
        elif section == "steps":
            steps.append(line)
        elif UNIT_PATTERN.match(stripped):
            ingredients.append(stripped)
        else:
            steps.append(line)
    if not ingredients and not steps:
        steps = lines
    return ingredients, steps


STOPWORDS = {
    "und", "oder", "frisch", "gehackt", "geschnitten", "optional", "nach",
    "geschmack", "vom", "der", "die", "das", "mit", "zum", "zum", "klein",
    "gross", "grosse", "etwas", "wenig", "reichlich",
}


def normalize_ingredient(name):
    name = name.lower()
    name = re.sub(
        r"^\s*\d+([.,]\d+)?\s*(g|kg|mg|ml|l|tl|el|prise(n)?|st(ü|ue)ck|st\.|scheibe(n)?|dose(n)?|packung(en)?|zehe(n)?|kopf|knolle(n)?|bund)?\.?\s*",
        "",
        name,
        flags=re.IGNORECASE,
    )
    name = re.sub(r"[^a-zäöüß\s-]", " ", name)
    words = [w for w in name.split() if w not in STOPWORDS and len(w) > 2]
    return " ".join(words).strip() if words else name.strip()


def score_recipe(recipe_ingredients, have):
    have_norm = {normalize_ingredient(h) for h in have if h.strip()}
    have_norm.discard("")
    if not have_norm or not recipe_ingredients:
        return 0.0, []
    matched = []
    for ing in recipe_ingredients:
        n = normalize_ingredient(ing)
        if n and any(h in n or n in h for h in have_norm):
            matched.append(ing)
    return len(matched) / len(recipe_ingredients), matched
