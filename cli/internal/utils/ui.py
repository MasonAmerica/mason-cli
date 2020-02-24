import contextlib

from cli.config import Config


@contextlib.contextmanager
def section(config: Config, name: str):
    header = '------------ {} ------------'.format(name)
    config.logger.info(header)
    yield
    config.logger.info('-' * len(header))
