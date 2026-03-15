import pywikibot
import re
import time

site = pywikibot.Site("fr", "vikidia")
site.login()

wp_site = pywikibot.Site("fr", "wikipedia")

MAX_MODIFIED = 100
modified_count = 0
BATCH_SIZE = 50 

while modified_count < MAX_MODIFIED:
    random_pages = site.randompages(total=BATCH_SIZE, namespaces=[0])

    for page in random_pages:
        if modified_count >= MAX_MODIFIED:
            break

        try:
            if page.isRedirectPage():
                continue

            text = page.text
            if "{{travaux" in text.lower() or "[[simple:" in text.lower() or "{{homonymie" in text.lower():
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

            page.save(summary=f"Ajout de [[simple:{simple_title}]] depuis [[wp:{wp_title}]]",
                      minor=True, bot=True)

            modified_count += 1
            print(f"Ajout sur : {page.title()} ({modified_count}/{MAX_MODIFIED})")

            time.sleep(0.5)

        except Exception as e:
            print("Erreur sur", page.title(), ":", e)
            
    time.sleep(1)
