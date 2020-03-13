import webbrowser

from pick import pick


class Interactivity:
    @staticmethod
    def pick(options, title):
        return pick(options, title)

    @staticmethod
    def open(url):
        webbrowser.open_new_tab(url)
