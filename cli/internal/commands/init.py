import contextlib
import json
import os

import click
import sys
import yaml

from cli.internal.commands.command import Command
from cli.internal.models.apk import Apk
from cli.internal.utils.validation import validate_credentials


class InitCommand(Command):
    def __init__(self, config, working_dir=None):
        self.config = config
        self.working_dir = os.path.abspath(working_dir or os.getcwd())

        validate_credentials(config)

    @Command.log('init')
    def run(self):
        self._print_details()
        self._validate_dir()

        if not self.config.skip_verify:
            click.confirm('Are you ready to proceed?', default=True, abort=True)

        project_id = self._choose_project()
        apps = self._get_selected_apps()
        config = self._rewritten_config(project_id)

        self._write_files(config, apps)
        self.config.logger.info('Mason initialization complete!')

    def _print_details(self):
        self.config.logger.info(click.style(fg='magenta', text="""
        ##     ##    ###     ######   #######  ##    ##
        ###   ###   ## ##   ##    ## ##     ## ###   ##
        #### ####  ##   ##  ##       ##     ## ####  ##
        ## ### ## ##     ##  ######  ##     ## ## ## ##
        ##     ## #########       ## ##     ## ##  ####
        ##     ## ##     ## ##    ## ##     ## ##   ###
        ##     ## ##     ##  ######   #######  ##    ##"""))
        self.config.logger.info('')
        self.config.logger.info('You\'re about to initialize a Mason project in this directory:')
        self.config.logger.info('')
        self.config.logger.info('  {}'.format(self.working_dir))
        self.config.logger.info('')

    def _validate_dir(self):
        home_dir = os.path.expanduser('~')
        if not self.working_dir.startswith(home_dir):
            self.config.logger.warning('You are currently outside your home directory.')
        elif self.working_dir == home_dir:
            self.config.logger.warning(
                'You are initializing your home directory as a Mason project.')
        elif os.path.exists(os.path.join(self.working_dir, '.masonrc')):
            self.config.logger.warning(
                'You are initializing in an existing Mason project directory.')

    def _choose_project(self):
        projects = self.config.api.get_projects() or []

        options = ['Create new project']
        for project in projects:
            options.append(project.get('name'))

        option, index = self.config.interactivity.pick(
            options, 'Choose an existing Mason project or create a new one:')

        if index == 0:
            id = click.prompt('Enter your new project ID')

            base_url = self.config.endpoints_store['console_projects_url']
            url = base_url + '/_create?name={}'.format(id)
            self.config.interactivity.open(url)

            option = id

        return option

    def _get_selected_apps(self):
        presentable_paths = self._locate_apps()
        user_string = ''
        for num, path in enumerate(presentable_paths):
            user_string = user_string + path

            if num + 1 < len(presentable_paths):
                user_string = user_string + ', '
        self.config.logger.info('')
        if user_string:
            self.config.logger.info('App directories found: {}'.format(user_string))

        while True:
            result = click.prompt(
                'Where should Mason look for apps? '
                '(Enter multiple paths separated by a comma, or leave blank if none.)',
                default='', show_default=False
            )

            sanitized_result = result.strip()
            if not sanitized_result:
                self.config.logger.info('')
                return []

            rebuilt_paths = []
            user_paths = sanitized_result.split(',')
            for user_path in user_paths:
                path = self._expanded_path(user_path.strip())
                if os.path.exists(path):
                    rebuilt_paths.append(path)
                else:
                    self.config.logger.error('Path does not exist: {}'.format(path))

            if len(rebuilt_paths) == len(user_paths):
                self.config.logger.info('')
                return self._make_paths_presentable(rebuilt_paths)

    def _rewritten_config(self, project_id):
        existing_config = self.config.api.get_latest_artifact(project_id, 'config')

        if existing_config:
            new_config = existing_config.get('config') or {}
        else:
            new_config = {}

        if not new_config.get('os'):
            new_config['os'] = {}

        new_config['os']['name'] = project_id
        new_config['os']['version'] = 'latest'

        return new_config

    def _write_files(self, config, apps):
        self.config.logger.info('Writing configuration file to mason.yml...')
        with open(os.path.join(self.working_dir, 'mason.yml'), 'w') as f:
            f.write(yaml.safe_dump(config))

        self.config.logger.info('Writing project information to .masonrc...')
        mason_rc = {
            'configs': 'mason.yml',
            'apps': apps
        }
        with open(os.path.join(self.working_dir, '.masonrc'), 'w') as f:
            f.write(json.dumps(mason_rc, indent=2) + os.linesep)

        self.config.logger.info('')

    def _locate_apps(self):
        apps = []
        apks = self._locate_files(self.working_dir, '.apk')

        for apk in apks:
            with self._error_swallower():
                Apk.parse(self.config, apk)
                apps.append(apk)

        return self._make_paths_presentable(apps)

    def _make_paths_presentable(self, paths):
        presentable_paths = []

        for path in paths:
            if os.path.isfile(path):
                parent = os.path.abspath(os.path.join(path, os.pardir))
            else:
                parent = path

            clean_path = os.path.relpath(parent, self.working_dir)
            presentable_paths.append(clean_path)

        return presentable_paths

    def _locate_files(self, dir, extension):
        if os.path.isfile(dir):
            if dir.endswith(extension):
                return [dir]
            else:
                return []

        files = []

        sub_paths = list(map(lambda sub: os.path.join(dir, sub), os.listdir(dir)))
        for file in sub_paths:
            files.extend(self._locate_files(file, extension))

        return files

    def _expanded_path(self, path):
        if os.path.isabs(path):
            file = path
        else:
            file = os.path.abspath(os.path.join(self.working_dir, path))
        return file

    @contextlib.contextmanager
    def _error_swallower(self):
        level = self.config.logger.level
        self.config.logger.setLevel(sys.maxsize)
        # noinspection PyBroadException
        try:
            yield level
        except Exception:
            pass
        finally:
            self.config.logger.setLevel(level)
