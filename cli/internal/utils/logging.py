import logging
import os

import click
import click_log

from cli.internal.utils.constants import LOG_PROTOCOL_TRACE


def install_logger(logger: logging.Logger, level):
    logger.setLevel(level)
    click_log.ClickHandler._use_stderr = False
    click_log.basic_config(logger)
    return logger


# noinspection PyUnusedLocal
def handle_set_level(ctx, param, value):
    default_level = os.environ.get('LOGLEVEL', 'INFO').upper()
    if default_level.isdigit():
        default_level = int(default_level)
    from cli.config import Config
    logger = install_logger(ctx.ensure_object(Config).logger, default_level)

    if not value or ctx.resilient_parsing:
        return

    if value.upper() == "TRACE":
        logger.setLevel(LOG_PROTOCOL_TRACE)
        return
    if value.isdigit():
        logger.setLevel(int(value))
        return

    x = getattr(logging, value.upper(), None)
    if x is None:
        raise click.BadParameter(
            'Must be CRITICAL, ERROR, WARNING, INFO or DEBUG, not {}'
        )
    logger.setLevel(x)


class LazyLog(object):
    def __init__(self, func):
        self.func = func

    def __str__(self):
        return self.func()
