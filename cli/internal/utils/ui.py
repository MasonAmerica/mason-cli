import contextlib


@contextlib.contextmanager
def section(config, name):
    header = '------------ {} ------------'.format(name)
    config.logger.info(header)
    yield
    config.logger.info('-' * len(header))
