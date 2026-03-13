import pywikibot
import re
from datetime import datetime, timezone
import warnings

warnings.filterwarnings("ignore")

site = pywikibot.Site("fr", "vikidia")
site.login()
now = datetime.now(timezone.utc)
today_str = now.strftime("%Y-%m-%d") 

changes = site.recentchanges(
    namespaces=[0],
    changetype="edit"
)

pages_set = set()
for change in changes:
    rc_time = datetime.fromisoformat(change["timestamp"])
    if rc_time.strftime("%Y-%m-%d") == today_str:
        pages_set.add(change["title"])

print(f"Nombre de pages réellement modifiées aujourd'hui : {len(pages_set)}")

wp_site = pywikibot.Site("fr", "wikipedia")

for title in pages_set:
    page = pywikibot.Page(site, title)
    try:
        if page.isRedirectPage():
            continue

        text = page.text
        if "{{Travaux" in text or "[[simple:" in text:
            continue

        match = re.search(r"\[\[wp:(.*?)\]\]", text)
        if not match:
            continue

        wp_title = match.group(1).strip()
        wp_page = pywikibot.Page(wp_site, wp_title)
        if not wp_page.exists():
            continue

        simple_title = None
        for lang in wp_page.langlinks():
            if lang.site.code == "simple":
                simple_title = lang.title
                break
        if not simple_title:
            continue

        simple_link = f"[[simple:{simple_title}]]"
        wp_link = f"[[wp:{wp_title}]]"

        if simple_link in text:
            continue

        new_text = text.replace(wp_link, wp_link + "\n" + simple_link)
        page.text = new_text

        summary = f"Ajout de [[simple:{simple_title}]] depuis [[wp:{wp_title}]]"
        page.save(summary=summary, minor=True, bot=True)

        print("Ajout sur :", title)

    except Exception as e:
        print("Erreur sur", title, ":", e)
