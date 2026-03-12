import re
import pywikibot
from datetime import datetime
from collections import deque

VIKIDIA_SITE = pywikibot.Site("fr", "vikidia")
WP_SITE = pywikibot.Site("fr", "wikipedia")
SIMPLE_SITE = pywikibot.Site("simple", "wikipedia")

IGNORE_TEMPLATES = [
    r"\{\{\s*Article\s*VikiConcours",
    r"\{\{\s*Travaux",
]

WP_IW_RE = re.compile(r"\[\[\s*(wp|w)\s*:\s*([^\]\|\n]+)(?:\|[^\]]*)?\s*\]\]", re.I)
SIMPLE_IW_RE = re.compile(r"\[\[\s*simple\s*:\s*([^\]\|\n]+)(?:\|[^\]]*)?\s*\]\]", re.I)

def log(msg: str):
    pywikibot.output(msg)

def should_ignore(text: str) -> str | None:
    low = text.lower().lstrip()
    if low.startswith("#redirect") or low.startswith("#redirection"):
        return "Page = redirection"
    for pattern in IGNORE_TEMPLATES:
        if re.search(pattern, text, flags=re.I):
            return "Modèle ignoré détecté"
    return None

def find_wp_target(text: str):
    m = WP_IW_RE.search(text)
    if not m:
        return None
    return m.group(2).strip()

def get_simple_from_wp(wp_title: str):
    try:
        wp_page = pywikibot.Page(WP_SITE, wp_title)
        if not wp_page.exists():
            return None
        for iw in wp_page.langlinks():
            if iw.site == SIMPLE_SITE:
                return iw.title
    except Exception as e:
        log(f"[ERREUR] Wikipédia: {e}")
        return None
    return None

def insert_simple_under_wp(text: str, simple_title: str) -> str:
    if SIMPLE_IW_RE.search(text):
        return text
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if WP_IW_RE.search(line):
            lines.insert(i + 1, f"[[simple:{simple_title}]]")
            return "\n".join(lines)
    return text

def process_page(title: str) -> bool:
    log(f"Traitement... {title}")
    page = pywikibot.Page(VIKIDIA_SITE, title)
    if page.namespace() != 0 or not page.exists():
        return False
    try:
        text = page.get()
    except Exception as e:
        log(f"Impossible de lire la page: {e}")
        return False
    if reason := should_ignore(text):
        log(f"Ignoré ({reason})")
        return False
    wp_title = find_wp_target(text)
    if not wp_title or SIMPLE_IW_RE.search(text):
        return False
    log(f"Interwiki Wikipédia trouvé : {wp_title}")
    simple_title = get_simple_from_wp(wp_title)
    if not simple_title:
        log("Pas d’interwiki simple trouvé sur Wikipédia")
        return False
    newtext = insert_simple_under_wp(text, simple_title)
    if newtext == text:
        return False
    summary = f"Bot: Ajout de [[simple:{simple_title}]] depuis [[w:{wp_title}]]"
    try:
        page.put(newtext, summary=summary, minor=True, bot=True)
        log("Page enregistrée")
        return True
    except Exception as e:
        log(f"Impossible de sauvegarder: {e}")
        return False

def main():
    log("=== Bot : Ajout de l'interwiki simple ===")
    today = datetime.utcnow().date()
    start = pywikibot.Timestamp(today.year, today.month, today.day, 0, 0, 0)

    seen = set()
    to_process = []

    rcgen = VIKIDIA_SITE.recentchanges(
        start=start,
        namespaces=[0],
        changetype="edit",
        reverse=True,
        total=500
    )

    while True:
        batch = list(rcgen)
        if not batch:
            break
        for rc in batch:
            title = rc.get("title")
            if title and title not in seen:
                seen.add(title)
                to_process.append(title)
        last_rc = batch[-1]
        last_ts = last_rc.get("timestamp")
        rcgen = VIKIDIA_SITE.recentchanges(
            start=last_ts,
            namespaces=[0],
            changetype="edit",
            reverse=True,
            total=500
        )

    log(f"{len(to_process)} pages à traiter")
    for title in to_process:
        process_page(title)

if __name__ == "__main__":
    main()