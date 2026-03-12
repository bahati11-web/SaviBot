import pywikibot
import requests
import re
from difflib import SequenceMatcher

site = pywikibot.Site("fr", "vikidia")

def similarite(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def est_homonymie(page):
    text = page.text.lower()
    if "homonymie" in text:
        return True
    try:
        for cat in page.categories():
            if "homonymie" in cat.title().lower():
                return True
    except:
        pass
    return False

def chercher_qid(titre):
    url = "https://www.wikidata.org/w/api.php"
    params = {
        "action": "wbsearchentities",
        "search": titre,
        "language": "fr",
        "limit": 10,
        "format": "json"
    }
    data = requests.get(url, params=params).json()
    meilleur_qid = None
    meilleur_score = 0
    for r in data.get("search", []):
        label = r["label"]
        description = r.get("description", "")
        if "homonymie" in description.lower():
            continue
        score = similarite(titre, label)
        if score > meilleur_score:
            meilleur_score = score
            meilleur_qid = r["id"]
    if meilleur_score >= 0.999:
        return meilleur_qid
    return None

def inserer_modele(text, qid):
    modele = "{{Élément Wikidata|" + qid + "}}"
    if modele in text:
        return text
    pattern = r"(\{\{[Pp]ortail.*?\}\}|\[\[Catégorie:.*?\]\])"
    match = re.search(pattern, text)
    if match:
        pos = match.start()
        return text[:pos] + modele + "\n" + text[pos:]
    return text + "\n\n" + modele

for page in site.randompages(total=100, namespaces=0):
    if page.isRedirectPage():
        continue
    if est_homonymie(page):
        continue
    titre = page.title()
    qid = chercher_qid(titre)
    if not qid:
        continue
    text = page.text
    nouveau = inserer_modele(text, qid)
    if nouveau != text:
        page.text = nouveau
        page.save(
            summary=f"Bot: Ajout de {{Élément Wikidata|{qid}}}",
            minor=True,
            bot=True
        )
