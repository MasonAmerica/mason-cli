import copy
import os
import random
import string
import time

import click

from cli.internal.utils.remote import RequestHandler
from cli.internal.utils.remote import build_url
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

        url = build_url(self.config.endpoints_store, 'analytics_url')
        try:
            self.handler.post(url, headers=headers, json=payload)
        except Exception as e:
            self.config.logger.debug(e)

    def log_config(self, config):
        self._compute_environment()

        try:
            mapped_configs = self._mapped_config(config)
        except Exception as e:
            self.config.logger.debug(e)
            return

        headers = {
            'Content-Type': 'application/json'
        }
        payload = {
            'property': 'configs',
            'event': 'register',
            'environment': self.environment,
            'configs2': mapped_configs
        }

        url = build_url(self.config.endpoints_store, 'analytics_url')
        try:
            self.handler.post(url, headers=headers, json=payload)
        except Exception as e:
            self.config.logger.debug(e)

    def _compute_environment(self):
        if self.ci and self.environment:
            return

        self.ci = True if os.getenv("CI") else False

        sample_url = build_url(self.config.endpoints_store, 'deploy_url')
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
    def _mapped_config(config):
        mapped_config = copy.deepcopy(config)

        mapped_config['customerApps'] = []
        for app in mapped_config.get('apps') or []:
            mapped_config['customerApps'].append({
                'name': app.get('package_name'),
                'version': str(app.get('version_code'))
            })
        mapped_config.pop('apps', None)

        anim = (mapped_config.get('media') or {}).get('bootanimation')
        if anim:
            mapped_config['bootanimation'] = [{
                'name': anim.get('name'),
                'version': str(anim.get('version'))
            }]
        splash = (mapped_config.get('media') or {}).get('splash')
        if splash:
            mapped_config['splash'] = [{
                'name': splash.get('name'),
                'version': str(splash.get('version'))
            }]
        mapped_config.pop('media', None)

        os = mapped_config.get('os') or {}
        os_configs = os.get('configurations') or {}
        mapped_config['name'] = os.get('name')
        mapped_config['version'] = str(os.get('version'))
        MasonAnalytics._map_os_config_items(mapped_config, os_configs, 'mason-management')
        MasonAnalytics._map_os_config_items(mapped_config, os_configs, 'mason-core')
        MasonAnalytics._map_os_config_items(mapped_config, os_configs, 'mason-fota')
        MasonAnalytics._map_os_config_items(mapped_config, os_configs, 'mason-app-updater')
        MasonAnalytics._map_os_config_items(mapped_config, os_configs, 'android')
        MasonAnalytics._map_os_config_items(mapped_config, os_configs, 'settings')
        MasonAnalytics._map_os_config_items(mapped_config, os_configs, 'systemui')
        mapped_config.pop('os', None)

        return mapped_config

    @staticmethod
    def _map_os_config_items(mapped_config, os_configs, name):
        items = (os_configs.get(name) or {}).items()

        name = name.replace('-', '_')
        mapped_config[name] = []
        for (key, val) in items:
            mapped_config[name].append({
                'key': key,
                'value': str(val)
            })

    @staticmethod
    def _random_string():
        letters = string.ascii_lowercase
        return ''.join(random.choice(letters) for i in range(32))
