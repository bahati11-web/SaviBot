import time
import re
import pywikibot
from collections import deque

VIKIDIA_SITE = pywikibot.Site("fr", "vikidia")
WP_SITE = pywikibot.Site("fr", "wikipedia")
SIMPLE_SITE = pywikibot.Site("simple", "wikipedia")

IGNORE_TEMPLATES = [
    r"\{\{\s*Article\s*VikiConcours",
    r"\{\{\s*Travaux",
]

WP_IW_RE = re.compile(
    r"\[\[\s*(wp|w)\s*:\s*([^\]\|\n]+)(?:\|[^\]]*)?\s*\]\]",
    re.I
)

SIMPLE_IW_RE = re.compile(
    r"\[\[\s*simple\s*:\s*([^\]\|\n]+)(?:\|[^\]]*)?\s*\]\]",
    re.I
)

def log(msg: str):
    pywikibot.output(msg)

def should_ignore(text: str) -> str | None:

    low = text.lower().lstrip()

    if low.startswith("#redirect") or low.startswith("#redirection"):
        return "Page = redirection"

    for pattern in IGNORE_TEMPLATES:
        if re.search(pattern, text, flags=re.I):
            return "Modèle ignoré détecté (VikiConcours/Travaux)"

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
        log(f"   [ERREUR] Wikipédia: {e}")
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

    if page.namespace() != 0:
        log("   -> Ignoré (pas dans l'espace principal)")
        return False

    if not page.exists():
        log("   -> Ignoré (page inexistante)")
        return False

    try:
        text = page.get()
    except Exception as e:
        log(f"   -> Ignoré (impossible de lire la page: {e})")
        return False

    reason = should_ignore(text)
    if reason:
        log(f"   -> Ignoré ({reason})")
        return False

    wp_title = find_wp_target(text)
    if not wp_title:
        log("   -> Ignoré (pas de [[wp:...]] ou [[w:...]])")
        return False

    if SIMPLE_IW_RE.search(text):
        log("   -> Ignoré (interwiki simple déjà présent)")
        return False

    log(f"   -> Interwiki Wikipédia trouvé : {wp_title}")

    simple_title = get_simple_from_wp(wp_title)
    if not simple_title:
        log("   -> Ignoré (pas d’interwiki simple trouvé sur Wikipédia)")
        return False

    log(f"   -> Interwiki simple trouvé : {simple_title}")

    newtext = insert_simple_under_wp(text, simple_title)
    if newtext == text:
        log("   -> Ignoré (aucun changement à faire)")
        return False

    summary = f"Bot: Ajout de [[simple:{simple_title}]] depuis [[w:{wp_title}]]"

    try:
        page.put(newtext, summary=summary, minor=True, botflag=True)
        log("   -> OK (page enregistrée)")
        return True

    except Exception as e:
        log(f"   -> ERREUR (impossible de sauvegarder: {e})")
        return False

def main():
    log("=== Bot : ajout interwiki simple depuis wp ===")

    start = pywikibot.Timestamp.utcnow()

    seen = deque(maxlen=400)

    while True:
        try:
            log("Recup de modif")

            rcgen = VIKIDIA_SITE.recentchanges(
                start=start,
                namespaces=[0],
                changetype="edit",
                reverse=True,
                total=100
            )

            last_ts = None
            did_edit = False
            count = 0

            for rc in rcgen:
                title = rc.get("title")
                if not title:
                    continue

                count += 1
                last_ts = rc.get("timestamp")

                if title in seen:
                    log(f"Traitement... {title}")
                    log("   -> Ignoré (déjà vu récemment)")
                    continue
                seen.append(title)

                if process_page(title):
                    did_edit = True
                    log("   -> Pause 60s (délai demandé)")
                    time.sleep(60)

            if last_ts:
                start = last_ts

            if count == 0:
                log("   -> Aucune modification nouvelle")
                time.sleep(10)

        except Exception as e:
            log(f"[ERREUR BOUCLE] {e}")
            time.sleep(30)


if __name__ == "__main__":
    main()