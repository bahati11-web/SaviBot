import re
import time
import pywikibot
import mwparserfromhell

site = pywikibot.Site("fr", "vikidia")

def pre_clean(text):
    text = re.sub(r'^(==+)\s*([^=\n]+?)\s*(==+)$', r'\1 \2 \3', text, flags=re.MULTILINE)
    text = re.sub(r'«\s*(.*?)\s*»', r'{{"|\1}}', text)
    return text*

def fix_text_nodes(code):
    for node in code.nodes:
        if isinstance(node, mwparserfromhell.nodes.text.Text):
            txt = str(node)
            txt = re.sub(r'\s+,', ',', txt)
            txt = re.sub(r',([^\s])', r', \1', txt)
            txt = re.sub(r'[ \t]{2,}', ' ', txt)
            txt = re.sub(r' +\n', '\n', txt)
            node.value = txt

def fix_wikilinks(code):
    for link in code.filter_wikilinks():
        title = str(link.title).strip()

        if title.lower().startswith("file:"):
            title = "Fichier:" + title[5:]

        link.title = title

        if link.text:
            link.text = str(link.text).strip()

def has_travaux(code):
    for tpl in code.filter_templates():
        if str(tpl.name).strip().lower().startswith("travaux"):
            return True
    return False

def process(text):
    text = pre_clean(text)
    code = mwparserfromhell.parse(text)

    if has_travaux(code):
        return None

    fix_text_nodes(code)
    fix_wikilinks(code)

    return str(code)

def main():
    start = pywikibot.Timestamp.utcnow()

    while True:
        rc = site.recentchanges(
            namespaces=[0],
            start=start,
            reverse=True
        )

        for change in rc:
            try:
                title = change["title"]
                page = pywikibot.Page(site, title)

                if not page.exists():
                    continue

                text = page.get()
                new_text = process(text)

                if new_text is None:
                    continue

                if new_text != text:
                    page.put(
                        new_text,
                        summary="Bot: corrections typographiques",
                        minor=True,
                        bot=True
                    )

                start = change["timestamp"]

            except Exception:
                continue

        time.sleep(30)

if __name__ == "__main__":
    main()
