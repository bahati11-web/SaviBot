import pywikibot
import requests
import re
import logging
from difflib import SequenceMatcher

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

site = pywikibot.Site("fr", "vikidia")
repo = pywikibot.Site("wikidata", "wikidata").data_repository()

cache_qid = {}

def similarite(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def est_homonymie(page):
    text = page.text.lower()

    if "homonymie" in text:
        logging.info(f"{page.title()} ignoré : homonymie texte")
        return True

    try:
        for cat in page.categories():
            if "homonymie" in cat.title().lower():
                logging.info(f"{page.title()} ignoré : catégorie homonymie")
                return True
    except Exception as e:
        logging.warning(f"Erreur catégories {page.title()} : {e}")

    return False


def qid_depuis_wiki(titre, wiki):

    url = "https://www.wikidata.org/w/api.php"

    params = {
        "action": "wbgetentities",
        "sites": wiki,
        "titles": titre,
        "format": "json"
    }

    try:
        data = requests.get(url, params=params).json()

        for qid, v in data.get("entities", {}).items():
            if qid != "-1":
                logging.info(f"{titre} → QID trouvé via {wiki} : {qid}")
                return qid
    except Exception as e:
        logging.warning(f"Erreur API {wiki} : {e}")

    return None


def chercher_qid_sitelinks(titre):

    for wiki in ["frwiki", "enwiki", "dewiki"]:
        qid = qid_depuis_wiki(titre, wiki)
        if qid:
            return qid

    return None


def chercher_qid_score(titre, contenu):

    url = "https://www.wikidata.org/w/api.php"

    params = {
        "action": "wbsearchentities",
        "search": titre,
        "language": "fr",
        "uselang": "fr",
        "limit": 10,
        "format": "json"
    }

    try:
        data = requests.get(url, params=params).json()
    except Exception as e:
        logging.error(f"Erreur requête Wikidata : {e}")
        return None

    meilleur_qid = None
    meilleur_score = 0

    for r in data.get("search", []):

        label = r["label"]
        description = r.get("description", "")

        if "homonymie" in description.lower():
            continue

        score_titre = similarite(titre, label)
        score_desc = similarite(contenu[:400], description)

        score_total = (score_titre * 0.8) + (score_desc * 0.2)

        logging.info(
            f"Candidat {r['id']} | label={label} | score_titre={score_titre:.4f} | score_desc={score_desc:.4f} | score_total={score_total:.4f}"
        )

        if score_titre >= 0.999 and score_total > meilleur_score:
            meilleur_score = score_total
            meilleur_qid = r["id"]

    if meilleur_qid:
        logging.info(f"QID sélectionné par score : {meilleur_qid}")

    return meilleur_qid


def qid_deja_lie(qid):

    try:
        item = pywikibot.ItemPage(repo, qid)
        item.get()

        if item.sitelinks and "frvikidia" in item.sitelinks:
            logging.info(f"{qid} ignoré : déjà lié frvikidia")
            return True

        return False

    except Exception as e:
        logging.warning(f"Erreur sitelinks {qid} : {e}")
        return False

def inserer_modele(text, qid):

    modele = "{{Élément Wikidata|" + qid + "}}"

    if modele in text:
        return text

    pattern = r"(\{\{[Pp]ortail.*?\}\}|\[\[Catégorie:.*?\]\])"

    match = re.search(pattern, text)

    if match:
        pos = match.start()
        logging.info("Insertion avant portail/catégorie")
        return text[:pos] + modele + "\n" + text[pos:]

    logging.info("Insertion fin de page")
    return text + "\n\n" + modele


for page in site.randompages(total=100, namespaces=0):

    titre = page.title()

    logging.info(f"Analyse page : {titre}")

    if page.isRedirectPage():
        logging.info("Ignoré : redirection")
        continue

    if est_homonymie(page):
        continue

    text = page.text

    if "{{Élément Wikidata" in text:
        logging.info("Ignoré : modèle déjà présent")
        continue

    if titre in cache_qid:
        qid = cache_qid[titre]
        logging.info(f"QID depuis cache : {qid}")
    else:

        qid = chercher_qid_sitelinks(titre)

        if not qid:
            qid = chercher_qid_score(titre, text)

        cache_qid[titre] = qid

    if not qid:
        logging.info("Aucun QID trouvé")
        continue

    if qid_deja_lie(qid):
        continue

    nouveau = inserer_modele(text, qid)

    if nouveau != text:

        page.text = nouveau

        try:
            page.save(
                summary=f"Bot: Ajout de {{Élément Wikidata|{qid}}}",
                minor=True,
                bot=True
            )

            logging.info(f"Modification enregistrée : {titre}")

        except Exception as e:
            logging.error(f"Erreur sauvegarde {titre} : {e}")
