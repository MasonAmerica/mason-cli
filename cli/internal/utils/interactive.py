import click
from pick import pick


class Interactivity:
    @staticmethod
    def pick(options, title):
        return pick(options, title)

    @staticmethod
    def open(url):
        click.launch(url)
