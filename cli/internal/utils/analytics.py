import os
import random
import string

import click
import time

from cli.internal.utils.remote import RequestHandler
from cli.internal.utils.store import Store
from cli.version import __version__


class MasonAnalytics:
    def __init__(self, config):
        self.config = config
        self.handler = RequestHandler(config)
        self.instance = self._random_string()
        self.session = Store('session', {})

        self.ci = None
        self.environment = None

    def log_event(self, command=None, duration_seconds=None, exception=None):
        self._compute_environment()

        headers = {
            'Content-Type': 'application/json'
        }
        payload = {
            'property': 'mason-cli',
            'event': 'invoke',
            'environment': self.environment,
            'cli': {
                'version': __version__,
                'command': command,
                'instance': self.instance,
                'session': self._sanitized_session(),
                'log_level': self.config.logger.level,
                'exception': exception.__class__.__name__ if exception else None,
                'flags': list({k: v for k, v in
                               click.get_current_context().params.items() if v}.keys()),
                'ci': self.ci,
                'duration': duration_seconds
            }
        }

        url = "https://platform.development.masonamerica.net/api/v1/analytics/log"
        try:
            self.handler.post(url, headers=headers, json=payload)
        except Exception as e:
            self.config.logger.debug(e)

    def _compute_environment(self):
        if self.ci and self.environment:
            return

        self.ci = True if os.getenv("CI") else False

        sample_url = self.config.endpoints_store['deploy_url']
        if 'development' in sample_url:
            self.environment = 'development'
        elif 'staging' in sample_url:
            self.environment = 'staging'
        else:
            self.environment = 'production'

    def _sanitized_session(self):
        current_time = int(time.time())

        last_used = self.session['last_used']
        if last_used and current_time - last_used < 900:  # 15 minutes
            self.session['last_used'] = current_time
            self.session.save()

            return self.session['id']
        else:
            id = self._random_string()

            self.session['last_used'] = current_time
            self.session['id'] = id
            self.session.save()

            return id

    @staticmethod
    def _random_string():
        letters = string.ascii_lowercase
        return ''.join(random.choice(letters) for i in range(32))
