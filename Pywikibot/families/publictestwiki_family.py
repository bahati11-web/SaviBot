from pywikibot import family


class Family(family.Family):  # noqa: D101

    name = 'publictestwiki'
    langs = {
        'en': 'publictestwiki.com',
    }

    def scriptpath(self, code):
        return {
            'en': '/w',
        }[code]

    def protocol(self, code):
        return {
            'en': 'https',
        }[code]
