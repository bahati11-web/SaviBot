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
        return True

    try:
        for cat in page.categories():
            if "homonymie" in cat.title().lower():
                return True
    except:
        pass

    return False


def chercher_qid_sitelinks(titre):

    url = "https://www.wikidata.org/w/api.php"

    for wiki in ["frwiki","enwiki","dewiki"]:

        params = {
            "action":"wbgetentities",
            "sites":wiki,
            "titles":titre,
            "format":"json"
        }

        try:
            data = requests.get(url,params=params).json()

            for qid,v in data.get("entities",{}).items():
                if qid != "-1":
                    return qid

        except:
            pass

    return None


def chercher_qid_sparql(titre):

    query = f"""
    SELECT ?item WHERE {{
      ?item rdfs:label "{titre}"@fr .
      ?item wdt:P31 ?type .

      FILTER(?type NOT IN (
        wd:Q4167410,
        wd:Q13406463,
        wd:Q11266439
      ))
    }}
    LIMIT 5
    """

    url = "https://query.wikidata.org/sparql"

    try:

        r = requests.get(
            url,
            params={"query":query,"format":"json"},
            headers={"User-Agent":"BahatiBot"}
        ).json()

        for b in r["results"]["bindings"]:

            uri = b["item"]["value"]
            return uri.split("/")[-1]

    except:
        pass

    return None


def chercher_qid_alias(titre):

    query = f"""
    SELECT ?item WHERE {{
      ?item skos:altLabel "{titre}"@fr .
      ?item wdt:P31 ?type .

      FILTER(?type NOT IN (
        wd:Q4167410,
        wd:Q13406463,
        wd:Q11266439
      ))
    }}
    LIMIT 5
    """

    url = "https://query.wikidata.org/sparql"

    try:

        r = requests.get(
            url,
            params={"query":query,"format":"json"},
            headers={"User-Agent":"BahatiBot"}
        ).json()

        for b in r["results"]["bindings"]:

            uri = b["item"]["value"]
            return uri.split("/")[-1]

    except:
        pass

    return None


def chercher_qid_score(titre, contenu):

    url = "https://www.wikidata.org/w/api.php"

    params = {
        "action":"wbsearchentities",
        "search":titre,
        "language":"fr",
        "limit":10,
        "format":"json"
    }

    try:
        data = requests.get(url,params=params).json()
    except:
        return None

    meilleur_qid = None
    meilleur_score = 0

    for r in data.get("search",[]):

        label = r["label"]
        description = r.get("description","")

        if "homonymie" in description.lower():
            continue

        score_titre = similarite(titre,label)
        score_desc = similarite(contenu[:400],description)

        score_total = (score_titre*0.8)+(score_desc*0.2)

        if score_titre >= 0.92 and score_total > meilleur_score:
            meilleur_score = score_total
            meilleur_qid = r["id"]

    return meilleur_qid


def qid_deja_lie(qid):

    try:

        item = pywikibot.ItemPage(repo,qid)
        item.get()

        if item.sitelinks and "frvikidia" in item.sitelinks:
            return True

    except:
        pass

    return False


def inserer_modele(text,qid):

    modele = "{{Élément Wikidata|" + qid + "}}"

    if modele in text:
        return text

    pattern = r"(\{\{[Pp]ortail.*?\}\}|\[\[Catégorie:.*?\]\])"

    match = re.search(pattern,text)

    if match:
        pos = match.start()
        return text[:pos] + modele + "\n" + text[pos:]

    return text + "\n\n" + modele


for page in site.randompages(total=100,namespaces=0):

    titre = page.title()

    if page.isRedirectPage():
        continue

    if page.isDisambig():
        continue

    if re.match(r"^\d{3,4}$",titre):
        continue

    if est_homonymie(page):
        continue

    text = page.text

    if "{{Élément Wikidata" in text:
        continue

    if titre in cache_qid:
        qid = cache_qid[titre]

    else:

        qid = chercher_qid_sitelinks(titre)

        if not qid:
            qid = chercher_qid_sparql(titre)

        if not qid:
            qid = chercher_qid_alias(titre)

        if not qid:
            qid = chercher_qid_score(titre,text)

        cache_qid[titre] = qid

    if not qid:
        continue

    if qid_deja_lie(qid):
        continue

    nouveau = inserer_modele(text,qid)

    if nouveau != text:

        page.text = nouveau

        try:

            page.save(
                summary=f"Bot: Ajout de {{Élément Wikidata|{qid}}}",
                minor=True,
                bot=True
            )

        except Exception as e:

            logging.error(e)
