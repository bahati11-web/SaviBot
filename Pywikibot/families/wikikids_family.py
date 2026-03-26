from pywikibot import family


class Family(family.Family):  # noqa: D101

    name = 'wikikids'
    langs = {
        'nl': 'wikikids.nl',
    }

    def scriptpath(self, code):
        return {
            'nl': '',
        }[code]

    def protocol(self, code):
        return {
            'nl': 'https',
        }[code]
