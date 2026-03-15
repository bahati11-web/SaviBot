import pywikibot
import re

site_it = pywikibot.Site("it", "vikidia")
site_fr = pywikibot.Site("fr", "vikidia")

site_fr.login()

pattern = re.compile(r"\[\[fr:(.*?)\]\]", re.IGNORECASE)

for page in site_it.allpages(namespace=0):

    try:
        text = page.text
    except:
        continue

    matches = pattern.findall(text)

    for fr_title in matches:

        fr_title = fr_title.strip()

        page_fr = pywikibot.Page(site_fr, fr_title)

        try:
            if not page_fr.exists():
                continue

            text_fr = page_fr.text

            it_link = f"[[it:{page.title()}]]"

            if re.search(r"\[\[it:", text_fr, re.IGNORECASE):
                continue

            if "[[Catégorie:" in text_fr:
                new_text = re.sub(
                    r"(\[\[Catégorie:[^\]]+\]\])",
                    it_link + "\n\\1",
                    text_fr,
                    count=1
                )
            else:
                new_text = text_fr.rstrip() + "\n" + it_link

            page_fr.text = new_text

            page_fr.save(
                summary=f"Ajout de {it_link}",
                minor=True,
                bot=True
            )

            print("Ajout :", page_fr.title())

        except Exception as e:
            print("Erreur :", page_fr.title(), e)
